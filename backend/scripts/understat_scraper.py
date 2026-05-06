"""
Understat Data Ingestion Engine — Phase 10
============================================
DrissionPage-based scraper that extracts matchcalendar, shots, and rosters
from Understat for all five major European leagues across multiple seasons.

Architecture
------------
- Runs as a standalone script (spawned as subprocess by the APScheduler).
- Imports the database URI dynamically from ``app.core.config`` (synchronous
  psycopg2 driver derived from the async config).
- Uses DrissionPage (Chromium) to execute JavaScript and read the
  ``window.teamsData``, ``window.datesData``, ``window.shotsData``, and
  ``window.rostersData`` variables injected by Understat.
- Implements request Jitter (10–20 s random sleep) and 30-minute Hibernation
  on 429 / "too many requests" detection.
- **matchcalendar** rows are UPSERTed (UPDATE + insert-if-missing).
- **shots** and **rosters** rows are INSERTed with ``ON CONFLICT DO NOTHING``.

Usage
-----
    python backend/scripts/understat_scraper.py

Environment
-----------
Relies on the same ``.env`` file (PostgreSQL credentials) that the FastAPI
application uses.  The script adds the parent directory (``backend/``) to
``sys.path`` so that ``from app.core.config import settings`` resolves
correctly when spawned from the APScheduler.
"""

from __future__ import annotations

import json
import logging
import os
import random
import sys
import time

from DrissionPage import ChromiumPage, ChromiumOptions
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Path bootstrap — allow ``from app.core.config import settings`` when this
# script is run as ``python scripts/understat_scraper.py`` from the backend/
# directory (which is the ``cwd`` set by the APScheduler subprocess).
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE)  # → backend/
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from app.core.config import settings

# ---------------------------------------------------------------------------
# Database connection  (synchronous psycopg2 driver)
# ---------------------------------------------------------------------------
# The settings object exposes an async URI (postgresql+asyncpg://).  We
# derive the synchronous equivalent by replacing the driver suffix.
_ASYNC_URI: str = settings.SQLALCHEMY_DATABASE_URI
_SYNC_URI: str = _ASYNC_URI.replace("+asyncpg", "+psycopg2")

engine = create_engine(_SYNC_URI, pool_pre_ping=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TARGET_LEAGUES = ["Serie_A", "EPL", "La_liga", "Bundesliga", "Ligue_1"]
TARGET_SEASONS = ["2025", "2024", "2023", "2022", "2021"]

JITTER_MIN = 10.0
JITTER_MAX = 20.0
HIBERNATION_PERIOD = 1800  # 30 minutes

logger = logging.getLogger("understat_scraper")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def safe_float(val: object) -> float:
    try:
        return float(val)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


def safe_int(val: object) -> int:
    try:
        return int(val)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def get_ppda(p: dict | None) -> float:
    """PPDA = passes allowed per defensive action."""
    if not p:
        return 0.0
    att = safe_float(p.get("att"))
    dfn = safe_float(p.get("def"))
    return att / dfn if dfn > 0 else 0.0


def build_matchdays_dict(dates_list: list[dict]) -> dict[int, int]:
    """Derive matchday (round) numbers from chronological match ordering."""
    sorted_matches = sorted(dates_list, key=lambda x: x.get("datetime", ""))
    team_games: dict[str, int] = {}
    match_rounds: dict[int, int] = {}
    for m in sorted_matches:
        if not m.get("datetime"):
            continue
        h_id = str(m["h"]["id"])
        a_id = str(m["a"]["id"])
        team_games[h_id] = team_games.get(h_id, 0) + 1
        team_games[a_id] = team_games.get(a_id, 0) + 1
        round_num = max(team_games[h_id], team_games[a_id])
        match_rounds[int(m["id"])] = round_num
    return match_rounds


def make_page() -> ChromiumPage:
    """Create a headless ChromiumPage suitable for VPS / server environments."""
    co = ChromiumOptions()
    co.headless(True)
    co.auto_port()  # avoid WebSocket crash on Windows
    co.set_argument("--no-sandbox")
    co.set_argument("--disable-dev-shm-usage")
    co.set_argument("--disable-gpu")
    co.set_user_agent(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
    return ChromiumPage(co)


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def scrape_single_match(page: ChromiumPage, match_id: int) -> bool:
    """
    Scrape shots + rosters for a single Understat match.

    Returns ``True`` when data was successfully saved (or was already
    present), ``False`` when Understat has not yet published the data.
    """
    # ── Skip if already scraped ────────────────────────────────────────
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT is_scraped FROM matchcalendar WHERE id = :id"),
            {"id": match_id},
        ).fetchone()
        if row and row[0]:
            logger.info("Match %d: already scraped, skipping.", match_id)
            return True

    # ── Jitter before request ──────────────────────────────────────────
    time.sleep(random.uniform(JITTER_MIN, JITTER_MAX))

    page.get(f"https://understat.com/match/{match_id}")

    # ── Hibernation on rate-limit detection ────────────────────────────
    if "too many requests" in page.html.lower() or "429" in page.html:
        logger.warning("Match %d: 429 detected. Hibernating 30 min.", match_id)
        time.sleep(HIBERNATION_PERIOD)
        page.get(f"https://understat.com/match/{match_id}")

    page.scroll.down(500)
    time.sleep(2)

    raw = page.run_js(
        """
        if (typeof window.shotsData !== 'undefined'
            && typeof window.rostersData !== 'undefined') {
            return JSON.stringify({s: window.shotsData, r: window.rostersData});
        }
        return null;
        """
    )

    if not raw:
        logger.info("Match %d: data not yet published on Understat.", match_id)
        return False

    m_json = json.loads(raw)

    with engine.begin() as conn:
        # Purge stale data before inserting fresh values
        conn.execute(text("DELETE FROM shots WHERE match_id = :id"), {"id": match_id})
        conn.execute(
            text("DELETE FROM rosters WHERE match_id = :id"), {"id": match_id}
        )

        # ── Shots ──────────────────────────────────────────────────────
        for side in ("h", "a"):
            for s in m_json["s"].get(side, []):
                conn.execute(
                    text(
                        """
                        INSERT INTO shots (
                            match_id, player_id, player, minute,
                            "xG", "X", "Y", result, team_type,
                            situation, "shotType", "lastAction", player_assisted
                        ) VALUES (
                            :m_id, :p_id, :p, :min,
                            :xg, :x, :y, :res, :side,
                            :sit, :st, :la, :pa
                        )
                        ON CONFLICT (match_id, player, minute) DO NOTHING
                        """
                    ),
                    {
                        "m_id": match_id,
                        "p_id": safe_int(s.get("player_id")),
                        "p": s.get("player"),
                        "min": safe_int(s.get("minute")),
                        "xg": safe_float(s.get("xG")),
                        "x": safe_float(s.get("X")),
                        "y": safe_float(s.get("Y")),
                        "res": s.get("result"),
                        "side": "home" if side == "h" else "away",
                        "sit": s.get("situation"),
                        "st": s.get("shotType"),
                        "la": s.get("lastAction"),
                        "pa": s.get("player_assisted"),
                    },
                )

        # ── Rosters ────────────────────────────────────────────────────
        for side in ("h", "a"):
            for r in m_json["r"].get(side, {}).values():
                conn.execute(
                    text(
                        """
                        INSERT INTO rosters (
                            match_id, player_id, player, position, "time",
                            goals, assists, shots, key_passes,
                            "xG", "xA", team_type,
                            "xGChain", "xGBuildup",
                            yellow_card, red_card
                        ) VALUES (
                            :m_id, :p_id, :p, :pos, :t,
                            :g, :as, :sh, :kp,
                            :xg, :xa, :team_type,
                            :xgc, :xgb,
                            :yc, :rc
                        )
                        ON CONFLICT (match_id, player_id) DO NOTHING
                        """
                    ),
                    {
                        "m_id": match_id,
                        "p_id": safe_int(r.get("player_id")),
                        "p": r.get("player"),
                        "pos": r.get("position"),
                        "t": safe_int(r.get("time")),
                        "g": safe_int(r.get("goals")),
                        "as": safe_int(r.get("assists")),
                        "sh": safe_int(r.get("shots")),
                        "kp": safe_int(r.get("key_passes")),
                        "xg": safe_float(r.get("xG")),
                        "xa": safe_float(r.get("xA")),
                        "team_type": r.get("h_a"),
                        "xgc": safe_float(r.get("xGChain")),
                        "xgb": safe_float(r.get("xGBuildup")),
                        "yc": safe_int(
                            r.get("yellow_card") or r.get("yellow_cards")
                        ),
                        "rc": safe_int(
                            r.get("red_card") or r.get("red_cards")
                        ),
                    },
                )

        # ── Mark match as scraped ──────────────────────────────────────
        result = conn.execute(
            text("UPDATE matchcalendar SET is_scraped = TRUE WHERE id = :id"),
            {"id": match_id},
        )
        if result.rowcount == 0:
            logger.warning(
                "Match %d: is_scraped not updated — row missing in matchcalendar.",
                match_id,
            )

    logger.info("Match %d: shots + rosters saved.", match_id)
    return True


def sync_all_seasons() -> None:
    """
    Full synchronisation loop across all target leagues and seasons.

    Phase 1 — For each league/season:
        1. Load the calendar page and extract ``teamsData`` + ``datesData``.
        2. UPSERT every played match into ``matchcalendar``.
        3. Collect match IDs whose data is missing or stale.

    Phase 2 — For each collected match:
        1. Call ``scrape_single_match`` (shots + rosters).
    """
    logger.info("Understat ingestion: STARTED — %d leagues × %d seasons.",
                 len(TARGET_LEAGUES), len(TARGET_SEASONS))

    page = make_page()

    try:
        for season in TARGET_SEASONS:
            logger.info("Season %s — beginning.", season)

            for league in TARGET_LEAGUES:
                time.sleep(random.uniform(JITTER_MIN, JITTER_MAX))

                league_url = f"https://understat.com/league/{league}/{season}"

                try:
                    page.get(league_url)

                    # ── Hibernation on 429 ─────────────────────────────
                    if "too many requests" in page.html.lower() or "429" in page.html:
                        logger.warning(
                            "429 on %s/%s. Hibernating 30 min.", league, season
                        )
                        time.sleep(HIBERNATION_PERIOD)
                        page.get(league_url)

                    page.scroll.down(1000)
                    time.sleep(2)

                    raw = page.run_js(
                        """
                        if (typeof window.teamsData !== 'undefined'
                            && typeof window.datesData !== 'undefined') {
                            return JSON.stringify({
                                t: window.teamsData,
                                d: window.datesData
                            });
                        }
                        return null;
                        """
                    )

                    if not raw:
                        logger.warning(
                            "No teamsData/datesData for %s %s. Skipping.",
                            league, season,
                        )
                        continue

                    league_data = json.loads(raw)
                    teams_dict: dict = league_data["t"]
                    dates_list: list[dict] = league_data["d"]

                    match_rounds = build_matchdays_dict(dates_list)
                    played_matches = [
                        m for m in dates_list if m.get("isResult") is True
                    ]

                    # ── Identify which matches need processing ─────────
                    matches_to_process: list[dict] = []
                    with engine.connect() as conn:
                        for m in played_matches:
                            m_id = int(m["id"])
                            row = conn.execute(
                                text(
                                    "SELECT is_scraped, home_goals "
                                    "FROM matchcalendar WHERE id = :id"
                                ),
                                {"id": m_id},
                            ).fetchone()
                            if not row or not row[0] or row[1] is None:
                                matches_to_process.append(m)

                    logger.info(
                        "%s %s: %d match(es) need processing.",
                        league, season, len(matches_to_process),
                    )

                    if not matches_to_process:
                        continue

                    # ── UPSERT matchcalendar rows ──────────────────────
                    with engine.begin() as conn:
                        for m in matches_to_process:
                            m_id = int(m["id"])
                            m_date = m["datetime"]
                            h_id = str(m["h"]["id"])
                            a_id = str(m["a"]["id"])

                            h_g = safe_int(m.get("goals", {}).get("h"))
                            a_g = safe_int(m.get("goals", {}).get("a"))
                            h_xg = safe_float(m.get("xG", {}).get("h"))
                            a_xg = safe_float(m.get("xG", {}).get("a"))

                            computed_round = match_rounds.get(m_id, 0)

                            h_stats = next(
                                (
                                    h
                                    for h in teams_dict.get(h_id, {}).get(
                                        "history", []
                                    )
                                    if h["date"] == m_date
                                ),
                                {},
                            )
                            a_stats = next(
                                (
                                    h
                                    for h in teams_dict.get(a_id, {}).get(
                                        "history", []
                                    )
                                    if h["date"] == m_date
                                ),
                                {},
                            )

                            conn.execute(
                                text(
                                    """
                                    UPDATE matchcalendar SET
                                        match_datetime = :m_date,
                                        home_goals = :h_g,
                                        away_goals = :a_g,
                                        "home_xG" = :h_xg,
                                        "away_xG" = :a_xg,
                                        home_ppda = :h_ppda,
                                        away_ppda = :a_ppda,
                                        home_deep = :h_deep,
                                        away_deep = :a_deep,
                                        home_xpts = :h_xpts,
                                        away_xpts = :a_xpts,
                                        matchday = :md,
                                        is_completed = TRUE
                                    WHERE id = :id
                                    """
                                ),
                                {
                                    "id": m_id,
                                    "m_date": m_date,
                                    "h_g": h_g,
                                    "a_g": a_g,
                                    "h_xg": h_xg,
                                    "a_xg": a_xg,
                                    "md": computed_round,
                                    "h_ppda": get_ppda(h_stats.get("ppda")),
                                    "a_ppda": get_ppda(a_stats.get("ppda")),
                                    "h_deep": safe_int(h_stats.get("deep")),
                                    "a_deep": safe_int(a_stats.get("deep")),
                                    "h_xpts": safe_float(
                                        h_stats.get("xpts")
                                    ),
                                    "a_xpts": safe_float(
                                        a_stats.get("xpts")
                                    ),
                                },
                            )

                    # ── Scrape shots + rosters for each match ──────────
                    for m in matches_to_process:
                        m_id = int(m["id"])
                        scrape_single_match(page, m_id)

                except Exception:
                    logger.exception(
                        "Critical error on %s %s.", league, season
                    )

    finally:
        page.quit()

    logger.info("Understat ingestion: COMPLETE.")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    sync_all_seasons()
