from flask import Flask, jsonify
import requests

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
    return "Hologram Cube Proxy Server Active"

@app.route('/maclar')
def maclar_cek():
    tum_maclar = []
    loglar = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for lig in LIGLER:
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lig['slug']}/scoreboard"
            res = requests.get(url, headers=headers, timeout=5)
            
            loglar.append(f"{lig['slug']}: HTTP {res.status_code}")
            
            if res.status_code == 200:
                data = res.json()
                events = data.get('events', [])
                loglar.append(f"{lig['slug']}: {len(events)} mac bulundu")
                
                for event in events:
                    comp = event['competitions'][0]
                    teams = comp['competitors']
                    
                    ev_ad = teams[0]['team'].get('shortDisplayName') or teams[0]['team'].get('name', 'EV')
                    dep_ad = teams[1]['team'].get('shortDisplayName') or teams[1]['team'].get('name', 'DEP')
                    
                    ev_skor = int(teams[0].get('score', 0))
                    dep_skor = int(teams[1].get('score', 0))
                    
                    status = event['status']['type']
                    d = status.get('shortDetail', '')
                    
                    tum_maclar.append({
                        "id": str(event['id']),
                        "lig": lig['ad'],
                        "ev": str(ev_ad).upper()[:9],
                        "dep": str(dep_ad).upper()[:9],
                        "evS": ev_skor,
                        "depS": dep_skor,
                        "dk": str(d)
                    })
        except Exception as e:
            loglar.append(f"{lig['slug']} HATA: {str(e)}")
            continue
            
    # Eğer maç bulunamazsa logları ekrana bas ki hatayı görelim
    if len(tum_maclar) == 0:
        return jsonify({"maclar": [], "debug_loglar": loglar})
        
    return jsonify({"maclar": tum_maclar})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
