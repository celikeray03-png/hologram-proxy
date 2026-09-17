from flask import Flask, jsonify
import requests

app = Flask(__name__)

LIGLER = [
    "tur.1",             # Süper Lig
    "uefa.europa",       # Avrupa Ligi
    "uefa.champions",    # Şampiyonlar Ligi
    "uefa.europa.conf",  # Konferans Ligi
    "eng.1",             # Premier League
    "esp.1",             # La Liga
    "ita.1",             # Serie A
    "ger.1",             # Bundesliga
    "fra.1"              # Ligue 1
]

@app.route('/')
def home():
    return "Hologram Cube Proxy Aktif!"

@app.route('/maclar')
def maclar_cek():
    tum_maclar = []
    
    for lig in LIGLER:
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lig}/scoreboard"
            res = requests.get(url, timeout=5)
            if res.status_code != 200:
                continue
            
            data = res.json()
            events = data.get('events', [])
            
            for event in events:
                comp = event['competitions'][0]
                status = event['status']
                
                # Takım isimleri (Short Name yoksa Full Name)
                ev = comp['competitors'][0]['team'].get('shortDisplayName') or comp['competitors'][0]['team'].get('name', 'EV')
                dep = comp['competitors'][1]['team'].get('shortDisplayName') or comp['competitors'][1]['team'].get('name', 'DEP')
                
                ev_skor = int(comp['competitors'][0].get('score', 0))
                dep_skor = int(comp['competitors'][1].get('score', 0))
                
                state = status['type']['state']
                d = status['type']['shortDetail']
                
                # Durum Ayarı
                if state == "pre":
                    # UTC saatini basitçe alıyoruz
                    date_str = event.get('date', '')
                    if 'T' in date_str:
                        d = date_str.split('T')[1][:5]
                elif state == "in":
                    d = f"{d} CANLI"
                elif state == "post" or d in ["FT", "FINAL"]:
                    d = "MS"
                
                tum_maclar.append({
                    "id": str(event['id']),
                    "ev": ev.upper()[:9],
                    "dep": dep.upper()[:9],
                    "evS": ev_skor,
                    "depS": dep_skor,
                    "dk": d
                })
        except Exception as e:
            continue
            
    return jsonify({"maclar": tum_maclar})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)