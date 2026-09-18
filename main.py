from flask import Flask, jsonify
import requests

app = Flask(__name__)

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
    loglar = []
    
    url = "https://www.fotmob.com/api/matchesData"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=8)
        loglar.append(f"FotMob HTTP Kodu: {res.status_code}")
        
        if res.status_code == 200:
            data = res.json()
            leagues = data.get('leagues', [])
            loglar.append(f"Toplam Lig Sayisi: {len(leagues)}")
            
            bulunan_mac_sayisi = 0
            for league in leagues:
                l_id = league.get('id')
                if l_id in LIG_MAP:
                    lig_adi = LIG_MAP[l_id]
                    matches = league.get('matches', [])
                    bulunan_mac_sayisi += len(matches)
                    
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
            
            loglar.append(f"Hedef Liglerde Bulunan Mac: {bulunan_mac_sayisi}")
            
    except Exception as e:
        loglar.append(f"HATA: {str(e)}")

    if len(tum_maclar) == 0:
        return jsonify({"maclar": [], "debug_loglar": loglar})

    return jsonify({"maclar": tum_maclar})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
