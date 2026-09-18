from flask import Flask, jsonify
import requests

app = Flask(__name__)

# Otomatik Çekilecek Ligler
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

# ELLE EKLENECEK ÖZEL/AVRUPA MAÇLARI (İstediğin zaman buraya ekle/çıkar yapabilirsin)
MANUEL_MACLAR = [
    {
        "id": "m_custom_1",
        "lig": "UEFA Avrupa Ligi",
        "ev": "GALATASARAY",
        "dep": "PAOK",
        "evS": 0,
        "depS": 0,
        "dk": "Çar 22:00"
    },
    {
        "id": "m_custom_2",
        "lig": "UEFA Avrupa Ligi",
        "ev": "Fenerbahçe",
        "dep": "U.SG",
        "evS": 0,
        "depS": 0,
        "dk": "Per 19:45"
    },
    {
        "id": "m_custom_3",
        "lig": "Konferans Ligi",
        "ev": "BAŞAKŞEHİR",
        "dep": "RAPID WIEN",
        "evS": 0,
        "depS": 0,
        "dk": "Çar 17:30"
    }
]

@app.route('/')
def home():
    return "Hologram Cube Live API Ready"

@app.route('/maclar')
def maclar_cek():
    tum_maclar = []
    
    # 1. Önce Elle Eklediğimiz Özel Maçları Listeye Koyuyoruz
    for mm in MANUEL_MACLAR:
        tum_maclar.append({
            "id": mm["id"],
            "lig": mm["lig"],
            "ev": mm["ev"].upper()[:9],
            "dep": mm["dep"].upper()[:9],
            "evS": mm["evS"],
            "depS": mm["depS"],
            "dk": mm["dk"]
        })

    # 2. Otomatik API Maçlarını Çekip Ekliyoruz
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'Accept': 'application/json'
    }

    for lig in LIGLER:
        try:
            url = f"https://site.web.api.espn.com/apis/site/v2/sports/soccer/{lig['slug']}/scoreboard"
            res = requests.get(url, headers=headers, timeout=5)

            if res.status_code == 200:
                data = res.json()
                events = data.get('events', [])

                for event in events:
                    comp = event['competitions'][0]
                    teams = comp['competitors']

                    ev_ad = teams[0]['team'].get('shortDisplayName') or teams[0]['team'].get('name', 'EV')
                    dep_ad = teams[1]['team'].get('shortDisplayName') or teams[1]['team'].get('name', 'DEP')

                    ev_skor = int(teams[0].get('score', 0))
                    dep_skor = int(teams[1].get('score', 0))

                    status = event['status']['type']
                    state = status.get('state')
                    d = status.get('shortDetail', '')

                    date_str = event.get('date', '')
                    if state == "pre" and 'T' in date_str:
                        saat_ham = date_str.split('T')[1][:5]
                        saat_int = (int(saat_ham.split(':')[0]) + 3) % 24
                        d = f"{saat_int:02d}:{saat_ham.split(':')[1]}"
                    elif state == "in":
                        d = f"{d} CANLI"
                    elif state == "post" or d in ["FT", "FINAL"]:
                        d = "MS"

                    tum_maclar.append({
                        "id": str(event['id']),
                        "lig": lig['ad'],
                        "ev": str(ev_ad).upper()[:9],
                        "dep": str(dep_ad).upper()[:9],
                        "evS": ev_skor,
                        "depS": dep_skor,
                        "dk": str(d)
                    })
        except Exception:
            continue

    return jsonify({"maclar": tum_maclar})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
