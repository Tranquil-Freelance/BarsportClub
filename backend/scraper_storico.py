import time
import random
import logging
import json
from DrissionPage import ChromiumPage, ChromiumOptions
from sqlalchemy import create_engine, text

# ==========================================
# CONFIGURAZIONE - MULTI STAGIONE (2014-2025)
# ==========================================
DB_URI = "postgresql://postgres:password@localhost:5432/xpalermostat"
engine = create_engine(DB_URI)

TARGET_LEAGUES = ['Serie_A', 'EPL', 'La_liga', 'Bundesliga', 'Ligue_1']

# ✅ ESTESO: Tutte le stagioni disponibili su Understat (2014-2025)
# Ordine: dal più recente al più vecchio (come l'originale)
TARGET_SEASONS = [
    '2025', '2024', '2023', '2022', '2021',  # Già fatti ✅
    '2020', '2019', '2018', '2017', '2016', '2015', '2014'  # Nuovi 🆕
]

# ⚡ DELAY ORIGINALI (che funzionano!) - NON MODIFICARE
JITTER_MIN = 3.0
JITTER_MAX = 7.0
HIBERNATION_PERIOD = 1800

# ⚡ BATCH SIZE ORIGINALE - NON MODIFICARE
BATCH_SIZE = 10


def safe_float(val):
    try:
        return float(val) if val is not None else 0.0
    except Exception:
        return 0.0


def safe_int(val):
    try:
        return int(val) if val is not None else 0
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
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--disable-gpu')
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_user_agent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    )
    return ChromiumPage(co)


def scrape_single_match_fast(page: ChromiumPage, match_id: int) -> bool:
    """
    Versione ottimizzata: scrapa shots e rosters di una singola partita.
    """
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT is_scraped FROM matchcalendar WHERE id = :id"),
            {"id": match_id}
        ).fetchone()
        if row and row[0]:
            return True

    # ⚡ OTTIMIZZAZIONE 3: Jitter ridotto
    time.sleep(random.uniform(JITTER_MIN, JITTER_MAX))
    
    try:
        page.get(f"https://understat.com/match/{match_id}")

        if "too many requests" in page.html.lower() or "429 Too Many Requests" in page.html:
            logging.warning(f"Match {match_id}: Rate limit. Attendo 30 min.")
            time.sleep(HIBERNATION_PERIOD)
            page.get(f"https://understat.com/match/{match_id}")

        # ⚡ OTTIMIZZAZIONE 4: Scroll minimo + sleep ridotto
        page.scroll.down(300)
        time.sleep(1)

        raw_match_json = page.run_js("""
            if(typeof window.shotsData !== 'undefined' && typeof window.rostersData !== 'undefined'){
                return JSON.stringify({s: window.shotsData, r: window.rostersData});
            }
            return null;
        """)

        if not raw_match_json:
            logging.info(f"Match {match_id}: dati non pubblicati.")
            return False

        m_json = json.loads(raw_match_json)
        
        # ⚡ OTTIMIZZAZIONE 5: Ritorna i dati invece di salvarli subito
        return m_json
        
    except Exception as e:
        logging.error(f"❌ Errore scraping match {match_id}: {e}")
        return False


def save_match_data_batch(match_id: int, m_json: dict) -> bool:
    """
    ⚡ OTTIMIZZAZIONE 6: Salva i dati in batch (più efficiente)
    """
    try:
        with engine.begin() as conn:
            # Pulisce i vecchi dati
            conn.execute(text("DELETE FROM shots WHERE match_id = :id"), {"id": match_id})
            conn.execute(text("DELETE FROM rosters WHERE match_id = :id"), {"id": match_id})

            # Shots
            for side in ['h', 'a']:
                for s in m_json['s'].get(side, []):
                    conn.execute(text("""
                        INSERT INTO shots (
                            match_id, player_id, player, minute, "xG", "X", "Y",
                            result, team_type, situation, "shotType", "lastAction", player_assisted
                        )
                        VALUES (
                            :m_id, :p_id, :p, :min, :xg, :x, :y, :res, :side, :sit, :st, :la, :assisted
                        )
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
                        "assisted": s.get('player_assisted')
                    })

            # Rosters
            for side in ['h', 'a']:
                for r in m_json['r'].get(side, {}).values():
                    conn.execute(text("""
                        INSERT INTO rosters (
                            match_id, player_id, player, position, "time",
                            goals, assists, shots, key_passes, "xG", "xA",
                            "xGChain", "xGBuildup", yellow_card, red_card, team_type
                        )
                        VALUES (
                            :m_id, :p_id, :p, :pos, :t, :g, :as, :sh, :kp, :xg, :xa,
                            :xgc, :xgb, :yc, :rc, :team_type
                        )
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
                        "xgc": safe_float(r.get('xGChain')),
                        "xgb": safe_float(r.get('xGBuildup')),
                        "yc": safe_int(r.get('yellow_cards') or r.get('yellow')),
                        "rc": safe_int(r.get('red_cards') or r.get('red')),
                        "team_type": r.get('h_a')
                    })

            # Update flag
            conn.execute(
                text("UPDATE matchcalendar SET is_scraped = TRUE WHERE id = :id"),
                {"id": match_id}
            )
            
        return True
    except Exception as e:
        logging.error(f"❌ Errore salvataggio match {match_id}: {e}")
        return False


def sync_all_seasons_fast():
    """
    ⚡ OTTIMIZZAZIONE 7: Versione ultra-veloce con batch processing
    """
    logging.info("🚀 AVVIO BULK SYNC OTTIMIZZATO (2014-2025)")
    page = make_page()

    total_matches = 0
    processed_matches = 0

    for season in TARGET_SEASONS:
        logging.info(f"🟢 STAGIONE: {season}")
        for league in TARGET_LEAGUES:
            time.sleep(random.uniform(JITTER_MIN, JITTER_MAX))
            league_url = f"https://understat.com/league/{league}/{season}"

            try:
                page.get(league_url)

                if "too many requests" in page.html.lower():
                    logging.warning("🚨 RATE LIMIT! Ibernazione 30 min...")
                    time.sleep(HIBERNATION_PERIOD)
                    page.get(league_url)

                # ⚡ OTTIMIZZAZIONE 8: Scroll minimo
                page.scroll.down(500)
                time.sleep(1)

                raw_league_json = page.run_js("""
                    if(typeof window.teamsData !== 'undefined' && typeof window.datesData !== 'undefined'){
                        return JSON.stringify({t: window.teamsData, d: window.datesData});
                    }
                    return null;
                """)

                if not raw_league_json:
                    logging.warning(f"⚠️ Nessun dato per {league} {season} (stagione non disponibile)")
                    continue

                league_data = json.loads(raw_league_json)
                teams_dict = league_data['t']
                dates_list = league_data['d']

                match_rounds = build_matchdays_dict(dates_list)
                played_matches = [m for m in dates_list if m.get('isResult') is True]
                
                # Filtra solo match non scrapati
                matches_to_process = []
                with engine.connect() as conn:
                    for m in played_matches:
                        m_id = int(m['id'])
                        row = conn.execute(
                            text("SELECT is_scraped FROM matchcalendar WHERE id = :id"),
                            {"id": m_id}
                        ).fetchone()
                        if not row or not row[0]:
                            matches_to_process.append(m)

                if not matches_to_process:
                    logging.info(f"✅ {league} {season}: Completo (0 match mancanti)")
                    continue

                total_matches += len(matches_to_process)
                logging.info(f"📊 {league} {season}: {len(matches_to_process)} match da processare")

                # ⚡ OTTIMIZZAZIONE 9: Aggiorna matchcalendar in batch
                with engine.begin() as conn:
                    for m in matches_to_process:
                        m_id = int(m['id'])
                        m_date = m['datetime']
                        h_id = str(m['h']['id'])
                        a_id = str(m['a']['id'])
                        computed_round = match_rounds.get(m_id, 0)

                        h_stats = next(
                            (h for h in teams_dict.get(h_id, {}).get('history', []) if h['date'] == m_date), {}
                        )
                        a_stats = next(
                            (h for h in teams_dict.get(a_id, {}).get('history', []) if h['date'] == m_date), {}
                        )

                        conn.execute(text("""
                            UPDATE matchcalendar SET
                                home_goals = :h_g, away_goals = :a_g,
                                "home_xG" = :h_xg, "away_xG" = :a_xg,
                                home_ppda = :h_ppda, away_ppda = :a_ppda,
                                home_deep = :h_deep, away_deep = :a_deep,
                                "home_xpts" = :h_xpts, "away_xpts" = :a_xpts,
                                matchday = :md, is_completed = TRUE
                            WHERE id = :id
                        """), {
                            "id": m_id,
                            "md": computed_round,
                            "h_g": safe_int(m.get('goals', {}).get('h')),
                            "a_g": safe_int(m.get('goals', {}).get('a')),
                            "h_xg": safe_float(m.get('xG', {}).get('h')),
                            "a_xg": safe_float(m.get('xG', {}).get('a')),
                            "h_ppda": get_ppda(h_stats.get('ppda')),
                            "a_ppda": get_ppda(a_stats.get('ppda')),
                            "h_deep": safe_int(h_stats.get('deep')),
                            "a_deep": safe_int(a_stats.get('deep')),
                            "h_xpts": safe_float(h_stats.get('xpts')),
                            "a_xpts": safe_float(a_stats.get('xpts')),
                        })

                # ⚡ OTTIMIZZAZIONE 10: Scrapa e salva in batch
                batch_data = []
                for idx, m in enumerate(matches_to_process, 1):
                    m_id = int(m['id'])
                    
                    logging.info(f"🔄 [{processed_matches + idx}/{total_matches}] Match {m_id}...")
                    
                    m_json = scrape_single_match_fast(page, m_id)
                    if m_json:
                        batch_data.append((m_id, m_json))
                    
                    # Salva ogni BATCH_SIZE match
                    if len(batch_data) >= BATCH_SIZE:
                        for batch_id, batch_json in batch_data:
                            if save_match_data_batch(batch_id, batch_json):
                                processed_matches += 1
                        batch_data = []
                        logging.info(f"💾 Batch salvato ({BATCH_SIZE} match)")
                    
                    # Progresso
                    if idx % 10 == 0:
                        logging.info(f"📈 Progresso: {idx}/{len(matches_to_process)}")

                # Salva gli ultimi match rimasti
                if batch_data:
                    for batch_id, batch_json in batch_data:
                        if save_match_data_batch(batch_id, batch_json):
                            processed_matches += 1
                    logging.info(f"💾 Ultimo batch salvato ({len(batch_data)} match)")

            except Exception as e:
                logging.error(f"❌ Errore su {league} {season}: {e}", exc_info=True)

    page.quit()
    logging.info(f"✅ SYNC COMPLETATO! Processati {processed_matches}/{total_matches} match")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
    sync_all_seasons_fast()