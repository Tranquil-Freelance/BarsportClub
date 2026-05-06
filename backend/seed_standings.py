import time
import random
import logging
import json
from DrissionPage import ChromiumPage, ChromiumOptions
from sqlalchemy import create_engine, text

# CONFIGURAZIONE
DB_URI = "postgresql://postgres:password@localhost:5432/xpalermostat" 
engine = create_engine(DB_URI)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def safe_float(val):
    try: return float(val)
    except: return 0.0

def professional_total_sync(target_ids):
    co = ChromiumOptions()
    co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    page = ChromiumPage(co)

    try:
        # --- 1. RECUPERO DATI MACRO ---
        logging.info("📊 Fase 1: Estrazione dati Macro (Serie A 2025)...")
        page.get("https://understat.com/league/Serie_A/2025")
        time.sleep(5)
        
        raw_teams = page.run_js("return JSON.stringify(teamsData);")
        if raw_teams:
            teams_data = json.loads(raw_teams)
            with engine.begin() as conn:
                for t_id in teams_data:
                    current_team_id = int(t_id)
                    for entry in teams_data[t_id].get('history', []):
                        ppda_v = safe_float(entry['ppda']['att']) / safe_float(entry['ppda']['def']) if safe_float(entry['ppda']['def']) != 0 else 0
                        
                        # Aggiornamento incrociato basato su team_id
                        sql_h = text("""
                            UPDATE matchcalendar SET 
                            home_ppda = :ppda, home_xpts = :xpts, home_deep = :deep
                            WHERE home_team_id = :t_id AND match_datetime::text LIKE :date_p
                        """)
                        conn.execute(sql_h, {"ppda": ppda_v, "xpts": safe_float(entry['xpts']), "deep": safe_float(entry['deep']), "t_id": current_team_id, "date_p": f"{entry['date']}%"})

                        sql_a = text("""
                            UPDATE matchcalendar SET 
                            away_ppda = :ppda, away_xpts = :xpts, away_deep = :deep
                            WHERE away_team_id = :t_id AND match_datetime::text LIKE :date_p
                        """)
                        conn.execute(sql_a, {"ppda": ppda_v, "xpts": safe_float(entry['xpts']), "deep": safe_float(entry['deep']), "t_id": current_team_id, "date_p": f"{entry['date']}%"})
            logging.info("✅ Dati Macro sincronizzati.")

        # --- 2. RECUPERO DATI MICRO (PAGINA PARTITA) ---
        for m_id in target_ids:
            logging.info(f"🕵️ Fase 2: Analisi Match {m_id}...")
            page.get(f"https://understat.com/match/{m_id}")
            
            data = None
            for tentativo in range(3): # 3 Tentativi di polling RAM
                time.sleep(3)
                raw_match = page.run_js("return (typeof window.shotsData !== 'undefined') ? JSON.stringify({shots: window.shotsData, rosters: window.rostersData}) : null;")
                if raw_match:
                    data = json.loads(raw_match)
                    break
                logging.warning(f"⏳ Tentativo {tentativo+1}: RAM non ancora popolata per {m_id}...")
                page.scroll.down(200)

            if not data or 'shots' not in data:
                logging.error(f"❌ Impossibile recuperare dati per Match {m_id}. Salto.")
                continue
            
            with engine.begin() as conn:
                # Pulizia chirurgica
                conn.execute(text("DELETE FROM shots WHERE match_id = :id"), {"id": m_id})
                conn.execute(text("DELETE FROM rosters WHERE match_id = :id"), {"id": m_id})

                # Inserimento Tiri
                for side in ['h', 'a']:
                    shots_list = data['shots'].get(side, [])
                    for s in shots_list:
                        conn.execute(text("""
                            INSERT INTO shots (match_id, player_id, player, minute, "xG", "X", "Y", result, team_type, situation, shot_type, "lastAction", player_assisted)
                            VALUES (:m_id, :p_id, :p, :min, :xg, :x, :y, :res, :side, :sit, :stype, :last, :passist)
                            ON CONFLICT (match_id, player, minute) DO NOTHING
                        """), {
                            "m_id": m_id, "p_id": int(s['player_id']), "p": s['player'], "min": int(s['minute']),
                            "xg": float(s['xG']), "x": float(s['X']), "y": float(s['Y']), "res": s['result'],
                            "side": 'home' if side == 'h' else 'away', "sit": s['situation'], 
                            "stype": s['shotType'], "last": s['lastAction'], "passist": s['player_assisted']
                        })
                
                # Inserimento Roster
                for side in ['h', 'a']:
                    r_dict = data['rosters'].get(side, {})
                    for r in r_dict.values():
                        conn.execute(text("""
                            INSERT INTO rosters (match_id, player_id, player, position, "time", goals, assists, shots, key_passes, "xG", "xA", "xGChain", "xGBuildup", team_type)
                            VALUES (:m_id, :p_id, :p, :pos, :time, :g, :a, :sh, :kp, :xg, :xa, :xgc, :xgb, :side)
                            ON CONFLICT (match_id, player_id) DO NOTHING
                        """), {
                            "m_id": m_id, "p_id": int(r['player_id']), "p": r['player'], "pos": r['position'],
                            "time": int(r['time']), "g": int(r['goals']), "a": int(r['assists']), "sh": int(r['shots']),
                            "kp": int(r['key_passes']), "xg": float(r['xG']), "xa": float(r['xA']),
                            "xgc": float(r['xGChain']), "xgb": float(r['xGBuildup']), "side": 'home' if side == 'h' else 'away'
                        })
                
                conn.execute(text("UPDATE matchcalendar SET is_scraped = True WHERE id = :id"), {"id": m_id})
            logging.info(f"✅ Match {m_id} Bonificato con successo.")
            time.sleep(random.uniform(2, 4))

    finally:
        page.quit()

if __name__ == "__main__":
    professional_total_sync([30139, 30140, 30141])