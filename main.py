from flask import Flask, jsonify
import requests

app = Flask(__name__)

# Doğrudan açık futbol veri CDN servisleri ve Fotmob web arayüzü
LIG_URLS = [
    {"ad": "Süper Lig", "url": "https://raw.githubusercontent.com/openfootball/turkish-football/master/2025-26/1-superlig.json"},
    {"ad": "Premier League", "url": "https://raw.githubusercontent.com/openfootball/england/master/2025-26/1-premierleague.json"}
]

@app.route('/')
def home():
    return "Hologram Cube Open-Data Proxy Active"

@app.route('/maclar')
def maclar_cek():
    tum_maclar = []
    loglar = []
    
    # Alternatif 1: Güvenilir Açık Spor API Servisi (TheSportsDB Open)
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # Ek olarak FotMob web-api şeması (güncel endpoint)
    fotmob_url = "https://www.fotmob.com/api/matches?date=20260918"
    
    try:
        res = requests.get(fotmob_url, headers=headers, timeout=6)
        loglar.append(f"FotMob Match API: {res.status_code}")
        
        if res.status_code == 200:
            data = res.json()
            leagues = data.get('leagues', [])
            
            for league in leagues:
                lig_adi = league.get('name', 'Lig')
                matches = league.get('matches', [])
                
                for m in matches:
                    ev = m.get('home', {}).get('name', 'EV')
                    dep = m.get('away', {}).get('name', 'DEP')
                    status = m.get('status', {})
                    
                    score_str = status.get('scoreStr', '0 - 0')
                    ev_s, dep_s = 0, 0
                    if ' - ' in str(score_str):
                        try:
                            parts = score_str.split(' - ')
                            ev_s = int(parts[0])
                            dep_s = int(parts[1])
                        except: pass

                    started = status.get('started', False)
                    finished = status.get('finished', False)
                    
                    if finished:
                        dk = "MS"
                    elif started:
                        dk = "CANLI"
                    else:
                        startTime = status.get('startTimeStr', '')
                        dk = startTime.split(' ')[1][:5] if ' ' in startTime else "YAKINDA"

                    tum_maclar.append({
                        "id": str(m.get('id')),
                        "lig": lig_adi,
                        "ev": str(ev).upper()[:9],
                        "dep": str(dep).upper()[:9],
                        "evS": ev_s,
                        "depS": dep_s,
                        "dk": dk
                    })
    except Exception as e:
        loglar.append(f"Hata: {str(e)}")

    if len(tum_maclar) == 0:
        return jsonify({"maclar": [], "debug_loglar": loglar})

    return jsonify({"maclar": tum_maclar})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
