import os
import time
import subprocess
import requests
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

# Türkiye Zaman Dilimi (UTC+3)
TR_TZ = timezone(timedelta(hours=3))

LIGLER = [
    {"slug": "tur.1", "ad": "Süper Lig"},
    {"slug": "eng.1", "ad": "Premier League"},
    {"slug": "esp.1", "ad": "La Liga"},
    {"slug": "ita.1", "ad": "Serie A"},
    {"slug": "ger.1", "ad": "Bundesliga"},
    {"slug": "fra.1", "ad": "Ligue 1"},
    {"slug": "uefa.champions", "ad": "Şampiyonlar Ligi"},
    {"slug": "uefa.europa", "ad": "UEFA Avrupa Ligi"},
    {"slug": "uefa.europa.conf", "ad": "Konferans Ligi"}
]

# Önbellek (Cache) Mekanizması (30 sn TTL)
CACHE_TTL = 30
_cache = {
    "timestamp": 0,
    "data": []
}

def fetch_single_league_date(lig, t, headers):
    matches = []
    url = f"https://site.web.api.espn.com/apis/site/v2/sports/soccer/{lig['slug']}/scoreboard?dates={t['str']}"
    try:
        res = requests.get(url, headers=headers, timeout=4)
        if res.status_code == 200:
            data = res.json()
            events = data.get('events', [])

            for event in events:
                comps = event.get('competitions', [])
                if not comps:
                    continue
                comp = comps[0]
                teams = comp.get('competitors', [])
                if len(teams) < 2:
                    continue

                ev_ad = teams[0]['team'].get('shortDisplayName') or teams[0]['team'].get('name', 'EV')
                dep_ad = teams[1]['team'].get('shortDisplayName') or teams[1]['team'].get('name', 'DEP')

                try:
                    ev_skor = int(teams[0].get('score', 0))
                except (ValueError, TypeError):
                    ev_skor = 0

                try:
                    dep_skor = int(teams[1].get('score', 0))
                except (ValueError, TypeError):
                    dep_skor = 0

                status = event.get('status', {}).get('type', {})
                state = status.get('state', '')
                d = status.get('shortDetail', '')

                date_str = event.get('date', '')

                if state == "pre" and 'T' in date_str:
                    try:
                        saat_ham = date_str.split('T')[1][:5]
                        saat_int = (int(saat_ham.split(':')[0]) + 3) % 24
                        d = f"{saat_int:02d}:{saat_ham.split(':')[1]}"
                    except Exception:
                        d = "YAKINDA"
                elif state == "in":
                    d = f"{d} CANLI"
                elif state == "post" or d in ["FT", "FINAL"]:
                    d = "MS"

                matches.append({
                    "id": str(event.get('id', '')),
                    "lig": lig['ad'],
                    "tarih": t["etiket"],
                    "ev": str(ev_ad).upper()[:9],
                    "dep": str(dep_ad).upper()[:9],
                    "evS": ev_skor,
                    "depS": dep_skor,
                    "dk": str(d),
                    "_state": state
                })
    except Exception:
        pass
    return matches

@app.route('/')
def home():
    return "Hologram Cube API Active"

@app.route('/maclar')
def maclar_cek():
    global _cache
    now = time.time()

    # Önbellek geçerliyse doğrudan anlık yanıt dön (10-20ms)
    if (now - _cache["timestamp"] < CACHE_TTL) and _cache["data"]:
        return jsonify({"maclar": _cache["data"]})

    # Türkiye Saatine Göre Dün, Bugün, Yarın (UTC + 3)
    tr_simdi = datetime.now(TR_TZ)
    tarihler = [
        {"etiket": "Dün", "str": (tr_simdi - timedelta(days=1)).strftime('%Y%m%d')},
        {"etiket": "Bugün", "str": tr_simdi.strftime('%Y%m%d')},
        {"etiket": "Yarın", "str": (tr_simdi + timedelta(days=1)).strftime('%Y%m%d')}
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'Accept': 'application/json'
    }

    tum_maclar = []
    tasks = []

    # 3 gün x 9 lig = 27 isteği eşzamanlı (paralel) çalıştırıyoruz (ThreadPoolExecutor)
    with ThreadPoolExecutor(max_workers=10) as executor:
        for t in tarihler:
            for lig in LIGLER:
                tasks.append(executor.submit(fetch_single_league_date, lig, t, headers))

        for future in as_completed(tasks):
            try:
                res = future.result()
                if res:
                    tum_maclar.extend(res)
            except Exception:
                pass

    if tum_maclar:
        # Önceliklendirme: Önce Canlı Maçlar, sonra Bugün, sonra Yarın, sonra Dün
        def oncelik_puani(m):
            puan = 0
            if m.get("_state") == "in":
                puan += 100
            if m.get("tarih") == "Bugün":
                puan += 50
            elif m.get("tarih") == "Yarın":
                puan += 20
            elif m.get("tarih") == "Dün":
                puan += 10
            return puan

        tum_maclar.sort(key=oncelik_puani, reverse=True)

        # Dahili yardımcı alanı temizle
        for m in tum_maclar:
            m.pop("_state", None)

        _cache["data"] = tum_maclar
        _cache["timestamp"] = now
    elif _cache["data"]:
        # Eğer geçici bir ağ hatası olduysa son başarılı veriyi sun
        return jsonify({"maclar": _cache["data"]})

    return jsonify({"maclar": tum_maclar})

# --- EKLENEN VİDEO DÖNÜŞTÜRÜCÜ & ELEMAN SERVİSİ ---
@app.route('/convert-upload', methods=['POST'])
def convert_and_upload():
    device_ip = request.form.get('device_ip')
    uploaded_file = request.files.get('file')

    if not device_ip or not uploaded_file:
        return "<h2>Hata: Eksik Parametre!</h2><a href='javascript:history.back()'>Geri Dön</a>", 400

    filename = uploaded_file.filename
    input_path = f"temp_{filename}"
    output_filename = os.path.splitext(filename)[0] + ".mjpeg"
    output_path = f"temp_{output_filename}"

    try:
        # 1. Yüklenen dosyayı geçici kaydet
        uploaded_file.save(input_path)

        # 2. FFmpeg ile 320x240, 25 FPS MJPEG formatına dönüştür
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", "scale=320:240:force_original_aspect_ratio=decrease,pad=320:240:(ow-iw)/2:(oh-ih)/2",
            "-q:v", "5",
            "-r", "25",
            "-pix_fmt", "yuvj420p",
            output_path
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        # 3. Dönüştürülen .mjpeg dosyasını ESP32'ye aktar
        esp32_url = f"http://{device_ip}/upload"
        with open(output_path, "rb") as f:
            files = {'upload': (output_filename, f, 'application/octet-stream')}
            response = requests.post(esp32_url, files=files, timeout=40)

        # Temizlik
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

        return f"<h2>Dönüştürme ve Yükleme Başarılı!</h2><p>{output_filename} SD karta yüklendi.</p><a href='http://{device_ip}/media'>Geri Dön</a>"

    except Exception as e:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        return f"<h2>Hata Oluştu!</h2><p>{str(e)}</p><a href='http://{device_ip}/media'>Geri Dön</a>", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
