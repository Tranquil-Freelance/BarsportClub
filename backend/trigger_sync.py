import time
import random
import logging
from DrissionPage import ChromiumPage
from sqlalchemy import create_engine, text

# ==========================================
# CONFIGURAZIONE DATABASE
# ==========================================
DB_URI = "postgresql://postgres:password@localhost:5432/xpalermostat" 
engine = create_engine(DB_URI)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def get_val(data_dict, keys):
    if not data_dict: return None
    lowered_data = {k.lower(): v for k, v in data_dict.items()}
    for k in keys:
        if k.lower() in lowered_data and lowered_data[k.lower()] is not None:
            return lowered_data[k.lower()]
    return None

def safe_float(val):
    try: return float(val)
    except: return 0.0

def safe_int(val):
    try: return int(val)
    except: return 0

def fast_automator_scraper():
    logging.info("🚀 SNIPER v35: Fast Automator (Fix Ribattute e Duplicati)")
    
    page = ChromiumPage()
    consecutive_errors = 0

    while True:
        with engine.connect() as conn:
            query = text("""
                SELECT m.id, m.league_id, m.match_datetime 
                FROM matchcalendar m
                WHERE m.match_datetime > '2025-07-01'
                AND m.match_datetime < NOW() - INTERVAL '1 hour'
                AND (
                    m.is_scraped = False 
                    OR NOT EXISTS (SELECT 1 FROM rosters r WHERE r.match_id = m.id)
                    OR EXISTS (SELECT 1 FROM shots s WHERE s.match_id = m.id AND s.shot_type IS NULL)
                )
                AND NOT EXISTS (
                    SELECT 1 FROM rosters r2 WHERE r2.match_id = m.id AND r2.team_type = 'ghost'
                )
                ORDER BY m.match_datetime DESC LIMIT 1
            """)
            match = conn.execute(query).fetchone()

        if not match:
            logging.info("🏁 DATABASE COMPLETO: Stagione 2025/26 sincronizzata e blindata al 100%.")
            break

        match_id, league_id, m_date = match
        url = f"https://understat.com/match/{match_id}"
        
        try:
            logging.info(f"⚡ Incursione Match {match_id} (Lega {league_id})...")
            page.get(url)
            
            time.sleep(random.uniform(0.5, 1.5))
            page.scroll.to_bottom()
            time.sleep(random.uniform(0.2, 0.5))
            page.scroll.to_top()
            
            dati_pronti = False
            for attesa in range(50):
                check = page.run_js("return (typeof window.shotsData !== 'undefined');")
                if check:
                    dati_pronti = True
                    break
                time.sleep(0.2)

            if not dati_pronti:
                page_text = page.html.lower()
                if "not found" in page_text or "error 404" in page_text:
                    logging.warning(f"👻 Match {match_id} 404 reale. Segno come Ghost.")
                    with engine.begin() as conn:
                        conn.execute(text("UPDATE matchcalendar SET is_scraped = True WHERE id = :id"), {"id": match_id})
                        conn.execute(text("INSERT INTO rosters (match_id, player_id, player, team_type) VALUES (:id, 0, 'GHOST_2025', 'ghost') ON CONFLICT DO NOTHING"), {"id": match_id})
                    consecutive_errors = 0
                    continue
                else:
                    logging.warning(f"⛔ Blocco rilevato su Match {match_id}.")
                    consecutive_errors += 1
                    if consecutive_errors >= 3:
                        logging.info("☕ CAFFÈ TIME: Ibernazione profonda per 30 minuti...")
                        time.sleep(1800)
                        consecutive_errors = 0
                        logging.info("🟢 Pausa terminata. Ripartiamo.")
                    else:
                        time.sleep(10)
                    continue

            raw_data = page.run_js("""
                let sData = typeof window.shotsData !== 'undefined' ? window.shotsData : {};
                let rData = typeof window.rostersData !== 'undefined' ? window.rostersData : (typeof window.playersData !== 'undefined' ? window.playersData : {});
                return { shots: sData, rosters: rData };
            """)

            with engine.begin() as conn:
                conn.execute(text("DELETE FROM shots WHERE match_id = :id"), {"id": match_id})
                conn.execute(text("DELETE FROM rosters WHERE match_id = :id"), {"id": match_id})

                # --- INSERIMENTO SHOTS (ON CONFLICT DO NOTHING SUL MINUTO) ---
                for side in ['h', 'a']:
                    for s in raw_data['shots'].get(side, []):
                        stype = get_val(s, ['shotType', 'shot_type', 'shottype'])
                        laction = get_val(s, ['lastAction', 'last_action', 'lastaction'])
                        passist = get_val(s, ['player_assisted', 'player_assisted_name'])
                        
                        conn.execute(text("""
                            INSERT INTO shots (id, match_id, player_id, player, minute, "xG", "X", "Y", result, team_type, situation, shot_type, "lastAction", player_assisted)
                            VALUES (:s_id, :m_id, :p_id, :p, :min, :xg, :x, :y, :res, :side, :sit, :stype, :last, :passist)
                            ON CONFLICT (match_id, player, minute) DO NOTHING
                        """), {
                            "s_id": safe_int(s.get('id', 0)) if s.get('id') else None,
                            "m_id": match_id, "p_id": safe_int(s.get('player_id')), "p": s.get('player'), "min": safe_int(s.get('minute', 0)),
                            "xg": safe_float(s.get('xG', 0)), "x": safe_float(s.get('X', 0)), "y": safe_float(s.get('Y', 0)),
                            "res": s.get('result'), "side": 'home' if side == 'h' else 'away', "sit": s.get('situation'), 
                            "stype": stype, "last": laction, "passist": passist
                        })

                # --- INSERIMENTO ROSTERS (ON CONFLICT DO NOTHING SUL PLAYER_ID) ---
                for side in ['h', 'a']:
                    roster_side = raw_data['rosters'].get(side, {})
                    roster_items = roster_side.values() if isinstance(roster_side, dict) else (roster_side if isinstance(roster_side, list) else [])
                    
                    for r in roster_items:
                        conn.execute(text("""
                            INSERT INTO rosters (match_id, player_id, player, position, "time", goals, assists, shots, key_passes, "xG", "xA", "xGChain", "xGBuildup", yellow_card, red_card, team_type)
                            VALUES (:m_id, :p_id, :p, :pos, :time, :g, :a, :sh, :kp, :xg, :xa, :xgc, :xgb, :yc, :rc, :side)
                            ON CONFLICT (match_id, player_id) DO NOTHING
                        """), {
                            "m_id": match_id, "p_id": safe_int(r.get('player_id')), "p": r.get('player'), "pos": r.get('position'), "time": safe_int(r.get('time', 0)),
                            "g": safe_int(r.get('goals', 0)), "a": safe_int(r.get('assists', 0)), "sh": safe_int(r.get('shots', 0)), "kp": safe_int(r.get('key_passes', 0)),
                            "xg": safe_float(r.get('xG', 0)), "xa": safe_float(r.get('xA', 0)), "xgc": safe_float(r.get('xGChain', 0)), "xgb": safe_float(r.get('xGBuildup', 0)),
                            "yc": safe_int(r.get('yellow_card', 0)), "rc": safe_int(r.get('red_card', 0)), "side": 'home' if side == 'h' else 'away'
                        })

                conn.execute(text("UPDATE matchcalendar SET is_scraped = True WHERE id = :id"), {"id": match_id})

            logging.info(f"✅ Match {match_id} fulminato e salvato.")
            consecutive_errors = 0
            time.sleep(random.uniform(2, 4)) 

        except Exception as e:
            logging.error(f"❌ Errore critico Match {match_id}: {e}")
            consecutive_errors += 1
            time.sleep(15)

    page.quit()

if __name__ == "__main__":
    fast_automator_scraper()