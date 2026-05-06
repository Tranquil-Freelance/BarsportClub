import time
import random
import logging
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
    """Estrae i valori bypassando i cambi di nome delle chiavi di Understat."""
    if not data_dict: return None
    lowered_data = {k.lower(): v for k, v in data_dict.items()}
    for k in keys:
        if k.lower() in lowered_data and lowered_data[k.lower()] is not None:
            return lowered_data[k.lower()]
    return None

def phantom_injector_scraper():
    logging.info("🚀 SNIPER v30: Phantom Injector. Simulazione Console F12 Attiva.")
    
    page = ChromiumPage()
    consecutive_errors = 0

    while True:
        with engine.connect() as conn:
            # Query per la stagione 2025/26 (caccia ai buchi nei tiri o giocatori mancanti)
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
            logging.info("🏁 DATABASE COMPLETO: Nessun match rimasto da estrarre per il 2025/26.")
            break

        match_id, league_id, m_date = match
        url = f"https://understat.com/match/{match_id}"
        
        try:
            logging.info(f"🔍 Accesso stealth al Match {match_id} (Lega {league_id})...")
            page.get(url)
            
            # --- COMPORTAMENTO UMANO (JITTER E SCROLL) ---
            time.sleep(random.uniform(4, 7))
            page.scroll.down(random.randint(400, 800))
            time.sleep(random.uniform(1, 3))
            
            # --- VERIFICA VARIABILI IN CONSOLE ---
            # Aspettiamo che shotsData e rostersData si materializzino nella RAM del browser
            dati_pronti = False
            for attesa in range(15):
                check = page.run_js("return (typeof window.shotsData !== 'undefined' && typeof window.rostersData !== 'undefined');")
                if check:
                    dati_pronti = True
                    break
                time.sleep(1)

            if not dati_pronti:
                page_text = page.html.lower()
                if "not found" in page_text or "error 404" in page_text:
                    logging.warning(f"👻 Match {match_id} è un 404 reale. Segno come Ghost.")
                    with engine.begin() as conn:
                        conn.execute(text("UPDATE matchcalendar SET is_scraped = True WHERE id = :id"), {"id": match_id})
                        conn.execute(text("INSERT INTO rosters (match_id, player_id, player, team_type) VALUES (:id, 0, 'GHOST_2025', 'ghost') ON CONFLICT DO NOTHING"), {"id": match_id})
                    consecutive_errors = 0
                    continue
                else:
                    # --- IBERNAZIONE ANTI-BAN (30 MINUTI) ---
                    logging.warning(f"⛔ Variabili non trovate sul Match {match_id}. Possibile blocco.")
                    consecutive_errors += 1
                    if consecutive_errors >= 3:
                        logging.info("⏳ IBERNAZIONE DI SICUREZZA: Sospensione per 30 minuti...")
                        time.sleep(1800)
                        consecutive_errors = 0
                        logging.info("♻️ Risveglio completato. Riprendo le operazioni.")
                    else:
                        time.sleep(15)
                    continue

            # =========================================================
            # ESTRAZIONE F12: PRELEVIAMO IL JSON PURO DALLA MEMORIA
            # =========================================================
            # Uso JSON.stringify lato JS per essere sicuro che i dati passino intatti a Python
            raw_json_string = page.run_js("""
                let sData = typeof window.shotsData !== 'undefined' ? window.shotsData : {};
                let rData = typeof window.rostersData !== 'undefined' ? window.rostersData : (typeof window.playersData !== 'undefined' ? window.playersData : {});
                return JSON.stringify({ shots: sData, rosters: rData });
            """)
            
            # Decodifichiamo in Python
            raw_data = json.loads(raw_json_string)

            with engine.begin() as conn:
                # --- SISTEMA UPSERT (ON CONFLICT DO NOTHING) ---
                
                # Inserimento SHOTS
                for side in ['h', 'a']:
                    for s in raw_data['shots'].get(side, []):
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

                # Inserimento ROSTERS
                for side in ['h', 'a']:
                    roster_side = raw_data['rosters'].get(side, {})
                    roster_items = roster_side.values() if isinstance(roster_side, dict) else (roster_side if isinstance(roster_side, list) else [])
                    
                    for r in roster_items:
                        conn.execute(text("""
                            INSERT INTO rosters (match_id, player_id, player, position, "time", goals, assists, shots, key_passes, "xG", "xA", "xGChain", "xGBuildup", yellow_card, red_card, team_type)
                            VALUES (:m_id, :p_id, :p, :pos, :time, :g, :a, :sh, :kp, :xg, :xa, :xgc, :xgb, :yc, :rc, :side)
                            ON CONFLICT DO NOTHING
                        """), {
                            "m_id": match_id, "p_id": r.get('player_id'), "p": r.get('player'), "pos": r.get('position'), "time": int(r.get('time', 0)),
                            "g": int(r.get('goals', 0)), "a": int(r.get('assists', 0)), "sh": int(r.get('shots', 0)), "kp": int(r.get('key_passes', 0)),
                            "xg": float(r.get('xG', 0)), "xa": float(r.get('xA', 0)), "xgc": float(r.get('xGChain', 0)), "xgb": float(r.get('xGBuildup', 0)),
                            "yc": int(r.get('yellow_card', 0)), "rc": int(r.get('red_card', 0)), "side": 'home' if side == 'h' else 'away'
                        })

                # Chiusura semaforo
                conn.execute(text("UPDATE matchcalendar SET is_scraped = True WHERE id = :id"), {"id": match_id})

            logging.info(f"✅ Match {match_id}: Dati catturati da JS e iniettati (Upsert).")
            consecutive_errors = 0
            time.sleep(random.uniform(4, 8)) # Jitter di uscita

        except Exception as e:
            logging.error(f"❌ Errore critico Match {match_id}: {e}")
            consecutive_errors += 1
            time.sleep(15)

    page.quit()

if __name__ == "__main__":
    phantom_injector_scraper()