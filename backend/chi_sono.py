import time
import random
import logging
import json
from DrissionPage import ChromiumPage, ChromiumOptions
from sqlalchemy import create_engine, text

# ==========================================
# CONFIGURAZIONE DATABASE
# ==========================================
DB_URI = "postgresql://postgres:password@localhost:5432/xpalermostat" # Metti la tua pass
engine = create_engine(DB_URI)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Leghe e stagioni bersaglio su Understat (5 anni + attuale)
TARGET_LEAGUES = ['Serie_A', 'EPL', 'La_liga', 'Bundesliga', 'Ligue_1']
TARGET_SEASONS = ['2025', '2024', '2023', '2022', '2021', '2020']

def safe_float(val):
    try: return float(val)
    except: return 0.0

def safe_int(val):
    try: return int(val)
    except: return 0

def get_or_create_league(conn, league_slug):
    """Trova l'ID della lega nel DB o la crea se non esiste, rispettando i vincoli NOT NULL."""
    clean_name = league_slug.replace('_', ' ')
    res = conn.execute(text("SELECT id FROM league WHERE understat_slug = :slug LIMIT 1"), {"slug": league_slug}).fetchone()
    if res:
        return res[0]
    else:
        res = conn.execute(text("INSERT INTO league (name, understat_slug) VALUES (:name, :slug) RETURNING id"), 
                           {"name": clean_name, "slug": league_slug}).fetchone()
        return res[0]

def upsert_team(conn, team_id, team_name, league_db_id):
    """Assicura che la squadra esista nel DB rispettando la Foreign Key league_id."""
    conn.execute(text("""
        INSERT INTO team (id, name, league_id) VALUES (:id, :name, :l_id)
        ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, league_id = EXCLUDED.league_id
    """), {"id": team_id, "name": team_name, "l_id": league_db_id})

def master_scraper_sync():
    logging.info("🌍 MASTER SCRAPER v53: Sincronizzazione Totale 2020-2025")
   
    co = ChromiumOptions()
    co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    page = ChromiumPage(co)

    for season in TARGET_SEASONS:
        for league in TARGET_LEAGUES:
            league_url = f"https://understat.com/league/{league}/{season}"
            logging.info(f"\n==================================================")
            logging.info(f"🏆 INIZIO SINCRONIZZAZIONE: {league.upper()} - Stagione {season}")
            logging.info(f"==================================================")
            
            try:
                # 1. FASE MACRO: Lettura del Calendario dalla Lega
                page.get(league_url)
                time.sleep(2) # Pausa caricamento
                
                raw_dates = page.run_js("return (typeof window.datesData !== 'undefined') ? JSON.stringify(window.datesData) : null;")
                if not raw_dates:
                    logging.warning(f"⚠️ Dati non trovati per {league} {season}. Salto.")
                    continue
                
                dates_data = json.loads(raw_dates)
                matches_to_scrape = []

                with engine.begin() as conn:
                    league_db_id = get_or_create_league(conn, league)

                    for match in dates_data:
                        match_id = int(match['id'])
                        is_result = match.get('isResult', False)
                        
                        # Creiamo/Aggiorniamo le squadre nel DB
                        h_team_id = int(match['h']['id'])
                        a_team_id = int(match['a']['id'])
                        upsert_team(conn, h_team_id, match['h']['title'], league_db_id)
                        upsert_team(conn, a_team_id, match['a']['title'], league_db_id)

                        # Se la partita è finita, prendiamo i dati macro
                        h_goals = safe_int(match.get('goals', {}).get('h')) if is_result else None
                        a_goals = safe_int(match.get('goals', {}).get('a')) if is_result else None
                        h_xg = safe_float(match.get('xG', {}).get('h')) if is_result else None
                        a_xg = safe_float(match.get('xG', {}).get('a')) if is_result else None
                        
                        # Statistiche avanzate
                        h_xpts = safe_float(match.get('xpts')) if is_result else None
                        a_xpts = safe_float(match.get('a', {}).get('xpts')) if is_result and 'a' in match and 'xpts' in match['a'] else None
                        h_deep = safe_int(match['h'].get('deep')) if is_result and 'deep' in match['h'] else 0
                        a_deep = safe_int(match['a'].get('deep')) if is_result and 'deep' in match['a'] else 0
                        
                        h_ppda = 0.0
                        if is_result and 'ppda' in match['h'] and safe_float(match['h']['ppda'].get('def')) > 0:
                            h_ppda = safe_float(match['h']['ppda'].get('att')) / safe_float(match['h']['ppda'].get('def'))
                        
                        a_ppda = 0.0
                        if is_result and 'ppda' in match['a'] and safe_float(match['a']['ppda'].get('def')) > 0:
                            a_ppda = safe_float(match['a']['ppda'].get('att')) / safe_float(match['a']['ppda'].get('def'))

                        # Controlliamo lo stato attuale del match nel nostro database
                        db_status = conn.execute(text("SELECT is_scraped FROM matchcalendar WHERE id = :id"), {"id": match_id}).fetchone()
                        is_scraped_in_db = db_status[0] if db_status else False

                        # UPSERT del Calendario
                        conn.execute(text("""
                            INSERT INTO matchcalendar (
                                id, league_id, home_team_id, away_team_id, match_datetime, 
                                is_completed, is_scraped, home_goals, away_goals, 
                                "home_xG", "away_xG", home_deep, away_deep, home_ppda, away_ppda, home_xpts, away_xpts
                            ) VALUES (
                                :id, :l_id, :h_id, :a_id, :m_date, 
                                :is_comp, :is_scrap, :h_g, :a_g, 
                                :h_xg, :a_xg, :h_deep, :a_deep, :h_ppda, :a_ppda, :h_xpts, :a_xpts
                            )
                            ON CONFLICT (id) DO UPDATE SET 
                                is_completed = EXCLUDED.is_completed,
                                home_goals = EXCLUDED.home_goals,
                                away_goals = EXCLUDED.away_goals,
                                "home_xG" = EXCLUDED."home_xG",
                                "away_xG" = EXCLUDED."away_xG",
                                home_deep = EXCLUDED.home_deep,
                                away_deep = EXCLUDED.away_deep,
                                home_ppda = EXCLUDED.home_ppda,
                                away_ppda = EXCLUDED.away_ppda,
                                home_xpts = EXCLUDED.home_xpts,
                                away_xpts = EXCLUDED.away_xpts
                        """), {
                            "id": match_id, "l_id": league_db_id, "h_id": h_team_id, "a_id": a_team_id,
                            "m_date": match['datetime'], "is_comp": is_result, "is_scrap": is_scraped_in_db,
                            "h_g": h_goals, "a_g": a_goals, "h_xg": h_xg, "a_xg": a_xg,
                            "h_deep": h_deep, "a_deep": a_deep, "h_ppda": h_ppda, "a_ppda": a_ppda,
                            "h_xpts": h_xpts, "a_xpts": a_xpts
                        })

                        if is_result and not is_scraped_in_db:
                            matches_to_scrape.append(match_id)

                logging.info(f"📊 {league} {season}: Calendario aggiornato. Match da scavare: {len(matches_to_scrape)}")

                # 2. FASE MICRO: Scrape chirurgico
                for m_id in matches_to_scrape:
                    match_url = f"https://understat.com/match/{m_id}"
                    logging.info(f"   🎯 Analisi Micro Match {m_id}...")
                    page.get(match_url)
                    
                    data_found = False
                    raw_match_json = None
                    
                    for _ in range(15):
                        if page.run_js("return (typeof window.shotsData !== 'undefined' && typeof window.rostersData !== 'undefined');"):
                            raw_match_json = page.run_js("return JSON.stringify({shots: window.shotsData, rosters: window.rostersData});")
                            data_found = True
                            break
                        page.scroll.down(100)
                        time.sleep(0.5)

                    if not data_found or not raw_match_json:
                        logging.warning(f"   ⛔ Match {m_id} non caricato. Sigillo.")
                        with engine.begin() as conn:
                            conn.execute(text("UPDATE matchcalendar SET is_scraped = TRUE WHERE id = :id"), {"id": m_id})
                        continue

                    match_data = json.loads(raw_match_json)

                    with engine.begin() as conn:
                        conn.execute(text("DELETE FROM shots WHERE match_id = :id"), {"id": m_id})
                        conn.execute(text("DELETE FROM rosters WHERE match_id = :id"), {"id": m_id})

                        # Iniezione Tiri
                        for side in ['h', 'a']:
                            for s in match_data['shots'].get(side, []):
                                conn.execute(text("""
                                    INSERT INTO shots (match_id, player_id, player, minute, "xG", "X", "Y", result, team_type, situation, shot_type, "lastAction", player_assisted)
                                    VALUES (:m_id, :p_id, :p, :min, :xg, :x, :y, :res, :side, :sit, :stype, :last, :passist)
                                    ON CONFLICT (match_id, player, minute) DO NOTHING
                                """), {
                                    "m_id": m_id, "p_id": safe_int(s.get('player_id')), "p": s.get('player'),
                                    "min": safe_int(s.get('minute')), "xg": safe_float(s.get('xG')),
                                    "x": safe_float(s.get('X')), "y": safe_float(s.get('Y')), "res": s.get('result'),
                                    "side": 'home' if side == 'h' else 'away', "sit": s.get('situation'),
                                    "stype": s.get('shotType'), "last": s.get('lastAction'), "passist": s.get('player_assisted')
                                })

                        # Iniezione Rosters
                        for side in ['h', 'a']:
                            r_dict = match_data['rosters'].get(side, {})
                            r_list = r_dict.values() if isinstance(r_dict, dict) else r_dict
                            for r in r_list:
                                conn.execute(text("""
                                    INSERT INTO rosters (match_id, player_id, player, position, "time", goals, assists, shots, key_passes, "xG", "xA", "xGChain", "xGBuildup", team_type)
                                    VALUES (:m_id, :p_id, :p, :pos, :time, :g, :a, :sh, :kp, :xg, :xa, :xgc, :xgb, :side)
                                    ON CONFLICT (match_id, player_id) DO NOTHING
                                """), {
                                    "m_id": m_id, "p_id": safe_int(r.get('player_id')), "p": r.get('player'),
                                    "pos": r.get('position'), "time": safe_int(r.get('time')), "g": safe_int(r.get('goals')),
                                    "a": safe_int(r.get('assists')), "sh": safe_int(r.get('shots')), "kp": safe_int(r.get('key_passes')),
                                    "xg": safe_float(r.get('xG')), "xa": safe_float(r.get('xA')), "xgc": safe_float(r.get('xGChain')),
                                    "xgb": safe_float(r.get('xGBuildup')), "side": 'home' if side == 'h' else 'away'
                                })

                        conn.execute(text("UPDATE matchcalendar SET is_scraped = TRUE WHERE id = :id"), {"id": m_id})

                    logging.info(f"   ✅ Match {m_id} archiviato.")
                    time.sleep(random.uniform(1.5, 3.5)) # Jitter Originale

            except Exception as e:
                logging.error(f"❌ Crash su {league} - {season}: {e}")
                time.sleep(5)

    page.quit()
    logging.info("🏁 SINCRONIZZAZIONE GLOBALE 2020-2025 COMPLETATA.")

if __name__ == "__main__":
    master_scraper_sync()