import time
import random
import logging
import json
from DrissionPage import ChromiumPage, ChromiumOptions
from sqlalchemy import create_engine, text

# ==========================================
# CONFIGURAZIONE - STORICO COMPLETO (2025-2021)
# ==========================================
DB_URI = "postgresql://postgres:password@localhost:5432/xpalermostat"
engine = create_engine(DB_URI)

TARGET_LEAGUES = ['Serie_A', 'EPL', 'La_liga', 'Bundesliga', 'Ligue_1']
TARGET_SEASONS = ['2025', '2024', '2023', '2022', '2021']

# TEMPI DIMEZZATI PER MASSIMA VELOCITA'
JITTER_MIN = 1.0
JITTER_MAX = 2.0
HIBERNATION_PERIOD = 1800


def safe_float(val):
    try: return float(val)
    except Exception: return 0.0

def safe_int(val):
    try: return int(val)
    except Exception: return 0

def get_ppda(p):
    if not p: return 0.0
    att = safe_float(p.get('att'))
    df = safe_float(p.get('def'))
    return att / df if df > 0 else 0.0

def build_matchdays_dict(dates_list):
    sorted_matches = sorted(dates_list, key=lambda x: x.get('datetime', ''))
    team_games = {}
    match_rounds = {}
    for m in sorted_matches:
        if not m.get('datetime'): continue
        h_id = str(m['h']['id'])
        a_id = str(m['a']['id'])
        team_games[h_id] = team_games.get(h_id, 0) + 1
        team_games[a_id] = team_games.get(a_id, 0) + 1
        round_num = max(team_games[h_id], team_games[a_id])
        match_rounds[int(m['id'])] = round_num
    return match_rounds

def make_page() -> ChromiumPage:
    co = ChromiumOptions()
    co.headless(True)
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--disable-gpu')
    co.set_user_agent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    )
    return ChromiumPage(co)

def update_standings_safely(conn, teams_dict, league_slug, season_str):
    """Aggiorna le classifiche. Salta in silenzio se c'è discordanza nei nomi."""
    l_row = conn.execute(text("SELECT id FROM league WHERE understat_slug = :slug OR name ILIKE :slug"), {"slug": f"%{league_slug}%"}).fetchone()
    if not l_row: return
    league_id = l_row[0]
    sea = f"{season_str}/{str(int(season_str)+1)[-2:]}"

    for u_id, data in teams_dict.items():
        title = data.get('title')
        t_row = conn.execute(text("SELECT id FROM team WHERE name ILIKE :title LIMIT 1"), {"title": f"%{title}%"}).fetchone()
        if not t_row: continue 

        db_team_id = t_row[0]
        history = data.get('history', [])
        if not history: continue

        conn.execute(text("""
            INSERT INTO team_season_stat (
                team_id, league_id, season, matches_played, wins, draws, losses, 
                goals_for, goals_against, points, "xG_for", "xG_against", xpts
            ) VALUES (
                :tid, :lid, :sea, :m, :w, :d, :l, :gf, :ga, :pts, :xgf, :xga, :xpts
            )
            ON CONFLICT (team_id, league_id, season) DO UPDATE SET
                matches_played = EXCLUDED.matches_played, wins = EXCLUDED.wins, draws = EXCLUDED.draws, losses = EXCLUDED.losses,
                goals_for = EXCLUDED.goals_for, goals_against = EXCLUDED.goals_against, points = EXCLUDED.points,
                "xG_for" = EXCLUDED."xG_for", "xG_against" = EXCLUDED."xG_against", xpts = EXCLUDED.xpts
        """), {
            "tid": db_team_id, "lid": league_id, "sea": sea,
            "m": len(history), "w": len([h for h in history if h.get('result') == 'w']),
            "d": len([h for h in history if h.get('result') == 'd']), "l": len([h for h in history if h.get('result') == 'l']),
            "gf": sum(safe_int(h.get('scored')) for h in history), "ga": sum(safe_int(h.get('missed')) for h in history),
            "pts": sum(safe_int(h.get('pts')) for h in history),
            "xgf": sum(safe_float(h.get('xG')) for h in history), "xga": sum(safe_float(h.get('xGA')) for h in history),
            "xpts": sum(safe_float(h.get('xpts')) for h in history)
        })

def scrape_single_match(page: ChromiumPage, match_id: int) -> bool:
    home_db_id = 0
    away_db_id = 0
    
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT is_scraped, home_team_id, away_team_id FROM matchcalendar WHERE id = :id"),
            {"id": match_id}
        ).fetchone()
        
        if row:
            if row[0]: 
                logging.info(f"Match {match_id}: già scrapato, skip.")
                return True
            home_db_id = row[1]
            away_db_id = row[2]

    time.sleep(random.uniform(JITTER_MIN, JITTER_MAX))
    page.get(f"https://understat.com/match/{match_id}")

    if "too many requests" in page.html.lower() or "429 Too Many Requests" in page.html:
        logging.warning(f"Match {match_id}: BAN rilevato. Attendo 30 min.")
        time.sleep(HIBERNATION_PERIOD)
        page.get(f"https://understat.com/match/{match_id}")

    page.scroll.down(500)
    time.sleep(1) 

    raw_match_json = page.run_js("""
        if(typeof window.shotsData !== 'undefined' && typeof window.rostersData !== 'undefined'){
            return JSON.stringify({s: window.shotsData, r: window.rostersData});
        } return null;
    """)

    if not raw_match_json: return False
    m_json = json.loads(raw_match_json)

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM shots WHERE match_id = :id"), {"id": match_id})
        conn.execute(text("DELETE FROM rosters WHERE match_id = :id"), {"id": match_id})

        for side in ['h', 'a']:
            for s in m_json['s'].get(side, []):
                conn.execute(text("""
                    INSERT INTO shots (match_id, player_id, player, minute, "xG", "X", "Y", result, team_type, situation, "shotType", "lastAction")
                    VALUES (:m_id, :p_id, :p, :min, :xg, :x, :y, :res, :side, :sit, :st, :la)
                    ON CONFLICT (match_id, player, minute) DO NOTHING
                """), {
                    "m_id": match_id, "p_id": safe_int(s.get('player_id')), "p": s.get('player'),
                    "min": safe_int(s.get('minute')), "xg": safe_float(s.get('xG')),
                    "x": safe_float(s.get('X')), "y": safe_float(s.get('Y')), "res": s.get('result'),
                    "side": 'home' if side == 'h' else 'away', "sit": s.get('situation'),
                    "st": s.get('shotType'), "la": s.get('lastAction'),
                })

        for side in ['h', 'a']:
            actual_team_id = home_db_id if side == 'h' else away_db_id
            for r in m_json['r'].get(side, {}).values():
                p_id = safe_int(r.get('player_id'))
                p_name = r.get('player')
                
                conn.execute(text("""
                    INSERT INTO rosters (match_id, player_id, player, position, "time", goals, assists, shots, key_passes, "xG", "xA", team_type)
                    VALUES (:m_id, :p_id, :p, :pos, :t, :g, :as, :sh, :kp, :xg, :xa, :team_type)
                    ON CONFLICT (match_id, player_id) DO NOTHING
                """), {
                    "m_id": match_id, "p_id": p_id, "p": p_name, "pos": r.get('position'), "t": safe_int(r.get('time')),
                    "g": safe_int(r.get('goals')), "as": safe_int(r.get('assists')), "sh": safe_int(r.get('shots')),
                    "kp": safe_int(r.get('key_passes')), "xg": safe_float(r.get('xG')), "xa": safe_float(r.get('xA')),
                    "team_type": r.get('h_a')
                })

                if actual_team_id > 0:
                    try:
                        conn.execute(text("""
                            INSERT INTO player (id, name, current_team_id)
                            VALUES (:pid, :name, :tid)
                            ON CONFLICT (id) DO UPDATE SET current_team_id = EXCLUDED.current_team_id, name = EXCLUDED.name
                        """), {"pid": p_id, "name": p_name, "tid": actual_team_id})
                    except Exception:
                        pass 

        conn.execute(text("UPDATE matchcalendar SET is_scraped = TRUE WHERE id = :id"), {"id": match_id})

    logging.info(f"✅ Match {match_id}: shots e rosters salvati.")
    return True

def sync_all_seasons_with_advanced_metrics():
    logging.info("🚀 AVVIO BULK SYNC STORICO VELOCE (2025-2021)")
    page = make_page()

    for season in TARGET_SEASONS:
        logging.info(f"🟢 INIZIO SYNC STAGIONE: {season}")
        for league in TARGET_LEAGUES:
            time.sleep(1)
            league_url = f"https://understat.com/league/{league}/{season}"

            try:
                page.get(league_url)

                if "too many requests" in page.html.lower() or "429 Too Many Requests" in page.html:
                    logging.warning("🚨 BAN RILEVATO. IBERNAZIONE 30 MINUTI.")
                    time.sleep(HIBERNATION_PERIOD)
                    page.get(league_url)

                page.scroll.down(1000)
                time.sleep(1)

                raw_league_json = page.run_js("""
                    if(typeof window.teamsData !== 'undefined' && typeof window.datesData !== 'undefined'){
                        return JSON.stringify({t: window.teamsData, d: window.datesData});
                    } return null;
                """)

                if not raw_league_json:
                    continue

                league_data = json.loads(raw_league_json)
                teams_dict = league_data['t']
                dates_list = league_data['d']

                with engine.begin() as conn:
                    update_standings_safely(conn, teams_dict, league, season)

                match_rounds = build_matchdays_dict(dates_list)
                played_matches = [m for m in dates_list if m.get('isResult') is True]
                matches_to_process = []

                with engine.connect() as conn:
                    for m in played_matches:
                        m_id = int(m['id'])
                        row = conn.execute(text("SELECT is_scraped FROM matchcalendar WHERE id = :id"), {"id": m_id}).fetchone()
                        if not row or not row[0]:
                            matches_to_process.append(m)

                logging.info(f"📊 {league} {season}: {len(matches_to_process)} match mancanti.")
                if not matches_to_process: continue

                with engine.begin() as conn:
                    for m in matches_to_process:
                        m_id = int(m['id'])
                        h_id = str(m['h']['id'])
                        a_id = str(m['a']['id'])
                        
                        h_stats = next((h for h in teams_dict[h_id]['history'] if h['date'] == m['datetime']), {})
                        a_stats = next((h for h in teams_dict[a_id]['history'] if h['date'] == m['datetime']), {})
                        
                        conn.execute(text("""
                            UPDATE matchcalendar SET
                                home_ppda = :h_ppda, away_ppda = :a_ppda,
                                home_deep = :h_deep, away_deep = :a_deep,
                                home_xpts = :h_xpts, away_xpts = :a_xpts,
                                matchday = :md, is_completed = TRUE
                            WHERE id = :id
                        """), {
                            "id": m_id, "md": match_rounds.get(m_id, 0),
                            "h_ppda": get_ppda(h_stats.get('ppda')), "a_ppda": get_ppda(a_stats.get('ppda')),
                            "h_deep": safe_int(h_stats.get('deep')), "a_deep": safe_int(a_stats.get('deep')),
                            "h_xpts": safe_float(h_stats.get('xpts')), "a_xpts": safe_float(a_stats.get('xpts')),
                        })

                for m in matches_to_process:
                    scrape_single_match(page, int(m['id']))

            except Exception as e:
                logging.error(f"❌ Errore su {league} {season}: {e}")

    page.quit()
    logging.info("✅ Bulk sync storico completato. Tutto allineato.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    sync_all_seasons_with_advanced_metrics()