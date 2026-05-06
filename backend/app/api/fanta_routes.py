"""
Fanta Draft Engine — Visual Analytics Edition
Endpoints:
  /players        — data table + scatter data, con filtro temporale
  /player/{id}    — profilo completo: stats p90, percentili, shots, trend, radar
  /search         — autocomplete giocatori
  /dashboard      — 4 widget legacy (backward compat)
  /auction-strategy
"""

import math
import logging
from typing import List, Dict, Any, Optional, Tuple
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from app.db.database import engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/fanta", tags=["Fanta Draft Engine"])

# ─── Constants ─────────────────────────────────────────────────────────────

MIN_MINUTES = 200
MIN_MINUTES_LAST5 = 135

FANTASY_PTS_GOAL = 5.0
FANTASY_PTS_ASSIST = 3.0

# ─── Position normalization ────────────────────────────────────────────────

_POS_NORM: Dict[str, str] = {
    "GK": "GK", "GKP": "GK",
    "DF": "DF", "CB": "DF", "LB": "DF", "RB": "DF",
    "WB": "DF", "LWB": "DF", "RWB": "DF",
    "MF": "MF", "CM": "MF", "CDM": "MF", "CAM": "MF",
    "LM": "MF", "RM": "MF", "AM": "MF", "DM": "MF",
    "DMF": "MF", "AMF": "MF",
    "FW": "FW", "LW": "FW", "RW": "FW", "CF": "FW",
    "ST": "FW", "SS": "FW", "WF": "FW",
}

def _normalize_position(raw: str) -> str:
    if not raw or raw.upper() in ("SUB", "N/D", "UNKNOWN", ""):
        return "N/D"
    return _POS_NORM.get(raw.upper(), "N/D")

# ─── League + team helpers ─────────────────────────────────────────────────

async def _resolve_league_id(conn, league: str) -> int:
    res = await conn.execute(
        text("SELECT id FROM league WHERE name ILIKE :n LIMIT 1"),
        {"n": league}
    )
    row = res.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Lega '{league}' non trovata")
    return int(row[0])

def _latest_team_cte_sql() -> str:
    return """latest_team AS (
    SELECT DISTINCT ON (r_lt.player_id)
        r_lt.player_id,
        CASE WHEN r_lt.team_type ILIKE 'h%'
             THEN mc_lt.home_team_id
             ELSE mc_lt.away_team_id
        END AS current_team_id
    FROM rosters r_lt
    JOIN matchcalendar mc_lt ON mc_lt.id = r_lt.match_id
        AND mc_lt.is_completed = true
        AND mc_lt.league_id = :league_id
    ORDER BY r_lt.player_id, mc_lt.match_datetime DESC
)"""

def _combine_cte(base_cte: str, extra_cte_body: str) -> str:
    if base_cte.strip():
        return base_cte.rstrip() + ",\n" + extra_cte_body
    return "WITH\n" + extra_cte_body

# ─── Temporal Filter Builder ───────────────────────────────────────────────

def build_filter_parts(filter_type: str, with_league: bool = False) -> Tuple[str, str, str]:
    league_in_cte = "AND mc_i.league_id = :league_id" if with_league else ""

    if filter_type == "previous":
        return (
            "",
            "",
            "AND EXTRACT(YEAR FROM mc.match_datetime) = "
            "(SELECT EXTRACT(YEAR FROM MAX(match_datetime)) FROM matchcalendar) - 1"
        )
    elif filter_type == "last5":
        cte = f"""WITH ranked_matches AS (
            SELECT r_i.player_id, mc_i.id AS match_id,
                   ROW_NUMBER() OVER (
                       PARTITION BY r_i.player_id ORDER BY mc_i.match_datetime DESC
                   ) AS rn
            FROM rosters r_i
            JOIN matchcalendar mc_i ON mc_i.id = r_i.match_id
            WHERE mc_i.is_completed = true {league_in_cte}
        ), last5 AS (
            SELECT player_id, match_id FROM ranked_matches WHERE rn <= 5
        )"""
        extra_join = "JOIN last5 l5 ON l5.player_id = r.player_id AND l5.match_id = mc.id"
        return (cte, extra_join, "")
    else:  # current — full season span (e.g. Aug 2025 → Aug 2026 for 2025/26)
        return (
            "",
            "",
            "AND mc.match_datetime >= ("
            "    SELECT CASE"
            "        WHEN EXTRACT(MONTH FROM MAX(mc_i.match_datetime)) >= 8"
            "        THEN DATE_TRUNC('year', MAX(mc_i.match_datetime)) + INTERVAL '7 months'"
            "        ELSE DATE_TRUNC('year', MAX(mc_i.match_datetime)) - INTERVAL '5 months'"
            "    END"
            "    FROM matchcalendar mc_i"
            "    WHERE mc_i.is_completed = true"
            f"    {'AND mc_i.league_id = :league_id' if with_league else ''}"
            ")"
            "AND mc.match_datetime < ("
            "    SELECT CASE"
            "        WHEN EXTRACT(MONTH FROM MAX(mc_i.match_datetime)) >= 8"
            "        THEN DATE_TRUNC('year', MAX(mc_i.match_datetime)) + INTERVAL '1 year' + INTERVAL '7 months'"
            "        ELSE DATE_TRUNC('year', MAX(mc_i.match_datetime)) + INTERVAL '7 months'"
            "    END"
            "    FROM matchcalendar mc_i"
            "    WHERE mc_i.is_completed = true"
            f"    {'AND mc_i.league_id = :league_id' if with_league else ''}"
            ")"
        )

def p90(total: float, minutes: float) -> float:
    if minutes < 1:
        return 0.0
    return round(total / minutes * 90, 3)

def safe_float(v) -> float:
    try:
        f = float(v or 0)
        return 0.0 if (math.isnan(f) or math.isinf(f)) else f
    except Exception:
        return 0.0

# ─── Core metric helpers (legacy, kept for backward compat) ───────────────

def normalize_season_weights(years: List[int]) -> Dict[int, float]:
    if not years:
        return {}
    sorted_years = sorted(years, reverse=True)
    weights = [0.5, 0.3, 0.2]
    if len(sorted_years) < 3:
        total = sum(weights[:len(sorted_years)])
        weights = [w / total for w in weights[:len(sorted_years)]]
    else:
        sorted_years = sorted_years[:3]
        weights = weights[:3]
    return dict(zip(sorted_years, weights))

def compute_weighted_xg_xa(season_stats: List[Dict]) -> Dict[str, float]:
    if not season_stats:
        return {"weighted_xg": 0.0, "weighted_xa": 0.0}
    years = [s["season"] for s in season_stats]
    weights = normalize_season_weights(years)
    wxg = sum(s["xg"] * weights[s["season"]] for s in season_stats if s["season"] in weights)
    wxa = sum(s["xa"] * weights[s["season"]] for s in season_stats if s["season"] in weights)
    return {"weighted_xg": wxg, "weighted_xa": wxa}

def compute_breakout_score(season_stats: List[Dict]) -> float:
    if not season_stats:
        return 1.0
    latest = max(season_stats, key=lambda s: s["season"])
    xg = latest["xg"]
    goals = latest["goals"]
    if xg == 0:
        return 1.0
    delta = (xg - goals) / xg
    return 1.0 + (delta * 0.5)

async def get_team_attack_index(conn, team_name: str, league_id: int) -> float:
    if not team_name:
        return 1.0
    result = await conn.execute(text("""
        SELECT AVG(CASE WHEN th.name = :t THEN mc."home_xG" ELSE mc."away_xG" END)
        FROM matchcalendar mc
        JOIN team th ON mc.home_team_id = th.id
        JOIN team ta ON mc.away_team_id = ta.id
        WHERE (th.name = :t OR ta.name = :t)
          AND mc.is_completed = true
          AND mc.league_id = :league_id
    """), {"t": team_name, "league_id": league_id})
    row = result.fetchone()
    avg_xg = float(row[0]) if row and row[0] else 1.0
    if avg_xg >= 1.5:
        return 1.2
    elif avg_xg >= 1.0:
        return 1.0
    return 0.8

def compute_value_score(wxg: float, wxa: float, position: str = "") -> float:
    return wxg * FANTASY_PTS_GOAL + wxa * FANTASY_PTS_ASSIST

def compute_max_bid_percentage(value_score: float, max_value: float = 100.0) -> float:
    if max_value == 0:
        return 0.0
    return min((value_score / max_value) * 20, 20.0)

def generate_labels(season_stats: List[Dict]) -> List[str]:
    labels = []
    if not season_stats:
        return labels
    latest = max(season_stats, key=lambda s: s["season"])
    xg, goals, shots = latest["xg"], latest["goals"], latest.get("shots", 0)
    if xg > goals and xg > 0.2:
        labels.append("Undervalued Finisher")
    if goals > xg * 1.5 and xg > 0.1:
        labels.append("Overperformer - Risky")
    if shots > 40 and xg / max(shots, 1) < 0.1:
        labels.append("Volume Striker")
    if len(season_stats) >= 2:
        xg_list = [s["xg"] for s in season_stats]
        if max(xg_list) - min(xg_list) < 0.5:
            labels.append("Safe Pick")
    return labels

# ─── NEW: Players List Endpoint ────────────────────────────────────────────

@router.get("/seasons")
async def get_fanta_seasons(league: str = Query("Serie A")):
    try:
        async with engine.connect() as conn:
            league_id = await _resolve_league_id(conn, league)
            result = await conn.execute(text("""
                SELECT DISTINCT EXTRACT(YEAR FROM mc.match_datetime)::int AS yr
                FROM matchcalendar mc
                WHERE mc.is_completed = true AND mc.league_id = :league_id
                ORDER BY yr DESC
            """), {"league_id": league_id})
            return [row[0] for row in result.fetchall()]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Seasons error: {e}")
        return []


@router.get("/players")
async def get_fanta_players(
    filter: str = Query("current", pattern="^(current|previous|last5)$"),
    league: str = Query("Serie A"),
    year: Optional[int] = Query(None),
):
    try:
        cte, extra_join, where = build_filter_parts(filter, with_league=True)
        if year is not None and filter != "last5":
            where = "AND EXTRACT(YEAR FROM mc.match_datetime) = :year"
        full_cte = _combine_cte(cte, _latest_team_cte_sql())
        min_min = MIN_MINUTES_LAST5 if filter == "last5" else MIN_MINUTES

        query_sql = f"""
            {full_cte}
            SELECT
                r.player,
                r.player_id::text                  AS player_id,
                MODE() WITHIN GROUP (ORDER BY r.position)
                    FILTER (WHERE r.position NOT IN ('Sub', 'SUB') AND r.position IS NOT NULL)
                                                   AS position,
                COUNT(DISTINCT mc.id)              AS matches,
                SUM(r."xG")                        AS total_xg,
                SUM(r."xA")                        AS total_xa,
                SUM(r.shots::float)                AS total_shots,
                COALESCE(SUM(r."xGChain"::float),0) AS total_xgchain,
                COALESCE(SUM(r.key_passes::float),0) AS total_keypasses,
                SUM(r.goals)                       AS total_goals,
                SUM(r.assists)                     AS total_assists,
                SUM(r.time::float)                 AS total_minutes,
                MAX(t_curr.name)                   AS team_name,
                SUM(CASE WHEN r.position NOT IN ('Sub', 'SUB') AND r.position IS NOT NULL THEN 1 ELSE 0 END) AS starts,
                SUM(CASE WHEN r.roster_in > 0 THEN 1 ELSE 0 END) AS sub_ins
            FROM rosters r
            JOIN matchcalendar mc ON mc.id = r.match_id
                AND mc.is_completed = true
                AND mc.league_id = :league_id
            LEFT JOIN latest_team lt ON lt.player_id = r.player_id
            LEFT JOIN team t_curr ON t_curr.id = lt.current_team_id
            {extra_join}
            WHERE 1=1 {where}
            GROUP BY r.player, r.player_id
            HAVING SUM(r.time::float) >= {min_min}
            ORDER BY SUM(r."xG") DESC
        """

        async with engine.connect() as conn:
            league_id = await _resolve_league_id(conn, league)
            params: dict = {"league_id": league_id}
            if year is not None and filter != "last5":
                params["year"] = year
            result = await conn.execute(text(query_sql), params)
            rows = result.fetchall()

        players = []
        for row in rows:
            mins      = safe_float(row[11])
            xg        = safe_float(row[4])
            xa        = safe_float(row[5])
            shots     = safe_float(row[6])
            xgchain   = safe_float(row[7])
            keypasses = safe_float(row[8])
            goals     = int(row[9] or 0)
            assists   = int(row[10] or 0)
            matches   = int(row[3] or 0)

            starts    = int(row[13] or 0)
            sub_ins   = int(row[14] or 0)

            xg_p90        = p90(xg, mins)
            xa_p90        = p90(xa, mins)
            shots_p90     = p90(shots, mins)
            xgchain_p90   = p90(xgchain, mins)
            keypasses_p90 = p90(keypasses, mins)
            production    = round(xg_p90 + xa_p90, 3)
            value         = xg_p90 * FANTASY_PTS_GOAL + xa_p90 * FANTASY_PTS_ASSIST

            titolarita_pct = round((starts / matches) * 100, 1) if matches > 0 else 0.0

            # 🚫 Hard-filter: skip benchwarmers with < 25% starter rate
            if titolarita_pct < 25.0:
                continue

            luck_index     = round((goals + assists) - (xg + xa), 2)
            efo            = round((xg_p90 * FANTASY_PTS_GOAL) + (xa_p90 * FANTASY_PTS_ASSIST), 2)
            is_breakout    = luck_index <= -1.0 and xg_p90 >= 0.15

            players.append({
                "player":         row[0],
                "player_id":      str(row[1]),
                "position":       _normalize_position(row[2]),
                "team":           row[12] or "",
                "matches":        matches,
                "goals":          goals,
                "assists":        assists,
                "minutes":        round(mins),
                "xg_p90":         xg_p90,
                "xa_p90":         xa_p90,
                "shots_p90":      shots_p90,
                "xgchain_p90":    xgchain_p90,
                "keypasses_p90":  keypasses_p90,
                "production":     production,
                "value_score":    round(value, 2),
                "titolarita_pct": titolarita_pct,
                "luck_index":     luck_index,
                "efo":            efo,
                "is_breakout":    is_breakout,
            })

        if players:
            max_vs = max(p["value_score"] for p in players) or 1.0
            for p in players:
                p["max_bid_pct"] = round(compute_max_bid_percentage(p["value_score"], max_vs), 1)

        return players

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Players list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── NEW: Enhanced Player Profile ─────────────────────────────────────────

async def _compute_percentiles(conn, player_id: str, position: str, filter_type: str, league_id: int) -> Dict[str, int]:
    cte, extra_join, where = build_filter_parts(filter_type, with_league=True)
    min_min = MIN_MINUTES_LAST5 if filter_type == "last5" else MIN_MINUTES

    q = text(f"""
        {cte if cte else ""}
        SELECT
            r.player_id::text,
            SUM(r."xG") / NULLIF(SUM(r.time::float), 0) * 90              AS xg_p90,
            SUM(r."xA") / NULLIF(SUM(r.time::float), 0) * 90              AS xa_p90,
            SUM(r.shots::float) / NULLIF(SUM(r.time::float), 0) * 90      AS shots_p90,
            COALESCE(SUM(r."xGChain"::float), 0)
                / NULLIF(SUM(r.time::float), 0) * 90                       AS xgchain_p90,
            COALESCE(SUM(r.key_passes::float), 0)
                / NULLIF(SUM(r.time::float), 0) * 90                       AS keypasses_p90
        FROM rosters r
        JOIN matchcalendar mc ON mc.id = r.match_id
            AND mc.is_completed = true
            AND mc.league_id = :league_id
        {extra_join}
        WHERE r.position = :pos {where}
        GROUP BY r.player_id
        HAVING SUM(r.time::float) >= {min_min}
    """)
    result = await conn.execute(q, {"pos": position, "league_id": league_id})
    rows = result.fetchall()

    metrics = ["xg_p90", "xa_p90", "shots_p90", "xgchain_p90", "keypasses_p90"]
    all_vals: Dict[str, List[float]] = {m: [] for m in metrics}
    target: Dict[str, float] = {m: 0.0 for m in metrics}

    for row in rows:
        pid = str(row[0])
        for i, m in enumerate(metrics):
            val = safe_float(row[i + 1])
            all_vals[m].append(val)
            if pid == str(player_id):
                target[m] = val

    percentiles = {}
    for m in metrics:
        vals = sorted(all_vals[m])
        if not vals:
            percentiles[m] = 50
            continue
        tval = target[m]
        rank = sum(1 for v in vals if v <= tval)
        percentiles[m] = min(round(rank / len(vals) * 100), 99)

    return percentiles


@router.get("/player/{player_id}")
async def get_fanta_player_profile(
    player_id: str,
    filter: str = Query("current", pattern="^(current|previous|last5)$"),
    league: str = Query("Serie A"),
):
    try:
        cte, extra_join, where = build_filter_parts(filter, with_league=True)
        full_cte = _combine_cte(cte, _latest_team_cte_sql())

        async with engine.connect() as conn:
            league_id = await _resolve_league_id(conn, league)

            # 1. Aggregate stats
            agg_sql = f"""
                {full_cte}
                SELECT
                    r.player,
                    MODE() WITHIN GROUP (ORDER BY r.position)
                        FILTER (WHERE r.position NOT IN ('Sub', 'SUB') AND r.position IS NOT NULL)
                                                        AS position,
                    COUNT(DISTINCT mc.id)               AS matches,
                    SUM(r."xG")                         AS total_xg,
                    SUM(r."xA")                         AS total_xa,
                    SUM(r.shots::float)                 AS total_shots,
                    COALESCE(SUM(r."xGChain"::float),0) AS total_xgchain,
                    COALESCE(SUM(r.key_passes::float),0) AS total_keypasses,
                    SUM(r.goals)                        AS total_goals,
                    SUM(r.assists)                      AS total_assists,
                    SUM(r.time::float)                  AS total_minutes,
                    MAX(t_curr.name)                    AS team_name
                FROM rosters r
                JOIN matchcalendar mc ON mc.id = r.match_id
                    AND mc.is_completed = true
                    AND mc.league_id = :league_id
                LEFT JOIN latest_team lt ON lt.player_id = r.player_id
                LEFT JOIN team t_curr ON t_curr.id = lt.current_team_id
                {extra_join}
                WHERE r.player_id = :pid {where}
                GROUP BY r.player
                HAVING SUM(r.time::float) >= 1
            """
            agg_res = await conn.execute(text(agg_sql), {"pid": player_id, "league_id": league_id})
            agg = agg_res.fetchone()

            if not agg:
                raise HTTPException(status_code=404, detail="Giocatore non trovato")

            mins      = safe_float(agg[10])
            xg        = safe_float(agg[3])
            xa        = safe_float(agg[4])
            shots     = safe_float(agg[5])
            xgchain   = safe_float(agg[6])
            keypasses = safe_float(agg[7])
            goals     = int(agg[8] or 0)
            assists   = int(agg[9] or 0)
            position  = _normalize_position(agg[1])
            team      = agg[11] or ""
            player_name = agg[0]

            stats = {
                "xg_p90":        p90(xg, mins),
                "xa_p90":        p90(xa, mins),
                "shots_p90":     p90(shots, mins),
                "xgchain_p90":   p90(xgchain, mins),
                "keypasses_p90": p90(keypasses, mins),
                "goals":         goals,
                "assists":       assists,
                "matches":       int(agg[2] or 0),
                "minutes":       round(mins),
            }

            # 2. Percentile ranks (league-scoped)
            percentiles = await _compute_percentiles(conn, player_id, position, filter, league_id)

            # 3. Shot map filtered by league
            if filter == "current":
                shots_match_filter = """
                    AND s.match_id IN (
                        SELECT id FROM matchcalendar
                        WHERE is_completed = true
                        AND league_id = :league_id
                        AND EXTRACT(YEAR FROM match_datetime) =
                            (SELECT EXTRACT(YEAR FROM MAX(match_datetime)) FROM matchcalendar)
                    )
                """
            elif filter == "previous":
                shots_match_filter = """
                    AND s.match_id IN (
                        SELECT id FROM matchcalendar
                        WHERE is_completed = true
                        AND league_id = :league_id
                        AND EXTRACT(YEAR FROM match_datetime) =
                            (SELECT EXTRACT(YEAR FROM MAX(match_datetime)) FROM matchcalendar) - 1
                    )
                """
            else:  # last5
                shots_match_filter = """
                    AND s.match_id IN (
                        SELECT mc_i.id
                        FROM rosters r_i
                        JOIN matchcalendar mc_i ON mc_i.id = r_i.match_id
                        WHERE r_i.player_id = :pid
                          AND mc_i.is_completed = true
                          AND mc_i.league_id = :league_id
                        ORDER BY mc_i.match_datetime DESC
                        LIMIT 5
                    )
                """

            shots_res = await conn.execute(
                text(f"""
                    SELECT s."X", s."Y", s."xG", s.result, s.situation, s."shotType", s.minute
                    FROM shots s
                    WHERE s.player_id = :pid {shots_match_filter}
                    ORDER BY s.minute
                """),
                {"pid": player_id, "league_id": league_id}
            )
            shots_data = [
                {
                    "X": safe_float(r[0]), "Y": safe_float(r[1]), "xG": safe_float(r[2]),
                    "result": r[3] or "Miss", "situation": r[4] or "Open Play",
                    "shotType": r[5] or "N/D", "minute": int(r[6] or 0),
                }
                for r in shots_res.fetchall()
            ]

            # 4. Per-matchday trend (league-scoped)
            trend_sql = f"""
                {cte if cte else ""}
                SELECT
                    mc.round                        AS matchday,
                    mc.match_datetime::date         AS match_date,
                    SUM(r."xG")                     AS xg,
                    SUM(r.goals)                    AS goals,
                    SUM(r."xA")                     AS xa,
                    SUM(r.assists)                  AS assists
                FROM rosters r
                JOIN matchcalendar mc ON mc.id = r.match_id
                    AND mc.is_completed = true
                    AND mc.league_id = :league_id
                {extra_join}
                WHERE r.player_id = :pid {where}
                GROUP BY mc.round, mc.match_datetime::date
                ORDER BY match_date
            """
            trend_res = await conn.execute(text(trend_sql), {"pid": player_id, "league_id": league_id})
            trend = [
                {
                    "matchday": int(r[0] or 0), "date": str(r[1]),
                    "xg": round(safe_float(r[2]), 3), "goals": int(r[3] or 0),
                    "xa": round(safe_float(r[4]), 3), "assists": int(r[5] or 0),
                }
                for r in trend_res.fetchall()
            ]

            # 5. Legacy seasonal breakdown (league-scoped)
            legacy_res = await conn.execute(text(f"""
                WITH
                {_latest_team_cte_sql()}
                SELECT
                    EXTRACT(YEAR FROM mc.match_datetime)::int AS season,
                    SUM(r.goals) as goals, SUM(r.assists) as assists,
                    SUM(r."xG") as xg,    SUM(r."xA") as xa,
                    SUM(r.shots) as shots, SUM(r.time) as minutes,
                    MAX(t_l.name) as team_name
                FROM rosters r
                JOIN matchcalendar mc ON mc.id = r.match_id
                    AND mc.league_id = :league_id
                LEFT JOIN latest_team lt_l ON lt_l.player_id = r.player_id
                LEFT JOIN team t_l ON t_l.id = lt_l.current_team_id
                WHERE r.player_id = :pid
                GROUP BY EXTRACT(YEAR FROM mc.match_datetime)
                ORDER BY season DESC
            """), {"pid": player_id, "league_id": league_id})
            season_stats_raw = [dict(r._mapping) for r in legacy_res.fetchall()]
            season_stats = [
                {k: (float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v)
                 for k, v in s.items()} for s in season_stats_raw
            ]

            tai = await get_team_attack_index(conn, team, league_id)

        weighted = compute_weighted_xg_xa(season_stats)
        breakout = compute_breakout_score(season_stats)
        value_score = compute_value_score(weighted["weighted_xg"], weighted["weighted_xa"], position)
        labels = generate_labels(season_stats)

        return {
            "player":              player_name,
            "player_id":           player_id,
            "position":            position,
            "team":                team,
            "filter":              filter,
            "league":              league,
            "stats":               stats,
            "percentiles":         percentiles,
            "shots":               shots_data,
            "trend":               trend,
            "season_stats":        season_stats,
            "weighted_xg":         round(weighted["weighted_xg"], 2),
            "weighted_xa":         round(weighted["weighted_xa"], 2),
            "breakout_multiplier": round(breakout, 2),
            "team_attack_index":   tai,
            "value_score":         round(value_score, 1),
            "max_bid_percentage":  round(compute_max_bid_percentage(value_score), 1),
            "labels":              labels,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Player profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── Existing: Search ──────────────────────────────────────────────────────

@router.get("/search")
async def search_fanta_players(
    q: str = Query(..., min_length=2),
    league: str = Query("Serie A"),
):
    try:
        async with engine.connect() as conn:
            league_id = await _resolve_league_id(conn, league)
            result = await conn.execute(text("""
                SELECT r.player, MIN(r.player_id)::text AS player_id, MAX(r.position) AS position
                FROM rosters r
                JOIN matchcalendar mc ON mc.id = r.match_id
                    AND mc.league_id = :league_id
                WHERE r.player ILIKE :q
                GROUP BY r.player
                ORDER BY r.player
                LIMIT 10
            """), {"q": f"%{q}%", "league_id": league_id})
            rows = result.mappings().all()
            return [
                {
                    "player":    r["player"],
                    "player_id": str(r["player_id"]),
                    "position":  _normalize_position(r["position"]),
                }
                for r in rows
            ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []


# ─── Existing: Dashboard (legacy 4-widget) ─────────────────────────────────

@router.get("/dashboard")
async def get_fanta_dashboard(league: str = Query("Serie A")):
    try:
        async with engine.connect() as conn:
            league_id = await _resolve_league_id(conn, league)
            full_cte = "WITH\n" + _latest_team_cte_sql()
            result = await conn.execute(text(f"""
                {full_cte}
                SELECT r.player, MIN(r.player_id)::text AS player_id,
                    MAX(r.position) AS position,
                    EXTRACT(YEAR FROM mc.match_datetime)::int AS season,
                    SUM(r.goals) AS goals, SUM(r.assists) AS assists,
                    SUM(r."xG") AS xg, SUM(r."xA") AS xa,
                    SUM(r.shots) AS shots, SUM(r.time) AS minutes,
                    MAX(t_curr.name) AS team_name
                FROM rosters r
                JOIN matchcalendar mc ON mc.id = r.match_id
                    AND mc.league_id = :league_id
                LEFT JOIN latest_team lt ON lt.player_id = r.player_id
                LEFT JOIN team t_curr ON t_curr.id = lt.current_team_id
                WHERE EXTRACT(YEAR FROM mc.match_datetime) >= EXTRACT(YEAR FROM NOW()) - 3
                GROUP BY r.player, r.player_id, EXTRACT(YEAR FROM mc.match_datetime)
                HAVING SUM(r.time) > 200
                ORDER BY r.player, season DESC
            """), {"league_id": league_id})
            rows = result.mappings().all()

        players_map: dict = {}
        for row in rows:
            name = row["player"]
            if name not in players_map:
                players_map[name] = {
                    "player_id": row["player_id"],
                    "position": _normalize_position(row["position"]),
                    "seasons": []
                }
            players_map[name]["seasons"].append({
                "season": row["season"], "goals": int(row["goals"] or 0),
                "assists": int(row["assists"] or 0), "xg": float(row["xg"] or 0),
                "xa": float(row["xa"] or 0), "shots": int(row["shots"] or 0),
                "minutes": int(row["minutes"] or 0), "team_name": row["team_name"] or "",
            })

        all_profiles = []
        for name, data in players_map.items():
            seasons = data["seasons"]
            weighted = compute_weighted_xg_xa(seasons)
            breakout = compute_breakout_score(seasons)
            value = compute_value_score(weighted["weighted_xg"], weighted["weighted_xa"], data["position"])
            labels = generate_labels(seasons)
            all_profiles.append({
                "player": name, "player_id": data["player_id"], "position": data["position"],
                "team": seasons[0]["team_name"] if seasons else "",
                "weighted_xg": round(weighted["weighted_xg"], 2),
                "weighted_xa": round(weighted["weighted_xa"], 2),
                "breakout_multiplier": round(breakout, 2), "value_score": round(value, 1),
                "labels": labels, "latest_xg": seasons[0]["xg"] if seasons else 0,
                "latest_goals": seasons[0]["goals"] if seasons else 0,
            })

        if not all_profiles:
            return {"best_value_picks": [], "breakout_candidates": [], "toxic_assets": [], "safe_picks": []}

        max_vs = max(p["value_score"] for p in all_profiles) or 1.0
        for p in all_profiles:
            p["max_bid_pct"] = round(compute_max_bid_percentage(p["value_score"], max_vs), 1)

        return {
            "best_value_picks":    sorted([p for p in all_profiles if "Undervalued Finisher" in p["labels"]], key=lambda x: x["value_score"], reverse=True)[:8],
            "breakout_candidates": sorted([p for p in all_profiles if p["breakout_multiplier"] > 1.15], key=lambda x: x["breakout_multiplier"], reverse=True)[:8],
            "toxic_assets":        sorted([p for p in all_profiles if "Overperformer - Risky" in p["labels"]], key=lambda x: (x["latest_goals"] - x["latest_xg"]), reverse=True)[:8],
            "safe_picks":          sorted([p for p in all_profiles if "Safe Pick" in p["labels"]], key=lambda x: x["value_score"], reverse=True)[:8],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── Existing: Auction Strategy ────────────────────────────────────────────

@router.get("/auction-strategy")
async def get_auction_strategy(
    budget: float = Query(500),
    participants: int = Query(8),
    filter: str = Query("current", pattern="^(current|previous|last5)$"),
    league: str = Query("Serie A"),
):
    try:
        cte, extra_join, where = build_filter_parts(filter, with_league=True)
        full_cte = _combine_cte(cte, _latest_team_cte_sql())
        min_min = MIN_MINUTES_LAST5 if filter == "last5" else MIN_MINUTES

        query_sql = f"""
            {full_cte}
            SELECT r.player, MIN(r.player_id)::text AS player_id,
                MAX(r.position) AS position,
                EXTRACT(YEAR FROM mc.match_datetime)::int AS season,
                SUM(r.goals) AS goals, SUM(r.assists) AS assists,
                SUM(r."xG") AS xg, SUM(r."xA") AS xa,
                SUM(r.shots) AS shots, SUM(r.time) AS minutes,
                MAX(t_curr.name) AS team_name
            FROM rosters r
            JOIN matchcalendar mc ON mc.id = r.match_id
                AND mc.is_completed = true
                AND mc.league_id = :league_id
            LEFT JOIN latest_team lt ON lt.player_id = r.player_id
            LEFT JOIN team t_curr ON t_curr.id = lt.current_team_id
            {extra_join}
            WHERE 1=1 {where}
            GROUP BY r.player, r.player_id, EXTRACT(YEAR FROM mc.match_datetime)
            HAVING SUM(r.time) > {min_min}
            ORDER BY r.player, season DESC
        """

        async with engine.connect() as conn:
            league_id = await _resolve_league_id(conn, league)
            result = await conn.execute(text(query_sql), {"league_id": league_id})
            rows = result.mappings().all()
            tai_result = await conn.execute(text("""
                SELECT t.name,
                    AVG(CASE WHEN mc.home_team_id=t.id THEN mc."home_xG" ELSE mc."away_xG" END) as avg_xg
                FROM team t
                JOIN matchcalendar mc ON (mc.home_team_id=t.id OR mc.away_team_id=t.id)
                WHERE mc.is_completed=true AND mc.league_id=:league_id
                GROUP BY t.name
            """), {"league_id": league_id})
            tai_map = {}
            for r in tai_result.fetchall():
                avg = float(r[1]) if r[1] else 1.0
                tai_map[r[0]] = 1.2 if avg >= 1.5 else (0.8 if avg < 1.0 else 1.0)

        players_map: dict = {}
        for row in rows:
            name = row["player"]
            if name not in players_map:
                players_map[name] = {
                    "player_id": row["player_id"],
                    "position": _normalize_position(row["position"]),
                    "seasons": []
                }
            players_map[name]["seasons"].append({
                "season": row["season"], "goals": int(row["goals"] or 0),
                "assists": int(row["assists"] or 0), "xg": float(row["xg"] or 0),
                "xa": float(row["xa"] or 0), "shots": int(row["shots"] or 0),
                "minutes": int(row["minutes"] or 0), "team_name": row["team_name"] or "",
            })

        POSITION_MAP_NORM = {"GK": "GK", "DF": "DF", "MF": "MF", "FW": "FW"}
        all_profiles = []
        for name, data in players_map.items():
            seasons = data["seasons"]
            weighted = compute_weighted_xg_xa(seasons)
            team = seasons[0]["team_name"] if seasons else ""
            tai = tai_map.get(team, 1.0)
            value = compute_value_score(weighted["weighted_xg"], weighted["weighted_xa"], data["position"]) * tai
            all_profiles.append({
                "player": name, "player_id": data["player_id"],
                "position": POSITION_MAP_NORM.get(data["position"], data["position"]),
                "team": team, "tai": tai, "value_score": round(value, 1),
            })

        if not all_profiles:
            return {"budget": budget, "participants": participants, "targets": []}

        max_vs = max(p["value_score"] for p in all_profiles) or 1.0
        counts = {"GK": 1, "DF": 3, "MF": 4, "FW": 3}
        targets = []
        for role, n in counts.items():
            for p in sorted([p for p in all_profiles if p["position"] == role], key=lambda x: x["value_score"], reverse=True)[:n]:
                pct = compute_max_bid_percentage(p["value_score"], max_vs)
                targets.append({
                    "name": p["player"], "player_id": p["player_id"], "position": p["position"],
                    "team": p["team"], "tai": p["tai"], "value_score": p["value_score"],
                    "max_price": round(budget * (pct / 100), 0), "budget_percentage": round(pct, 1),
                })

        targets.sort(key=lambda x: x["value_score"], reverse=True)
        return {"budget": budget, "participants": participants, "targets": targets}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auction strategy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
