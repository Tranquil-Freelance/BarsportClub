import time
import random
import logging
import re
import json
from DrissionPage import ChromiumPage
from sqlalchemy import create_engine, text

# ==========================================
# CONFIGURAZIONE DATABASE
# ==========================================
DB_URI = "postgresql://postgres:password@localhost:5432/xpalermostat" 
engine = create_engine(DB_URI)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def get_val(data_dict, keys):
    """Cerca una chiave in modo flessibile per i dati raw."""
    if not data_dict: return None
    lowered_data = {k.lower(): v for k, v in data_dict.items()}
    for k in keys:
        if k.lower() in lowered_data and lowered_data[k.lower()] is not None:
            return lowered_data[k.lower()]
    return None

def browser_scraper_stealth():
    logging.info("🚀 Avvio Scraper di Precisione: Coordinate Tiri e Rosters 2025/26.")
    page = ChromiumPage()

    while True:
        with engine.connect() as conn:
            # Cerca i match del 2025/26 che hanno bisogno di micro-dati
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
            logging.info("🏁 DATABASE MICRO-DATI COMPLETO: Stagione 2025/26 chiusa e blindata.")
            break

        match_id, league_id, m_date = match
        url = f"https://understat.com/match/{match_id}"
        
        try:
            logging.info(f"🔍 Accesso Match {match_id} (Lega {league_id}) del {m_date}")
            page.get(url)
            
            # --- Jitter di Sicurezza Estrema ---
            time.sleep(random.uniform(5, 12))
            page.scroll.down(random.randint(600, 1000))
            time.sleep(random.uniform(2, 5))

            html = page.html
            s_match = re.search(r"shotsData\s+=\s+JSON\.parse\('(.+?)'\)", html)
            r_match = re.search(r"rostersData\s+=\s+JSON\.parse\('(.+?)'\)", html)

            # --- Gestione Ban / Ghost ---
            if not s_match or not r_match:
                page_text = html.lower()
                if "not found" in page_text or "error 404" in page_text:
                    logging.warning(f"👻 ID {match_id} è un 404 reale. Marcato come Ghost.")
                    with engine.begin() as conn:
                        conn.execute(text("UPDATE matchcalendar SET is_scraped = True WHERE id = :id"), {"id": match_id})
                        conn.execute(text("INSERT INTO rosters (match_id, player_id, player, team_type) VALUES (:id, 0, 'GHOST_2025', 'ghost') ON CONFLICT DO NOTHING"), {"id": match_id})
                    continue
                else:
                    logging.warning(f"⛔ Rilevato blocco Cloudflare/IP sul Match {match_id}.")
                    logging.info("⏳ IBERNAZIONE: Sospensione script per 30 minuti...")
                    time.sleep(1800)
                    logging.info("♻️ Risveglio completato. Riprendo il lavoro...")
                    continue 

            shots = json.loads(s_match.group(1).encode('utf-8').decode('unicode_escape'))
            rosters = json.loads(r_match.group(1).encode('utf-8').decode('unicode_escape'))

            with engine.begin() as conn:
                # --- SISTEMA UPSERT: Aggiunge senza distruggere ---

                for side in ['h', 'a']:
                    for s in shots.get(side, []):
                        stype = get_val(s, ['shotType', 'shot_type', 'shottype'])
                        laction = get_val(s, ['lastAction', 'last_action', 'lastaction'])
                        passist = get_val(s, ['player_assisted', 'player_assisted_name'])
                        
                        conn.execute(text("""
                            INSERT INTO shots (id, match_id, player_id, player, minute, "xG", "X", "Y", result, team_type, situation, shot_type, "lastAction", player_assisted)
                            VALUES (:s_id, :m_id, :p_id, :p, :min, :xg, :x, :y, :res, :side, :sit, :stype, :last, :passist)
                            ON CONFLICT DO NOTHING
                        """), {
                            "s_id": int(s.get('id', 0)) if s.get('id') else None,
                            "m_id": match_id, "p_id": s.get('player_id'), "p": s.get('player'), "min": int(s.get('minute', 0)),
                            "xg": float(s.get('xG', 0)), "x": float(s.get('X', 0)), "y": float(s.get('Y', 0)),
                            "res": s.get('result'), "side": 'home' if side == 'h' else 'away', "sit": s.get('situation'), 
                            "stype": stype, "last": laction, "passist": passist
                        })

                for side in ['h', 'a']:
                    for p_id, p in rosters.get(side, {}).items():
                        conn.execute(text("""
                            INSERT INTO rosters (match_id, player_id, player, position, "time", goals, assists, shots, key_passes, "xG", "xA", "xGChain", "xGBuildup", team_type)
                            VALUES (:m_id, :p_id, :p, :pos, :time, :g, :a, :sh, :kp, :xg, :xa, :xgc, :xgb, :side)
                            ON CONFLICT DO NOTHING
                        """), {
                            "m_id": match_id, "p_id": p_id, "p": p.get('player'), "pos": p.get('position'), "time": int(p.get('time', 0)),
                            "g": int(p.get('goals', 0)), "a": int(p.get('assists', 0)), "sh": int(p.get('shots', 0)), "kp": int(p.get('key_passes', 0)),
                            "xg": float(p.get('xG', 0)), "xa": float(p.get('xA', 0)), "xgc": float(p.get('xGChain', 0)), "xgb": float(p.get('xGBuildup', 0)),
                            "side": 'home' if side == 'h' else 'away'
                        })

                # Semaforo verde sul match
                conn.execute(text("UPDATE matchcalendar SET is_scraped = True WHERE id = :id"), {"id": match_id})

            logging.info(f"✅ Match {match_id} completato con coordinate e rosters.")

        except Exception as e:
            logging.error(f"❌ Errore critico Match {match_id}: {e}")
            time.sleep(15)

    page.quit()

if __name__ == "__main__":
    browser_scraper_stealth()