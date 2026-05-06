"""
Data Integrity Audit - xPalermoStat Database
=============================================
Verifica 4 punti critici su matchcalendar, rosters, shots.

Esecuzione: python backend/data_integrity_audit.py
Richiede: asyncpg, connessione a PostgreSQL (xpalermostat)
"""

import asyncio
import asyncpg
from datetime import datetime

DB_DSN = "postgres://postgres:password@localhost:5432/xpalermostat"


def fmt(val):
    """Format a value for clean display."""
    if val is None:
        return "NULL"
    if isinstance(val, float):
        return f"{val:.4f}"
    return str(val)


def dt_or_na(val):
    """Format a datetime or return 'N/A'."""
    if val is None:
        return "N/A"
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M")
    return str(val)


def section(title: str):
    line = "=" * 72
    print(f"\n{line}")
    print(f"  {title}")
    print(line)


def subsection(title: str):
    print(f"\n  --- {title} ---")


async def check_ghost_matches(conn):
    """
    1) PARTITE FANTASMA
    Due sotto-controlli:
      a) NULL values: is_completed=true ma goals/xG sono NULL (dati mancanti)
      b) All-zero: is_completed=true, is_scraped=true E TUTTI e 4 i campi sono 0 (sospetto)
    """
    section("CHECK 1 - PARTITE FANTASMA")

    # --- 1a: NULL values in completed matches ---
    subsection("1a - Completed match con goals/xG a NULL (dati mancanti)")
    rows_null = await conn.fetch("""
        SELECT
            id,
            match_datetime,
            home_goals,
            away_goals,
            "home_xG",
            "away_xG",
            is_completed,
            is_scraped
        FROM matchcalendar
        WHERE is_completed = true
          AND (home_goals IS NULL OR away_goals IS NULL
            OR "home_xG"  IS NULL OR "away_xG"  IS NULL)
        ORDER BY match_datetime NULLS LAST, id
    """)

    if not rows_null:
        print("  [OK] Nessun NULL value sospetto in partite completate.\n")
    else:
        print(f"  [ERR] {len(rows_null)} partite completate con valori NULL:\n")
        hdr = f"  {'ID':>8}  {'Data':<18}  {'home_g':>7}  {'away_g':>7}  {'home_xG':>8}  {'away_xG':>8}  {'scraped':>7}"
        sep = f"  {'--':>8}  {'----':<18}  {'------':>7}  {'------':>7}  {'-------':>8}  {'-------':>8}  {'-------':>7}"
        print(hdr)
        print(sep)
        for r in rows_null:
            print(f"  {r['id']:>8}  {dt_or_na(r['match_datetime']):<18}  {fmt(r['home_goals']):>7}  {fmt(r['away_goals']):>7}  {fmt(r['home_xG']):>8}  {fmt(r['away_xG']):>8}  {str(r['is_scraped']):>7}")
        print()

    # --- 1b: All fields exactly zero in scraped matches ---
    subsection("1b - Scraped match con goals=0 E xG=0.0 (anomalia)")
    rows_zero = await conn.fetch("""
        SELECT
            id,
            match_datetime,
            home_goals,
            away_goals,
            "home_xG",
            "away_xG",
            is_completed,
            is_scraped
        FROM matchcalendar
        WHERE is_completed = true
          AND is_scraped = true
          AND home_goals = 0
          AND away_goals = 0
          AND "home_xG" = 0.0
          AND "away_xG" = 0.0
        ORDER BY match_datetime NULLS LAST, id
    """)

    if not rows_zero:
        print("  [OK] Nessun match scrapato con TUTTI i campi a zero.\n")
    else:
        print(f"  [ERR] {len(rows_zero)} match scrapati con goals=0 e xG=0.0 (veri fantasmi?):\n")
        hdr = f"  {'ID':>8}  {'Data':<18}  {'home_g':>7}  {'away_g':>7}  {'home_xG':>8}  {'away_xG':>8}"
        sep = f"  {'--':>8}  {'----':<18}  {'------':>7}  {'------':>7}  {'-------':>8}  {'-------':>8}"
        print(hdr)
        print(sep)
        for r in rows_zero:
            print(f"  {r['id']:>8}  {dt_or_na(r['match_datetime']):<18}  {fmt(r['home_goals']):>7}  {fmt(r['away_goals']):>7}  {fmt(r['home_xG']):>8}  {fmt(r['away_xG']):>8}")
        print()

    return {'nulls': rows_null, 'all_zeros': rows_zero}


async def check_goal_inconsistency(conn):
    """
    2) INCONGRUENZA RETI
    Confronta home_goals/away_goals (matchcalendar) con COUNT(shots WHERE result='Goal').
    Solo per match con is_scraped=true (shots dovrebbero essere presenti).
    Se is_scraped=false, la differenza e' attesa perche' i tiri non sono stati ancora importati.
    """
    section("CHECK 2 - INCONGRUENZA RETI")
    print("Criterio: solo match con is_scraped=true (shots presenti)\n")

    rows = await conn.fetch("""
        SELECT
            m.id,
            m.match_datetime,
            m.home_goals,
            m.away_goals,
            COALESCE(hg.cnt, 0) AS actual_home_goals,
            COALESCE(ag.cnt, 0) AS actual_away_goals
        FROM matchcalendar m
        LEFT JOIN (
            SELECT match_id, COUNT(*) AS cnt
            FROM shots
            WHERE result = 'Goal' AND team_type = 'home'
            GROUP BY match_id
        ) hg ON hg.match_id = m.id
        LEFT JOIN (
            SELECT match_id, COUNT(*) AS cnt
            FROM shots
            WHERE result = 'Goal' AND team_type = 'away'
            GROUP BY match_id
        ) ag ON ag.match_id = m.id
        WHERE m.is_completed = true
          AND m.is_scraped = true
          AND (
               m.home_goals IS DISTINCT FROM COALESCE(hg.cnt, 0)
            OR m.away_goals IS DISTINCT FROM COALESCE(ag.cnt, 0)
          )
        ORDER BY m.match_datetime NULLS LAST, m.id
    """)

    if not rows:
        print("  [OK] TUTTE LE PARTITE (scrapate) hanno goals e shot-count coincidenti.\n")
        return []

    print(f"  [ERR] TROVATE {len(rows)} PARTITE (scrapate) CON GOAL DISCREPANTI:\n")
    hdr = f"  {'ID':>8}  {'Data':<18}  {'m.home_g':>8}  {'shots_h':>8}  {'m.away_g':>8}  {'shots_a':>8}  {'Diff_H':>7}  {'Diff_A':>7}"
    sep = f"  {'--':>8}  {'----':<18}  {'--------':>8}  {'-------':>8}  {'--------':>8}  {'-------':>8}  {'------':>7}  {'------':>7}"
    print(hdr)
    print(sep)
    for r in rows:
        dh = r['home_goals'] - r['actual_home_goals']
        da = r['away_goals'] - r['actual_away_goals']
        print(f"  {r['id']:>8}  {dt_or_na(r['match_datetime']):<18}  {r['home_goals']:>8}  {r['actual_home_goals']:>8}  {r['away_goals']:>8}  {r['actual_away_goals']:>8}  {dh:+d}  {da:+d}")
    print()
    return rows


async def check_shadow_players(conn):
    """
    3) GIOCATORI 'OMBRA'
    rosters: time>0 MA tutte le statistiche offensive a zero.
    Criterio piu' stretto: time>0, shots=0, key_passes=0, xG=0.0, xA=0.0, goals=0, assists=0.
    Inoltre, filtra per minimum time (es. >= 30 min) per evitare subentri brevi senza azione.
    """
    section("CHECK 3 - GIOCATORI 'OMBRA'")
    print("Criterio: time>=30min, shots=0, key_passes=0, xG=0.0, xA=0.0, goals=0, assists=0\n")

    # Main query: time >= 30 min, all stats zero
    rows = await conn.fetch("""
        SELECT
            r.match_id,
            r.player_id,
            r.player,
            r.position,
            r.team_type,
            r.time,
            r.shots,
            r.key_passes,
            r."xG",
            r."xA",
            r.goals,
            r.assists
        FROM rosters r
        WHERE r.time >= 30
          AND (r.shots = 0 OR r.shots IS NULL)
          AND (r.key_passes = 0 OR r.key_passes IS NULL)
          AND (r."xG" = 0.0 OR r."xG" IS NULL)
          AND (r."xA" = 0.0 OR r."xA" IS NULL)
          AND (r.goals = 0 OR r.goals IS NULL)
          AND (r.assists = 0 OR r.assists IS NULL)
        ORDER BY r.time DESC, r.player
    """)

    # Breakdown by position (for context)
    pos_breakdown = await conn.fetch("""
        SELECT
            r.position,
            COUNT(*) AS cnt
        FROM rosters r
        WHERE r.time >= 30
          AND (r.shots = 0 OR r.shots IS NULL)
          AND (r.key_passes = 0 OR r.key_passes IS NULL)
          AND (r."xG" = 0.0 OR r."xG" IS NULL)
          AND (r."xA" = 0.0 OR r."xA" IS NULL)
          AND (r.goals = 0 OR r.goals IS NULL)
          AND (r.assists = 0 OR r.assists IS NULL)
        GROUP BY r.position
        ORDER BY COUNT(*) DESC
    """)

    if not rows:
        print("  [OK] NESSUN GIOCATORE OMBRA rilevato (con >=30min).\n")
        return []

    print(f"  [ERR] TROVATI {len(rows)} GIOCATORI OMBRA (>=30min, tutte le stats a 0):\n")

    # Position breakdown
    print("  Breakdown per posizione:")
    hdr2 = f"  {'Posizione':<20}  {'Conteggio':>10}"
    sep2 = f"  {'--------':<20}  {'--------':>10}"
    print(hdr2)
    print(sep2)
    for p in pos_breakdown:
        pos_label = p['position'] if p['position'] else 'NULL'
        print(f"  {pos_label:<20}  {p['cnt']:>10}")
    print()

    # Sample rows (first 50)
    print(f"  Campione (prime 50 righe):\n")
    hdr = f"  {'MatchID':>8}  {'PlayerID':>9}  {'Player':<24}  {'Pos':<6}  {'Side':>4}  {'Min':>5}  {'Shots':>5}  {'KP':>4}  {'xG':>8}  {'xA':>8}  {'G':>3}  {'A':>3}"
    sep = f"  {'------':>8}  {'--------':>9}  {'------':<24}  {'---':<6}  {'----':>4}  {'---':>5}  {'-----':>5}  {'--':>4}  {'--':>8}  {'--':>8}  {'-':>3}  {'-':>3}"
    print(hdr)
    print(sep)
    for r in rows[:50]:
        print(f"  {r['match_id']:>8}  {r['player_id']:>9}  {r['player']:<24}  {str(r['position'] or ''):<6}  {str(r['team_type'] or ''):>4}  {r['time']:>5}  {r['shots'] or 0:>5}  {r['key_passes'] or 0:>4}  {fmt(r['xG']):>8}  {fmt(r['xA']):>8}  {r['goals']:>3}  {r['assists']:>3}")
    if len(rows) > 50:
        print(f"  ... e {len(rows) - 50} altri.")
    print()
    return rows


async def check_orphans(conn):
    """
    4) ORFANI E MISSING
    """
    section("CHECK 4 - ORFANI E MISSING")

    # --- 4a: rosters orfani ---
    subsection("4a - Rosters con match_id inesistente")
    rows_r = await conn.fetch("""
        SELECT r.match_id, COUNT(*) AS righe, COUNT(DISTINCT r.player) AS giocatori_distinti
        FROM rosters r
        LEFT JOIN matchcalendar m ON r.match_id = m.id
        WHERE m.id IS NULL
        GROUP BY r.match_id
        ORDER BY r.match_id
    """)
    if rows_r:
        print(f"\n  [ERR] TROVATI {len(rows_r)} match_id ORFANI in rosters:\n")
        for rr in rows_r:
            print(f"     match_id={rr['match_id']}  ->  {rr['righe']} righe, {rr['giocatori_distinti']} giocatori")
    else:
        print("\n  [OK] Nessun orfano in rosters.")

    # --- 4b: shots orfani ---
    subsection("4b - Shots con match_id inesistente")
    rows_s = await conn.fetch("""
        SELECT s.match_id, COUNT(*) AS righe, COUNT(DISTINCT s.player) AS giocatori_distinti
        FROM shots s
        LEFT JOIN matchcalendar m ON s.match_id = m.id
        WHERE m.id IS NULL
        GROUP BY s.match_id
        ORDER BY s.match_id
    """)
    if rows_s:
        print(f"\n  [ERR] TROVATI {len(rows_s)} match_id ORFANI in shots:\n")
        for rs in rows_s:
            print(f"     match_id={rs['match_id']}  ->  {rs['righe']} righe, {rs['giocatori_distinti']} giocatori")
    else:
        print("\n  [OK] Nessun orfano in shots.")

    # --- 4c: matchcalendar senza rosters ---
    subsection("4c - Match in matchcalendar SENZA righe in rosters")
    rows_m_no_r = await conn.fetch("""
        SELECT m.id, m.match_datetime, m.is_completed, m.is_scraped
        FROM matchcalendar m
        LEFT JOIN rosters r ON r.match_id = m.id
        WHERE r.match_id IS NULL
        ORDER BY m.match_datetime NULLS LAST, m.id
    """)
    if rows_m_no_r:
        print(f"\n  [ERR] TROVATI {len(rows_m_no_r)} match SENZA rosters:\n")
        hdr = f"  {'ID':>8}  {'Data':<18}  {'Completato':>10}  {'Scraped':>8}"
        sep = f"  {'--':>8}  {'----':<18}  {'----------':>10}  {'-------':>8}"
        print(hdr)
        print(sep)
        for r in rows_m_no_r:
            print(f"  {r['id']:>8}  {dt_or_na(r['match_datetime']):<18}  {str(r['is_completed']):>10}  {str(r['is_scraped']):>8}")
    else:
        print("\n  [OK] Tutti i match hanno righe in rosters.")

    # --- 4d: matchcalendar senza shots ---
    subsection("4d - Match in matchcalendar SENZA righe in shots")
    rows_m_no_s = await conn.fetch("""
        SELECT m.id, m.match_datetime, m.is_completed, m.is_scraped
        FROM matchcalendar m
        LEFT JOIN shots s ON s.match_id = m.id
        WHERE s.match_id IS NULL
        ORDER BY m.match_datetime NULLS LAST, m.id
    """)
    if rows_m_no_s:
        print(f"\n  [ERR] TROVATI {len(rows_m_no_s)} match SENZA shots:\n")
        hdr = f"  {'ID':>8}  {'Data':<18}  {'Completato':>10}  {'Scraped':>8}"
        sep = f"  {'--':>8}  {'----':<18}  {'----------':>10}  {'-------':>8}"
        print(hdr)
        print(sep)
        for r in rows_m_no_s:
            print(f"  {r['id']:>8}  {dt_or_na(r['match_datetime']):<18}  {str(r['is_completed']):>10}  {str(r['is_scraped']):>8}")
    else:
        print("\n  [OK] Tutti i match hanno righe in shots.")

    print()
    return rows_r, rows_s, rows_m_no_r, rows_m_no_s


async def check_player_stats_table(conn):
    """Check aggiuntivo: tabella player_stats."""
    section("CHECK BONUS - Tabella player_stats")
    exists = await conn.fetchval("""
        SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'player_stats')
    """)
    if not exists:
        print("  [WARN] Tabella `player_stats` non esiste nel database.\n")
        return

    cnt = await conn.fetchval("SELECT COUNT(*) FROM player_stats")
    print(f"  Tabella `player_stats` esiste con {cnt} righe.")

    orphans = await conn.fetch("""
        SELECT ps.match_id, COUNT(*) AS righe
        FROM player_stats ps
        LEFT JOIN matchcalendar m ON ps.match_id = m.id
        WHERE m.id IS NULL
        GROUP BY ps.match_id
        ORDER BY ps.match_id
    """)
    if orphans:
        print(f"  [ERR] TROVATI {len(orphans)} match_id ORFANI in player_stats:")
        for o in orphans:
            print(f"     match_id={o['match_id']} -> {o['righe']} righe")
    else:
        print("  [OK] Nessun orfano in player_stats.")
    print()


async def summary(conn):
    section("SOMMARIO DATABASE")
    mc = await conn.fetchval("SELECT COUNT(*) FROM matchcalendar")
    mc_completed = await conn.fetchval("SELECT COUNT(*) FROM matchcalendar WHERE is_completed = true")
    mc_scraped = await conn.fetchval("SELECT COUNT(*) FROM matchcalendar WHERE is_scraped = true")
    rosters_cnt = await conn.fetchval("SELECT COUNT(*) FROM rosters")
    shots_cnt = await conn.fetchval("SELECT COUNT(*) FROM shots")
    matches_with_rosters = await conn.fetchval("SELECT COUNT(DISTINCT match_id) FROM rosters")
    matches_with_shots = await conn.fetchval("SELECT COUNT(DISTINCT match_id) FROM shots")

    print(f"  matchcalendar : {mc} totali  ({mc_completed} completati, {mc_scraped} scrapati)")
    print(f"  rosters      : {rosters_cnt} righe  ({matches_with_rosters} match coperti)")
    print(f"  shots        : {shots_cnt} tiri    ({matches_with_shots} match coperti)")
    print()

    # Additional stats for context
    subsection("Dettaglio matchcalendar per stato")
    stats = await conn.fetch("""
        SELECT
            is_completed,
            is_scraped,
            COUNT(*) AS cnt
        FROM matchcalendar
        GROUP BY is_completed, is_scraped
        ORDER BY is_completed, is_scraped
    """)
    hdr = f"  {'Completato':>10}  {'Scraped':>8}  {'Conteggio':>10}"
    sep = f"  {'----------':>10}  {'-------':>8}  {'--------':>10}"
    print(hdr)
    print(sep)
    for s in stats:
        print(f"  {str(s['is_completed']):>10}  {str(s['is_scraped']):>8}  {s['cnt']:>10}")
    print()


async def main():
    print("\n" + "#" * 72)
    print("#  DATA INTEGRITY AUDIT - xPalermoStat")
    print(f"#  Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("#" * 72)

    conn = await asyncpg.connect(DB_DSN)
    try:
        await summary(conn)
        results = {}
        results['ghost_matches']   = await check_ghost_matches(conn)
        results['goal_mismatches'] = await check_goal_inconsistency(conn)
        results['shadow_players']  = await check_shadow_players(conn)
        results['orphans']         = await check_orphans(conn)
        await check_player_stats_table(conn)

        # === REPORT FINALE ===
        section("CONCLUSIONI")

        gm = results['ghost_matches']
        totals = {
            'Fantasma - NULL values (completed)':     len(gm['nulls']),
            'Fantasma - All-zero (scraped)':          len(gm['all_zeros']),
            'Goal discrepanti (scraped only)':        len(results['goal_mismatches']),
            'Giocatori ombra (>=30min, all zero)':    len(results['shadow_players']),
        }
        r_or = results['orphans']
        totals['Orfani rosters (match_id)'] = len(r_or[0]) if r_or[0] else 0
        totals['Orfani shots (match_id)']   = len(r_or[1]) if r_or[1] else 0
        totals['Match senza rosters']       = len(r_or[2]) if r_or[2] else 0
        totals['Match senza shots']         = len(r_or[3]) if r_or[3] else 0

        any_issue = any(v > 0 for v in totals.values())

        print(f"\n  {'Controllo':<40}  {'Esito':>10}")
        print(f"  {'--------':<40}  {'-----':>10}")
        for label, count in totals.items():
            status = f"[ERR] {count}" if count > 0 else "[OK]"
            print(f"  {label:<40}  {status:>10}")

        print()
        print(f"  NOTE:")
        print(f"  - 'Fantasma - NULL values': partite completate ma con goals/xG = NULL (dati mancanti)")
        print(f"  - 'Fantasma - All-zero': partite scrapate ma con goals=0 e xG=0.0 (molto sospetto)")
        print(f"  - 'Goal discrepanti': solo partite scrapate (is_scraped=true)")
        print(f"  - 'Giocatori ombra': solo con time>=30min per escludere subentri brevi")

        if any_issue:
            print(f"\n  [WARN] TROVATI PROBLEMI DI INTEGRITA' - consultare i dettagli sopra.\n")
        else:
            print(f"\n  [OK] DATABASE PULITO - nessuna anomalia rilevata.\n")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
