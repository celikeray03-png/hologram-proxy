from flask import Flask, jsonify
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

LIGLER = [
    {"slug": "tur.1", "ad": "Süper Lig"},
    {"slug": "uefa.europa", "ad": "UEFA Avrupa Ligi"},
    {"slug": "uefa.champions", "ad": "Şampiyonlar Ligi"},
    {"slug": "uefa.europa.conf", "ad": "Konferans Ligi"},
    {"slug": "eng.1", "ad": "Premier League"},
    {"slug": "esp.1", "ad": "La Liga"},
    {"slug": "ita.1", "ad": "Serie A"},
    {"slug": "ger.1", "ad": "Bundesliga"},
    {"slug": "fra.1", "ad": "Ligue 1"}
]

@app.route('/')
def home():
    return "Hologram Cube Dynamic API Aktif!"

@app.route('/maclar')
def maclar_cek():
    # Bugün ve Yarının Tarihlerini Alıyoruz (YYYYMMDD)
    bugun = datetime.now()
    yarin = bugun + timedelta(days=1)
    tarih_param = f"{bugun.strftime('%Y%m%d')}-{yarin.strftime('%Y%m%d')}"
    
    tum_maclar = []
    
    for lig in LIGLER:
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lig['slug']}/scoreboard?dates={tarih_param}"
            res = requests.get(url, timeout=4)
            if res.status_code != 200:
                continue
            
            data = res.json()
            events = data.get('events', [])
            
            for event in events:
                comp = event['competitions'][0]
                status = event['status']
                
                ev = comp['competitors'][0]['team'].get('shortDisplayName') or comp['competitors'][0]['team'].get('name', 'EV')
                dep = comp['competitors'][1]['team'].get('shortDisplayName') or comp['competitors'][1]['team'].get('name', 'DEP')
                
                ev_skor = int(comp['competitors'][0].get('score', 0))
                dep_skor = int(comp['competitors'][1].get('score', 0))
                
                state = status['type']['state']
                d = status['type']['shortDetail']
                
                # Tarih/Saat Formatı
                date_str = event.get('date', '')
                gun_etiketi = ""
                if 'T' in date_str:
                    mac_tarihi = date_str.split('T')[0].replace('-', '')
                    saat = date_str.split('T')[1][:5]
                    # Türkiye Saati Ötelemesi (Yaklaşık +3)
                    saat_int = (int(saat.split(':')[0]) + 3) % 24
                    saat_fmt = f"{saat_int:02d}:{saat.split(':')[1]}"
                    
                    if mac_tarihi == bugun.strftime('%Y%m%d'):
                        gun_etiketi = f"Bugün {saat_fmt}"
                    else:
                        gun_etiketi = f"Yarın {saat_fmt}"
                
                if state == "pre":
                    d = gun_etiketi
                elif state == "in":
                    d = f"{d} CANLI"
                elif state == "post" or d in ["FT", "FINAL"]:
                    d = "MS"
                
                tum_maclar.append({
                    "id": str(event['id']),
                    "lig": lig['ad'],
                    "ev": ev.upper()[:9],
                    "dep": dep.upper()[:9],
                    "evS": ev_skor,
                    "depS": dep_skor,
                    "dk": d
                })
        except Exception:
            continue
            
    return jsonify({"maclar": tum_maclar})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
