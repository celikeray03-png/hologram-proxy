from flask import Flask, jsonify
import requests

app = Flask(__name__)

# FotMob Lig ID'leri
LIG_MAP = {
    47: "Premier League",
    87: "La Liga",
    54: "Serie A",
    53: "Bundesliga",
    57: "Ligue 1",
    71: "Süper Lig",
    42: "Şampiyonlar Ligi",
    73: "UEFA Avrupa Ligi",
    10216: "Konferans Ligi"
}

@app.route('/')
def home():
    return "Hologram Cube FotMob Proxy Active"

@app.route('/maclar')
def maclar_cek():
    tum_maclar = []
    
    # FotMob Mobil Endpoint (Engelsiz)
    url = "https://www.fotmob.com/api/matchesData"
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=6)
        
        if res.status_code == 200:
            data = res.json()
            leagues = data.get('leagues', [])
            
            for league in leagues:
                l_id = league.get('id')
                
                # Sadece takip ettiğimiz ligleri alıyoruz
                if l_id in LIG_MAP:
                    lig_adi = LIG_MAP[l_id]
                    matches = league.get('matches', [])
                    
                    for m in matches:
                        ev = m.get('home', {}).get('name', 'EV')
                        dep = m.get('away', {}).get('name', 'DEP')
                        
                        status = m.get('status', {})
                        score_str = status.get('scoreStr', '0 - 0')
                        
                        ev_s = 0
                        dep_s = 0
                        if ' - ' in score_str:
                            try:
                                parts = score_str.split(' - ')
                                ev_s = int(parts[0])
                                dep_s = int(parts[1])
                            except:
                                pass

                        started = status.get('started', False)
                        finished = status.get('finished', False)
                        cancelled = status.get('cancelled', False)
                        
                        dk = status.get('reason', {}).get('short', '')
                        
                        if finished:
                            dk = "MS"
                        elif cancelled:
                            dk = "İPTAL"
                        elif started and not finished:
                            live_time = status.get('liveTime', {}).get('short', '')
                            dk = f"{live_time}' CANLI" if live_time else "CANLI"
                        else:
                            # Maç başlamadıysa başlama saatini alıyoruz
                            startTime = status.get('startTimeStr', '')
                            if startTime and ' ' in startTime:
                                dk = startTime.split(' ')[1][:5]
                            else:
                                dk = "YAKINDA"

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
        return jsonify({"maclar": [], "hata": str(e)})

    return jsonify({"maclar": tum_maclar})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
