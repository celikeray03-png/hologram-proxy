from flask import Flask, jsonify
import requests

app = Flask(__name__)

# ESPN Lig Kodları
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
    return "Hologram Cube Proxy Server Active"

@app.route('/maclar')
def maclar_cek():
    tum_maclar = []
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    })
    
    for lig in LIGLER:
        try:
            # Doğrudan aktüel fikstür endpoint'i (Tarih zorlaması yok)
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lig['slug']}/scoreboard"
            res = session.get(url, timeout=5)
            
            if res.status_code != 200:
                continue
            
            data = res.json()
            events = data.get('events', [])
            
            for event in events:
                comp = event['competitions'][0]
                status = event['status']
                
                competitors = comp.get('competitors', [])
                if len(competitors) < 2:
                    continue
                
                ev = competitors[0]['team'].get('shortDisplayName') or competitors[0]['team'].get('name', 'EV')
                dep = competitors[1]['team'].get('shortDisplayName') or competitors[1]['team'].get('name', 'DEP')
                
                ev_skor = int(competitors[0].get('score', 0))
                dep_skor = int(competitors[1].get('score', 0))
                
                state = status['type']['state']
                d = status['type']['shortDetail']
                
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
                    "ev": str(ev).upper()[:9],
                    "dep": str(dep).upper()[:9],
                    "evS": ev_skor,
                    "depS": dep_skor,
                    "dk": d
                })
        except Exception:
            continue
            
    return jsonify({"maclar": tum_maclar})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
