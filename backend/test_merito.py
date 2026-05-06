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

def professional_2025_cleanup():
    logging.info("🚀 SNIPER v50: Protocollo Zero Conflict (Macro + Micro)")
    
    co = ChromiumOptions()
    co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    page = ChromiumPage(co)

    try:
        # --- 1. SINCRONIZZAZIONE MACRO (PAGINE LEGA) ---
        leghe = ["Serie_A", "Premier_League", "La_liga", "Bundesliga", "Ligue_1"]
        for lega in leghe:
            logging.info(f"📊 Fase 1: Sincronizzazione Macro Lega: {lega}...")
            page.get(f"https://understat.com/league/{lega}/2025")
            time.sleep(5)
            
            raw_teams = page.run_js("return (typeof teamsData !== 'undefined') ? JSON.stringify(teamsData) : null;")
            if raw_teams:
                teams_data = json.loads(raw_teams)
                with engine.begin() as conn:
                    for t_id in teams_data:
                        for entry in teams_data[t_id].get('history', []):
                            ppda_v = safe_float(entry['ppda']['att']) / safe_float(entry['ppda']['def']) if safe_float(entry['ppda']['def']) != 0 else 0
                            
                            # SQL con CAST standard per evitare conflitti con i ":" di SQLAlchemy
                            sql = text("""
                                UPDATE matchcalendar SET 
                                home_ppda = CASE WHEN home_team_id = :t_id THEN :ppda ELSE home_ppda END,
                                home_xpts = CASE WHEN home_team_id = :t_id THEN :xpts ELSE home_xpts END,
                                home_deep = CASE WHEN home_team_id = :t_id THEN :deep ELSE home_deep END,
                                away_ppda = CASE WHEN away_team_id = :t_id THEN :ppda ELSE away_ppda END,
                                away_xpts = CASE WHEN away_team_id = :t_id THEN :xpts ELSE away_xpts END,
                                away_deep = CASE WHEN away_team_id = :t_id THEN :deep ELSE away_deep END
                                WHERE (home_team_id = :t_id OR away_team_id = :t_id)
                                AND CAST(match_datetime AS DATE) = CAST(:date_val AS DATE)
                            """)
                            conn.execute(sql, {
                                "ppda": ppda_v, 
                                "xpts": safe_float(entry['xpts']), 
                                "deep": safe_float(entry['deep']), 
                                "t_id": int(t_id), 
                                "date_val": entry['date']
                            })
                logging.info(f"✅ Lega {lega} sincronizzata.")

        # --- 2. BONIFICA MICRO (PAGINE MATCH - METODO F12) ---
        logging.info("🕵️ Fase 2: Inizio bonifica Micro su tutti i buchi del 2025...")
        while True:
            with engine.connect() as conn:
                # Seleziona un match del 2025 che non ha tiri registrati
                query = text("""
                    SELECT m.id FROM matchcalendar m
                    WHERE m.match_datetime > '2025-07-01' 
                    AND m.is_completed = true
                    AND NOT EXISTS (SELECT 1 FROM shots s WHERE s.match_id = m.id)
                    LIMIT 1
                """)
                match = conn.execute(query).fetchone()

            if not match:
                logging.info("🏁 MISSIONE COMPIUTA: Database 2025 perfettamente integro.")
                break

            match_id = match[0]
            url = f"https://understat.com/match/{match_id}"
            
            logging.info(f"🚀 Iniezione F12 su Match {match_id}...")
            page.get(url)
            
            data = None
            # Polling RAM (Metodo Sniper v49)
            for tentativo in range(3):
                time.sleep(3)
                raw_match = page.run_js("return (typeof window.shotsData !== 'undefined' && typeof window.rostersData !== 'undefined') ? JSON.stringify({shots: window.shotsData, rosters: window.rostersData}) : null;")
                if raw_match:
                    data = json.loads(raw_match)
                    break
                page.scroll.down(200)
                logging.warning(f"⏳ Match {match_id}: RAM non popolata, tentativo {tentativo+1}...")

            if not data or 'shots' not in data:
                logging.error(f"❌ Match {match_id} fallito. Salto.")
                continue

            with engine.begin() as conn:
                # Terra bruciata preventiva
                conn.execute(text("DELETE FROM shots WHERE match_id = :id"), {"id": match_id})
                conn.execute(text("DELETE FROM rosters WHERE match_id = :id"), {"id": match_id})

                # Iniezione Tiri
                for side in ['h', 'a']:
                    for s in data['shots'].get(side, []):
                        conn.execute(text("""
                            INSERT INTO shots (match_id, player_id, player, minute, "xG", "X", "Y", result, team_type, situation, shot_type, "lastAction", player_assisted)
                            VALUES (:m_id, :p_id, :p, :min, :xg, :x, :y, :res, :side, :sit, :stype, :last, :passist)
                            ON CONFLICT DO NOTHING
                        """), {
                            "m_id": match_id, "p_id": int(s['player_id']), "p": s['player'], "min": int(s['minute']),
                            "xg": float(s['xG']), "x": float(s['X']), "y": float(s['Y']), "res": s['result'],
                            "side": 'home' if side == 'h' else 'away', "sit": s['situation'], 
                            "stype": s['shotType'], "last": s['lastAction'], "passist": s.get('player_assisted')
                        })

                # Iniezione Roster (xGChain/BuildUp)
                for side in ['h', 'a']:
                    r_dict = data['rosters'].get(side, {})
                    for r in r_dict.values():
                        conn.execute(text("""
                            INSERT INTO rosters (match_id, player_id, player, position, "time", goals, assists, shots, key_passes, "xG", "xA", "xGChain", "xGBuildup", team_type)
                            VALUES (:m_id, :p_id, :p, :pos, :time, :g, :a, :sh, :kp, :xg, :xa, :xgc, :xgb, :side)
                            ON CONFLICT DO NOTHING
                        """), {
                            "m_id": match_id, "p_id": int(r['player_id']), "p": r['player'], "pos": r['position'],
                            "time": int(r['time']), "g": int(r['goals']), "a": int(r['assists']), "sh": int(r['shots']),
                            "kp": int(r['key_passes']), "xg": float(r['xG']), "xa": float(r['xA']),
                            "xgc": float(r['xGChain']), "xgb": float(r['xGBuildup']), "side": 'home' if side == 'h' else 'away'
                        })
                
                conn.execute(text("UPDATE matchcalendar SET is_scraped = True WHERE id = :id"), {"id": match_id})
            
            logging.info(f"✅ Match {match_id} bonificato.")
            time.sleep(random.uniform(2, 4))

    except Exception as e:
        logging.error(f"🚨 Errore fatale nello script: {e}")
    finally:
        page.quit()

if __name__ == "__main__":
    professional_2025_cleanup()