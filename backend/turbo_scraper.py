import time
import random
import logging
import json
from DrissionPage import ChromiumPage, ChromiumOptions
from sqlalchemy import create_engine, text

# ==========================================
# CONFIGURAZIONE DATABASE
# ==========================================
DB_URI = "postgresql://postgres:password@localhost:5432/xpalermostat" 
engine = create_engine(DB_URI)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def safe_float(val):
    try: return float(val)
    except: return 0.0

def safe_int(val):
    try: return int(val)
    except: return 0

def professional_hammer_sync():
    logging.info("🚀 SNIPER v45: Protocollo RAM F12 - Professional Edition (Anti-Conflict)")
    
    co = ChromiumOptions()
    co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    page = ChromiumPage(co)
    
    while True:
        with engine.connect() as conn:
            # Audit in tempo reale: peschiamo solo match del 2025 con buchi (NULL o 0 nelle coordinate)
            query = text("""
                SELECT DISTINCT m.id, m.match_datetime 
                FROM matchcalendar m
                JOIN shots s ON s.match_id = m.id
                WHERE m.match_datetime > '2025-07-01'
                AND (s.shot_type IS NULL OR s."X" IS NULL OR s."X" = 0)
                ORDER BY m.match_datetime DESC
                LIMIT 1
            """)
            match = conn.execute(query).fetchone()

        if not match:
            logging.info("🏁 MISSIONE COMPIUTA: Database 2025 blindato e pulito.")
            break

        match_id = match[0]
        url = f"https://understat.com/match/{match_id}"
        
        try:
            logging.info(f"🕵️  Analisi Match {match_id}...")
            page.get(url)
            
            data_found = False
            raw_json = None
            
            # Polling rapido: max 10 secondi
            for _ in range(20): 
                check = page.run_js("return (typeof window.shotsData !== 'undefined' && typeof window.rostersData !== 'undefined');")
                if check:
                    raw_json = page.run_js("return JSON.stringify({shots: window.shotsData, rosters: window.rostersData});")
                    data_found = True
                    break
                page.scroll.down(100)
                time.sleep(0.5)

            if not data_found or not raw_json:
                logging.warning(f"⛔ Match {match_id} non ha popolato la RAM. Salto.")
                continue

            data = json.loads(raw_json)

            with engine.begin() as conn:
                # 1. PULIZIA DEI VECCHI RECORD (Terra Bruciata)
                conn.execute(text("DELETE FROM shots WHERE match_id = :id"), {"id": match_id})
                conn.execute(text("DELETE FROM rosters WHERE match_id = :id"), {"id": match_id})

                # 2. INIEZIONE TIRI (Con scudo anti-duplicati nello stesso minuto)
                for side in ['h', 'a']:
                    for s in data['shots'].get(side, []):
                        conn.execute(text("""
                            INSERT INTO shots (match_id, player_id, player, minute, "xG", "X", "Y", result, team_type, situation, shot_type, "lastAction", player_assisted)
                            VALUES (:m_id, :p_id, :p, :min, :xg, :x, :y, :res, :side, :sit, :stype, :last, :passist)
                            ON CONFLICT (match_id, player, minute) DO NOTHING
                        """), {
                            "m_id": match_id, "p_id": safe_int(s.get('player_id')), "p": s.get('player'), 
                            "min": safe_int(s.get('minute')), "xg": safe_float(s.get('xG')),
                            "x": safe_float(s.get('X')), "y": safe_float(s.get('Y')), "res": s.get('result'),
                            "side": 'home' if side == 'h' else 'away', "sit": s.get('situation'), 
                            "stype": s.get('shotType'), "last": s.get('lastAction'), "passist": s.get('player_assisted')
                        })

                # 3. INIEZIONE ROSTERS (Con scudo anti-duplicati player_id)
                for side in ['h', 'a']:
                    r_dict = data['rosters'].get(side, {})
                    r_list = r_dict.values() if isinstance(r_dict, dict) else r_list
                    for r in r_list:
                        conn.execute(text("""
                            INSERT INTO rosters (match_id, player_id, player, position, "time", goals, assists, shots, key_passes, "xG", "xA", "xGChain", "xGBuildup", team_type)
                            VALUES (:m_id, :p_id, :p, :pos, :time, :g, :a, :sh, :kp, :xg, :xa, :xgc, :xgb, :side)
                            ON CONFLICT (match_id, player_id) DO NOTHING
                        """), {
                            "m_id": match_id, "p_id": safe_int(r.get('player_id')), "p": r.get('player'),
                            "pos": r.get('position'), "time": safe_int(r.get('time')), "g": safe_int(r.get('goals')),
                            "a": safe_int(r.get('assists')), "sh": safe_int(r.get('shots')), "kp": safe_int(r.get('key_passes')),
                            "xg": safe_float(r.get('xG')), "xa": safe_float(r.get('xA')), "xgc": safe_float(r.get('xGChain')),
                            "xgb": safe_float(r.get('xGBuildup')), "side": 'home' if side == 'h' else 'away'
                        })

                # 4. MARCATURA FINALE
                conn.execute(text("UPDATE matchcalendar SET is_scraped = True WHERE id = :id"), {"id": match_id})

            logging.info(f"✅ Match {match_id} BONIFICATO SENZA ERRORI.")
            time.sleep(random.uniform(1.5, 3))

        except Exception as e:
            logging.error(f"❌ Errore critico Match {match_id}: {e}")
            time.sleep(5)

    page.quit()

if __name__ == "__main__":
    professional_hammer_sync()