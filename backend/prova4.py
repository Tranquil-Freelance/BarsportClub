import time
import random
import logging
import json
from DrissionPage import ChromiumPage, ChromiumOptions
from sqlalchemy import create_engine, text

# ==========================================
# CONFIGURAZIONE - MULTI STAGIONE
# ==========================================
DB_URI = "postgresql://postgres:password@localhost:5432/xpalermostat"
engine = create_engine(DB_URI)

TARGET_LEAGUES = ['Serie_A', 'EPL', 'La_liga', 'Bundesliga', 'Ligue_1']
# Inserisci qui le 5 stagioni che hai in memoria (modifica gli anni se necessario)
TARGET_SEASONS = ['2025', '2024', '2023', '2022', '2021']

JITTER_MIN = 10.0
JITTER_MAX = 20.0
HIBERNATION_PERIOD = 1800


def safe_float(val):
    try:
        return float(val)
    except Exception:
        return 0.0


def safe_int(val):
    try:
        return int(val)
    except Exception:
        return 0


def get_ppda(p):
    if not p:
        return 0.0
    att = safe_float(p.get('att'))
    df = safe_float(p.get('def'))
    return att / df if df > 0 else 0.0


def build_matchdays_dict(dates_list):
    sorted_matches = sorted(dates_list, key=lambda x: x.get('datetime', ''))
    team_games = {}
    match_rounds = {}
    for m in sorted_matches:
        if not m.get('datetime'):
            continue
        h_id = str(m['h']['id'])
        a_id = str(m['a']['id'])
        team_games[h_id] = team_games.get(h_id, 0) + 1
        team_games[a_id] = team_games.get(a_id, 0) + 1
        round_num = max(team_games[h_id], team_games[a_id])
        match_rounds[int(m['id'])] = round_num
    return match_rounds


def make_page() -> ChromiumPage:
    """Crea un'istanza ChromiumPage headless per VPS Linux."""
    co = ChromiumOptions()
    co.headless(True)
    co.auto_port()  # <-- FIX PER EVITARE IL CRASH WEBSOCKET SU WINDOWS
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--disable-gpu')
    co.set_user_agent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    )
    return ChromiumPage(co)


def scrape_single_match(page: ChromiumPage, match_id: int) -> bool:
    """
    Scrapa shots e rosters di una singola partita.
    """
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT is_scraped FROM matchcalendar WHERE id = :id"),
            {"id": match_id}
        ).fetchone()
        if row and row[0]:
            logging.info(f"Match {match_id}: già scrapato, skip.")
            return True

    time.sleep(random.uniform(JITTER_MIN, JITTER_MAX))
    page.get(f"https://understat.com/match/{match_id}")

    if "too many requests" in page.html.lower() or "429 Too Many Requests" in page.html:
        logging.warning(f"Match {match_id}: BAN rilevato. Attendo 30 min.")
        time.sleep(HIBERNATION_PERIOD)
        page.get(f"https://understat.com/match/{match_id}")

    page.scroll.down(500)
    time.sleep(2)

    raw_match_json = page.run_js("""
        if(typeof window.shotsData !== 'undefined' && typeof window.rostersData !== 'undefined'){
            return JSON.stringify({s: window.shotsData, r: window.rostersData});
        }
        return null;
    """)

    if not raw_match_json:
        logging.info(f"Match {match_id}: dati non ancora pubblicati su understat.")
        return False

    m_json = json.loads(raw_match_json)

    with engine.begin() as conn:
        # Pulisce i vecchi dati fallati prima di inserire quelli nuovi corretti
        conn.execute(text("DELETE FROM shots WHERE match_id = :id"), {"id": match_id})
        conn.execute(text("DELETE FROM rosters WHERE match_id = :id"), {"id": match_id})

        for side in ['h', 'a']:
            for s in m_json['s'].get(side, []):
                conn.execute(text("""
                    INSERT INTO shots (match_id, player_id, player, minute, "xG", "X", "Y",
                                       result, team_type, situation, "shotType", "lastAction")
                    VALUES (:m_id, :p_id, :p, :min, :xg, :x, :y, :res, :side, :sit, :st, :la)
                    ON CONFLICT (match_id, player, minute) DO NOTHING
                """), {
                    "m_id": match_id,
                    "p_id": safe_int(s.get('player_id')),
                    "p": s.get('player'),
                    "min": safe_int(s.get('minute')),
                    "xg": safe_float(s.get('xG')),
                    "x": safe_float(s.get('X')),
                    "y": safe_float(s.get('Y')),
                    "res": s.get('result'),
                    "side": 'home' if side == 'h' else 'away',
                    "sit": s.get('situation'),
                    "st": s.get('shotType'),
                    "la": s.get('lastAction'),
                })

        for side in ['h', 'a']:
            for r in m_json['r'].get(side, {}).values():
                # Fix letale: team_type aggiunto e mappato con r.get('h_a')
                conn.execute(text("""
                    INSERT INTO rosters (match_id, player_id, player, position, "time",
                                         goals, assists, shots, key_passes, "xG", "xA", team_type)
                    VALUES (:m_id, :p_id, :p, :pos, :t, :g, :as, :sh, :kp, :xg, :xa, :team_type)
                    ON CONFLICT (match_id, player_id) DO NOTHING
                """), {
                    "m_id": match_id,
                    "p_id": safe_int(r.get('player_id')),
                    "p": r.get('player'),
                    "pos": r.get('position'),
                    "t": safe_int(r.get('time')),
                    "g": safe_int(r.get('goals')),
                    "as": safe_int(r.get('assists')),
                    "sh": safe_int(r.get('shots')),
                    "kp": safe_int(r.get('key_passes')),
                    "xg": safe_float(r.get('xG')),
                    "xa": safe_float(r.get('xA')),
                    "team_type": r.get('h_a')
                })

        result = conn.execute(
            text("UPDATE matchcalendar SET is_scraped = TRUE WHERE id = :id"),
            {"id": match_id}
        )
        if result.rowcount == 0:
            logging.warning(
                f"Match {match_id}: is_scraped non aggiornato — riga mancante in matchcalendar."
            )

    logging.info(f"✅ Match {match_id}: shots e rosters salvati.")
    return True


def sync_all_seasons_with_advanced_metrics():
    """Bulk sync per tutte le stagioni target."""
    logging.info("🚀 AVVIO BULK SYNC MULTI-STAGIONE")
    page = make_page()

    for season in TARGET_SEASONS:
        logging.info(f"🟢 INIZIO SYNC STAGIONE: {season}")
        for league in TARGET_LEAGUES:
            time.sleep(random.uniform(JITTER_MIN, JITTER_MAX))
            league_url = f"https://understat.com/league/{league}/{season}"

            try:
                page.get(league_url)

                if "too many requests" in page.html.lower() or "429 Too Many Requests" in page.html:
                    logging.warning("🚨 BAN RILEVATO. IBERNAZIONE 30 MINUTI.")
                    time.sleep(HIBERNATION_PERIOD)
                    page.get(league_url)

                page.scroll.down(1000)
                time.sleep(2)

                raw_league_json = page.run_js("""
                    if(typeof window.teamsData !== 'undefined' && typeof window.datesData !== 'undefined'){
                        return JSON.stringify({t: window.teamsData, d: window.datesData});
                    }
                    return null;
                """)

                if not raw_league_json:
                    logging.warning(f"⚠️ Impossibile trovare teamsData per {league} {season}. Salto.")
                    continue

                league_data = json.loads(raw_league_json)
                teams_dict = league_data['t']
                dates_list = league_data['d']

                match_rounds = build_matchdays_dict(dates_list)
                played_matches = [m for m in dates_list if m.get('isResult') is True]
                matches_to_process = []

                with engine.connect() as conn:
                    for m in played_matches:
                        m_id = int(m['id'])
                        
                        # <-- MODIFICA QUI: Seleziono anche i gol. Se la riga manca, o non è scrapata, 
                        # o i gol sono NULL (come nel caso del Napoli), processiamo il match.
                        row = conn.execute(
                            text("SELECT is_scraped, home_goals FROM matchcalendar WHERE id = :id"),
                            {"id": m_id}
                        ).fetchone()
                        
                        if not row or not row[0] or row[1] is None:
                            matches_to_process.append(m)

                logging.info(f"📊 {league} {season}: {len(matches_to_process)} match mancanti o da aggiornare.")

                if not matches_to_process:
                    continue

                with engine.begin() as conn:
                    for m in matches_to_process:
                        m_id = int(m['id'])
                        m_date = m['datetime']
                        h_id = str(m['h']['id'])
                        a_id = str(m['a']['id'])
                        
                        # <-- MODIFICA QUI: Estrazione sicura dei gol dal JSON di Understat
                        h_g = safe_int(m.get('goals', {}).get('h'))
                        a_g = safe_int(m.get('goals', {}).get('a'))
                        
                        computed_round = match_rounds.get(m_id, 0)
                        h_stats = next(
                            (h for h in teams_dict.get(h_id, {}).get('history', []) if h['date'] == m_date), {}
                        )
                        a_stats = next(
                            (h for h in teams_dict.get(a_id, {}).get('history', []) if h['date'] == m_date), {}
                        )
                        
                        # <-- MODIFICA QUI: Aggiunti match_datetime, home_goals e away_goals all'UPDATE
                        conn.execute(text("""
                            UPDATE matchcalendar SET
                                match_datetime = :m_date,
                                home_goals = :h_g,
                                away_goals = :a_g,
                                home_ppda = :h_ppda, away_ppda = :a_ppda,
                                home_deep = :h_deep, away_deep = :a_deep,
                                home_xpts = :h_xpts, away_xpts = :a_xpts,
                                matchday = :md, is_completed = TRUE
                            WHERE id = :id
                        """), {
                            "id": m_id,
                            "m_date": m_date,
                            "h_g": h_g,
                            "a_g": a_g,
                            "md": computed_round,
                            "h_ppda": get_ppda(h_stats.get('ppda')),
                            "a_ppda": get_ppda(a_stats.get('ppda')),
                            "h_deep": safe_int(h_stats.get('deep')),
                            "a_deep": safe_int(a_stats.get('deep')),
                            "h_xpts": safe_float(h_stats.get('xpts')),
                            "a_xpts": safe_float(a_stats.get('xpts')),
                        })

                for m in matches_to_process:
                    m_id = int(m['id'])
                    scrape_single_match(page, m_id)

            except Exception as e:
                logging.error(f"❌ Errore critico su {league} {season}: {e}")

    page.quit()
    logging.info("✅ Bulk sync multi-stagione completato.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    sync_all_seasons_with_advanced_metrics()