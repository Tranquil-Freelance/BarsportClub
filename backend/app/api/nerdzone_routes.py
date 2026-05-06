from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import text
from typing import List, Optional

from app.db.database import engine

router = APIRouter()

ALLOWED_COLUMNS = {
    "xG", "xA", "shots", "goals", "assists", "key_passes", "xGChain", "xGBuildup", "time"
}

DERIVED_METRICS = {
    "xG_p90":         'SUM(r."xG"::float)        / NULLIF(SUM(r.time::float), 0) * 90',
    "xA_p90":         'SUM(r."xA"::float)        / NULLIF(SUM(r.time::float), 0) * 90',
    "shots_p90":      'SUM(r.shots::float)       / NULLIF(SUM(r.time::float), 0) * 90',
    "goals_p90":      'SUM(r.goals::float)       / NULLIF(SUM(r.time::float), 0) * 90',
    "assists_p90":    'SUM(r.assists::float)     / NULLIF(SUM(r.time::float), 0) * 90',
    "key_passes_p90": 'SUM(r.key_passes::float)  / NULLIF(SUM(r.time::float), 0) * 90',
    "xGChain_p90":    'SUM(r."xGChain"::float)   / NULLIF(SUM(r.time::float), 0) * 90',
    "xGBuildup_p90":  'SUM(r."xGBuildup"::float) / NULLIF(SUM(r.time::float), 0) * 90',
}

QUOTED_COLS = {"xG", "xA", "xGChain", "xGBuildup"}

RADAR_METRIC_DEFS = [
    ("xG_p90",         'SUM(r."xG"::float)        / NULLIF(SUM(r.time::float), 0) * 90'),
    ("xA_p90",         'SUM(r."xA"::float)        / NULLIF(SUM(r.time::float), 0) * 90'),
    ("shots_p90",      'SUM(r.shots::float)       / NULLIF(SUM(r.time::float), 0) * 90'),
    ("key_passes_p90", 'SUM(r.key_passes::float)  / NULLIF(SUM(r.time::float), 0) * 90'),
    ("xGChain_p90",    'SUM(r."xGChain"::float)   / NULLIF(SUM(r.time::float), 0) * 90'),
    ("xGBuildup_p90",  'SUM(r."xGBuildup"::float) / NULLIF(SUM(r.time::float), 0) * 90'),
]

SEASON_DATES = {
    "2025/26": "2025-08-01",
    "2024/25": "2024-07-01",
    "2023/24": "2023-07-01",
}


def resolve_metric(col: str) -> str:
    if col in DERIVED_METRICS:
        return DERIVED_METRICS[col]
    if col in ALLOWED_COLUMNS:
        quoted = f'r."{col}"' if col in QUOTED_COLS else f"r.{col}"
        return f"SUM({quoted}::float)"
    raise HTTPException(
        status_code=400,
        detail=f"Invalid metric: '{col}'. Allowed: {sorted(ALLOWED_COLUMNS | set(DERIVED_METRICS))}.",
    )


@router.get("/api/nerd-zone/query")
async def nerd_zone_query(
    entity: str = Query(..., pattern="^(player|team)$"),
    xAxis: str = Query(...),
    yAxis: str = Query(...),
    zAxis: Optional[str] = Query(default=None),
    league_ids: List[int] = Query(default=[1]),  # Default: Serie A (id=1)
    min_time: int = Query(default=500, ge=0),
    roles: List[str] = Query(default=[]),
    location_filter: str = Query(default="All", pattern="^(All|Home|Away)$"),
    season: str = Query(default="2025/26"),
):
    x_expr = resolve_metric(xAxis)
    y_expr = resolve_metric(yAxis)
    z_expr = resolve_metric(zAxis) if zAxis else None

    location_clause = ""
    if location_filter == "Home":
        location_clause = "AND r.team_type ILIKE 'h%'"
    elif location_filter == "Away":
        location_clause = "AND r.team_type ILIKE 'a%'"

    season_clause = ""
    if season in SEASON_DATES:
        season_clause = f"AND mc.match_datetime >= '{SEASON_DATES[season]}'"

    z_select = f",\n               {z_expr} AS z" if z_expr else ",\n               NULL::float AS z"
    league_filter = "AND mc.league_id = ANY(CAST(:league_ids AS int[]))" if league_ids else ""

    if entity == "player":
        name_select = "r.player AS name"
        extra_selects = (
            "MAX(r.position) AS position,\n"
            "               MAX(lt_nz.team_name) AS team_name"
        )
        group_col = "r.player"
        join_team = (
            "LEFT JOIN (\n"
            "        SELECT DISTINCT ON (ctc.player) ctc.player, t.name AS team_name\n"
            "        FROM (\n"
            "            SELECT player, team_id, COUNT(*) AS appearances\n"
            "            FROM (\n"
            "                SELECT rm.player, rm.home_team_id AS team_id\n"
            "                FROM (\n"
            "                    SELECT r_s.player, mc_s.home_team_id, mc_s.away_team_id,\n"
            "                           ROW_NUMBER() OVER(PARTITION BY r_s.player ORDER BY mc_s.match_datetime DESC) AS rn\n"
            "                    FROM rosters r_s\n"
            "                    JOIN matchcalendar mc_s ON mc_s.id = r_s.match_id AND mc_s.is_completed = true\n"
            "                ) rm WHERE rm.rn <= 3\n"
            "                UNION ALL\n"
            "                SELECT rm.player, rm.away_team_id AS team_id\n"
            "                FROM (\n"
            "                    SELECT r_s.player, mc_s.home_team_id, mc_s.away_team_id,\n"
            "                           ROW_NUMBER() OVER(PARTITION BY r_s.player ORDER BY mc_s.match_datetime DESC) AS rn\n"
            "                    FROM rosters r_s\n"
            "                    JOIN matchcalendar mc_s ON mc_s.id = r_s.match_id AND mc_s.is_completed = true\n"
            "                ) rm WHERE rm.rn <= 3\n"
            "            ) rt\n"
            "            GROUP BY player, team_id\n"
            "        ) ctc\n"
            "        JOIN team t ON t.id = ctc.team_id\n"
            "        ORDER BY ctc.player, ctc.appearances DESC\n"
            "    ) lt_nz ON lt_nz.player = r.player"
        )
        role_filter = "AND UPPER(r.position) = ANY(CAST(:roles AS text[]))" if roles else ""
    else:
        name_select = "t.name AS name"
        extra_selects = "NULL::text AS position,\n               t.name AS team_name"
        group_col = "t.name"
        join_team = (
            "JOIN team t ON (\n"
            "            CASE WHEN r.team_type ILIKE 'h%' THEN mc.home_team_id ELSE mc.away_team_id END\n"
            "        ) = t.id"
        )
        role_filter = ""

    sql = f"""
        SELECT {name_select},
               {extra_selects},
               {x_expr} AS x,
               {y_expr} AS y
               {z_select}
        FROM rosters r
        JOIN matchcalendar mc ON r.match_id = mc.id
        {join_team}
        WHERE mc.is_completed = true
          {season_clause}
          {league_filter}
          {location_clause}
          {role_filter}
        GROUP BY {group_col}
        HAVING SUM(r.time::float) >= :min_time
        ORDER BY x DESC NULLS LAST
    """

    params: dict = {"min_time": min_time}
    if league_ids:
        params["league_ids"] = league_ids
    if roles:
        params["roles"] = [r.upper() for r in roles]

    async with engine.connect() as conn:
        res = await conn.execute(text(sql), params)
        rows = res.fetchall()

    return [
        {
            "name": row[0],
            "position": row[1],
            "team_name": row[2],
            "x": float(row[3]) if row[3] is not None else None,
            "y": float(row[4]) if row[4] is not None else None,
            "z": float(row[5]) if row[5] is not None else None,
        }
        for row in rows
    ]


@router.get("/api/nerd-zone/radar")
async def nerd_zone_radar(
    names: List[str] = Query(...),
    min_time: int = Query(default=0, ge=0),
    league_ids: List[int] = Query(default=[]),
):
    if not names:
        return []

    league_filter = ""
    params: dict = {"names": names, "min_time": min_time}
    if league_ids:
        league_filter = "AND mc.league_id = ANY(CAST(:league_ids AS int[]))"
        params["league_ids"] = league_ids
    else:
        # Default: Serie A
        league_filter = "AND mc.league_id = (SELECT id FROM league WHERE name ILIKE 'Serie A' LIMIT 1)"

    radar_selects = ",\n           ".join(
        f"{expr} AS {key}" for key, expr in RADAR_METRIC_DEFS
    )

    sql = f"""
        SELECT r.player AS name,
               {radar_selects}
        FROM rosters r
        JOIN matchcalendar mc ON r.match_id = mc.id
        WHERE r.player = ANY(CAST(:names AS text[]))
          {league_filter}
        GROUP BY r.player
        HAVING SUM(r.time::float) >= :min_time
    """

    async with engine.connect() as conn:
        res = await conn.execute(text(sql), params)
        rows = res.fetchall()

    radar_keys = ["name"] + [k for k, _ in RADAR_METRIC_DEFS]
    return [
        {k: (float(v) if v is not None and k != "name" else (v or "")) for k, v in zip(radar_keys, row)}
        for row in rows
    ]


# ─── NERD ZONE — UNDERSTAT CLONE ENDPOINTS ──────────────────────────────────

_SEASON_BOUNDS: dict[str, tuple[str, str]] = {
    "2025/26": ("2025-08-01", "2026-07-31"),
    "2024/25": ("2024-07-01", "2025-07-31"),
    "2023/24": ("2023-07-01", "2024-06-30"),
    "2022/23": ("2022-07-01", "2023-06-30"),
    "all":     ("2000-01-01", "2099-12-31"),
}


def season_range_sql(season: str, alias: str = "mc") -> str:
    """Embeds date range as SQL literal — avoids asyncpg timestamp binding issues."""
    s, e = _SEASON_BOUNDS.get(season, _SEASON_BOUNDS["2025/26"])
    return f"{alias}.match_datetime BETWEEN '{s}' AND '{e} 23:59:59'"


SEASON_LABEL_SQL = """
    CASE
        WHEN mc.match_datetime >= '2025-08-01' THEN '2025/26'
        WHEN mc.match_datetime >= '2024-07-01' THEN '2024/25'
        WHEN mc.match_datetime >= '2023-07-01' THEN '2023/24'
        WHEN mc.match_datetime >= '2022-07-01' THEN '2022/23'
        ELSE 'Older'
    END
"""

SHOT_ZONE_SQL = """
    CASE
        WHEN s."X" > 0.942 AND s."Y" BETWEEN 0.365 AND 0.635 THEN 'Six Yard Box'
        WHEN s."X" > 0.83  AND s."Y" BETWEEN 0.21  AND 0.79  THEN 'Penalty Area'
        WHEN s."X" > 0.83  AND s."Y" < 0.21                  THEN 'Penalty Area Left'
        WHEN s."X" > 0.83  AND s."Y" > 0.79                  THEN 'Penalty Area Right'
        WHEN s."X" BETWEEN 0.64 AND 0.83                      THEN 'Zone 14'
        ELSE 'Outside Box'
    END
"""


@router.get("/api/nerd-zone/league-table")
async def nerd_zone_league_table(
    league_id: int = Query(default=2),
    season:    str = Query(default="2025/26"),
):
    dr = season_range_sql(season)
    sql = text(f"""
        WITH tm AS (
            SELECT mc.home_team_id AS tid,
                   mc.home_goals::int AS gf, mc.away_goals::int AS ga,
                   mc."home_xG"::float AS xg, mc."away_xG"::float AS xga,
                   COALESCE(mc.home_xpts::float, 0) AS xpts
            FROM matchcalendar mc
            WHERE mc.is_completed = true AND mc.league_id = :lid AND {dr}
            UNION ALL
            SELECT mc.away_team_id,
                   mc.away_goals::int, mc.home_goals::int,
                   mc."away_xG"::float, mc."home_xG"::float,
                   COALESCE(mc.away_xpts::float, 0)
            FROM matchcalendar mc
            WHERE mc.is_completed = true AND mc.league_id = :lid AND {dr}
        )
        SELECT t.id, t.name,
               COUNT(*)::int                                                AS mp,
               SUM(CASE WHEN tm.gf>tm.ga THEN 1 ELSE 0 END)::int          AS w,
               SUM(CASE WHEN tm.gf=tm.ga THEN 1 ELSE 0 END)::int          AS d,
               SUM(CASE WHEN tm.gf<tm.ga THEN 1 ELSE 0 END)::int          AS l,
               SUM(tm.gf)::int                                              AS gf,
               SUM(tm.ga)::int                                              AS ga,
               (SUM(tm.gf)-SUM(tm.ga))::int                                AS gd,
               SUM(CASE WHEN tm.gf>tm.ga THEN 3 WHEN tm.gf=tm.ga THEN 1 ELSE 0 END)::int AS pts,
               ROUND(SUM(tm.xg)::numeric, 2)                               AS xg,
               ROUND(SUM(tm.xga)::numeric, 2)                              AS xga,
               ROUND(SUM(tm.xpts)::numeric, 2)                             AS xpts,
               ROUND((SUM(tm.xg)-SUM(tm.xga))::numeric, 2)                AS xgd
        FROM tm JOIN team t ON t.id = tm.tid
        GROUP BY t.id, t.name
        ORDER BY pts DESC, gd DESC, gf DESC
    """)
    async with engine.connect() as conn:
        res = await conn.execute(sql, {"lid": league_id})
        rows = res.fetchall()
    keys = ["id","name","mp","w","d","l","gf","ga","gd","pts","xg","xga","xpts","xgd"]
    return [dict(zip(keys, r)) for r in rows]


@router.get("/api/nerd-zone/teams")
async def nerd_zone_teams(league_id: int = Query(default=2)):
    sql = text("""
        SELECT DISTINCT t.id, t.name
        FROM team t
        JOIN matchcalendar mc ON (mc.home_team_id = t.id OR mc.away_team_id = t.id)
        WHERE mc.league_id = :lid
        ORDER BY t.name
    """)
    async with engine.connect() as conn:
        res = await conn.execute(sql, {"lid": league_id})
        rows = res.fetchall()
    return [{"id": r[0], "name": r[1]} for r in rows]


@router.get("/api/nerd-zone/team-matches")
async def nerd_zone_team_matches(
    team_id: int = Query(...),
    season:  str = Query(default="2025/26"),
    limit:   int = Query(default=38),
):
    dr = season_range_sql(season)
    sql = text(f"""
        SELECT mc.id                           AS match_id,
               mc.match_datetime::text         AS date,
               ht.name                         AS home_team,
               at.name                         AS away_team,
               mc.home_team_id,
               mc.away_team_id,
               mc.home_goals,
               mc.away_goals,
               mc."home_xG"::float             AS home_xg,
               mc."away_xG"::float             AS away_xg,
               mc.is_completed,
               mc.matchday,
               (mc.home_team_id = :tid)        AS is_home
        FROM matchcalendar mc
        JOIN team ht ON ht.id = mc.home_team_id
        JOIN team at ON at.id = mc.away_team_id
        WHERE (mc.home_team_id = :tid OR mc.away_team_id = :tid)
          AND {dr}
        ORDER BY mc.match_datetime
        LIMIT :lim
    """)
    async with engine.connect() as conn:
        res = await conn.execute(sql, {"tid": team_id, "lim": limit})
        rows = res.fetchall()
    keys = ["match_id","date","home_team","away_team","home_team_id","away_team_id",
            "home_goals","away_goals","home_xg","away_xg","is_completed","matchday","is_home"]
    return [dict(zip(keys, r)) for r in rows]


@router.get("/api/nerd-zone/team-roster")
async def nerd_zone_team_roster(
    team_id:  int           = Query(...),
    season:   str           = Query(default="2025/26"),
    position: Optional[str] = Query(default=None),
    last_n:   Optional[int] = Query(default=None),
):
    dr = season_range_sql(season)

    last_n_clause = ""
    if last_n:
        last_n_clause = f"""
            AND r.match_id IN (
                SELECT id FROM matchcalendar
                WHERE (home_team_id = :tid OR away_team_id = :tid)
                  AND is_completed = true
                ORDER BY match_datetime DESC LIMIT {int(last_n)}
            )"""

    pos_clause = ""
    params: dict = {"tid": team_id}
    if position and position.upper() != "ALL":
        pos_clause = "AND UPPER(r.position) = :pos"
        params["pos"] = position.upper()

    sql = text(f"""
        SELECT r.player,
               MAX(r.position)                                              AS position,
               COUNT(DISTINCT r.match_id)::int                             AS apps,
               ROUND(SUM(r.time::float)::numeric, 0)::int                  AS minutes,
               SUM(r.goals::float)::int                                     AS goals,
               SUM(r.assists::float)::int                                   AS assists,
               ROUND(SUM(r.shots::float)::numeric,0)::int                  AS shots,
               ROUND(SUM(r.key_passes::float)::numeric,0)::int             AS key_passes,
               ROUND(SUM(r."xG"::float)::numeric,2)                        AS xg,
               ROUND(SUM(r."xA"::float)::numeric,2)                        AS xa,
               ROUND(SUM(r."xGChain"::float)::numeric,2)                   AS xgchain,
               ROUND(SUM(r."xGBuildup"::float)::numeric,2)                 AS xgbuildup,
               ROUND(CASE WHEN SUM(r.time::float)>0
                     THEN SUM(r.shots::float)/SUM(r.time::float)*90
                     ELSE 0 END::numeric,2)                                 AS sh90,
               ROUND(CASE WHEN SUM(r.time::float)>0
                     THEN SUM(r.key_passes::float)/SUM(r.time::float)*90
                     ELSE 0 END::numeric,2)                                 AS kp90,
               ROUND(CASE WHEN SUM(r.time::float)>0
                     THEN SUM(r."xG"::float)/SUM(r.time::float)*90
                     ELSE 0 END::numeric,3)                                 AS xg90,
               ROUND(CASE WHEN SUM(r.time::float)>0
                     THEN SUM(r."xA"::float)/SUM(r.time::float)*90
                     ELSE 0 END::numeric,3)                                 AS xa90
        FROM rosters r
        JOIN matchcalendar mc ON mc.id = r.match_id
        WHERE mc.is_completed = true
          AND (
              (mc.home_team_id = :tid AND r.team_type ILIKE 'h%%')
              OR (mc.away_team_id = :tid AND r.team_type ILIKE 'a%%')
          )
          AND {dr}
          {last_n_clause}
          {pos_clause}
        GROUP BY r.player
        HAVING SUM(r.time::float) > 0
        ORDER BY xg DESC NULLS LAST
    """)
    async with engine.connect() as conn:
        res = await conn.execute(sql, params)
        rows = res.fetchall()
    keys = ["player","position","apps","minutes","goals","assists","shots","key_passes",
            "xg","xa","xgchain","xgbuildup","sh90","kp90","xg90","xa90"]
    return [dict(zip(keys, r)) for r in rows]


@router.get("/api/nerd-zone/team-stats")
async def nerd_zone_team_stats(
    team_id: int = Query(...),
    season:  str = Query(default="2025/26"),
    tab:     str = Query(default="situation"),
):
    dr = season_range_sql(season)

    if tab == "timing":
        dim_expr = """CASE
            WHEN s.minute BETWEEN 1  AND 15 THEN '1-15'
            WHEN s.minute BETWEEN 16 AND 30 THEN '16-30'
            WHEN s.minute BETWEEN 31 AND 45 THEN '31-45+'
            WHEN s.minute BETWEEN 46 AND 60 THEN '46-60'
            WHEN s.minute BETWEEN 61 AND 75 THEN '61-75'
            ELSE '76+'
        END"""
        order_by = "MIN(s.minute) ASC"
    elif tab == "zones":
        dim_expr = SHOT_ZONE_SQL
        order_by = "xg DESC"
    elif tab == "result":
        dim_expr = "s.result"
        order_by = "sh DESC"
    elif tab in ("formation", "game_state", "attack_speed"):
        return []
    else:  # situation
        dim_expr = "s.situation"
        order_by = "xg DESC"

    sql = text(f"""
        WITH fwd AS (
            SELECT {dim_expr} AS dim,
                   COUNT(*) AS sh,
                   SUM(CASE WHEN s.result='Goal' THEN 1 ELSE 0 END) AS g,
                   ROUND(SUM(s."xG"::float)::numeric,2) AS xg
            FROM shots s JOIN matchcalendar mc ON mc.id=s.match_id
            WHERE mc.is_completed=true
              AND ((mc.home_team_id=:tid AND s.h_a='h')
                   OR (mc.away_team_id=:tid AND s.h_a='a'))
              AND {dr}
            GROUP BY 1
        ),
        agn AS (
            SELECT {dim_expr} AS dim,
                   COUNT(*) AS sha,
                   SUM(CASE WHEN s.result='Goal' THEN 1 ELSE 0 END) AS ga,
                   ROUND(SUM(s."xG"::float)::numeric,2) AS xga
            FROM shots s JOIN matchcalendar mc ON mc.id=s.match_id
            WHERE mc.is_completed=true
              AND ((mc.home_team_id=:tid AND s.h_a='a')
                   OR (mc.away_team_id=:tid AND s.h_a='h'))
              AND {dr}
            GROUP BY 1
        )
        SELECT COALESCE(f.dim,a.dim)               AS dimension,
               COALESCE(f.sh,0)::int               AS sh,
               COALESCE(f.g,0)::int                AS g,
               COALESCE(a.sha,0)::int              AS sha,
               COALESCE(a.ga,0)::int               AS ga,
               COALESCE(f.xg,0)                    AS xg,
               COALESCE(a.xga,0)                   AS xga,
               ROUND((COALESCE(f.xg,0)-COALESCE(a.xga,0))::numeric,2) AS xgd,
               ROUND(CASE WHEN COALESCE(f.sh,0)>0
                     THEN COALESCE(f.xg,0)::float/f.sh ELSE 0 END::numeric,3) AS xg_per_sh,
               ROUND(CASE WHEN COALESCE(a.sha,0)>0
                     THEN COALESCE(a.xga,0)::float/a.sha ELSE 0 END::numeric,3) AS xga_per_sha
        FROM fwd f FULL OUTER JOIN agn a ON f.dim=a.dim
        ORDER BY {order_by}
    """)
    async with engine.connect() as conn:
        res = await conn.execute(sql, {"tid": team_id})
        rows = res.fetchall()
    keys = ["dimension","sh","g","sha","ga","xg","xga","xgd","xg_per_sh","xga_per_sha"]
    return [dict(zip(keys, r)) for r in rows]


# ---------------------------------------------------------------------------
# Player endpoints
# ---------------------------------------------------------------------------

@router.get("/api/nerd-zone/player-history")
async def nerd_zone_player_history(
    player:     str       = Query(...),
    tab:        str       = Query(default="season"),
    league_ids: List[int] = Query(default=[]),
):
    params: dict = {"player": player}
    league_clause = ""
    if league_ids:
        league_clause = "AND mc.league_id = ANY(CAST(:lids AS int[]))"
        params["lids"] = league_ids

    if tab == "situation":
        sql_str = f"""
            SELECT s.situation AS label,
                   COUNT(*)::int AS shots,
                   SUM(CASE WHEN s.result='Goal' THEN 1 ELSE 0 END)::int AS goals,
                   ROUND(SUM(s."xG"::float)::numeric,2) AS xg,
                   ROUND(CASE WHEN COUNT(*)>0
                         THEN SUM(s."xG"::float)/COUNT(*) ELSE 0 END::numeric,3) AS xg_per_shot,
                   ROUND(CASE WHEN COUNT(*)>0
                         THEN SUM(CASE WHEN s.result='Goal' THEN 1.0 ELSE 0 END)/COUNT(*)
                         ELSE 0 END::numeric,3) AS conversion_pct
            FROM shots s
            JOIN matchcalendar mc ON mc.id=s.match_id
            WHERE s.player=:player AND mc.is_completed=true {league_clause}
            GROUP BY s.situation ORDER BY xg DESC
        """
    elif tab == "position":
        sql_str = f"""
            SELECT UPPER(r.position) AS label,
                   COUNT(DISTINCT r.match_id)::int AS matches,
                   ROUND(SUM(r.time::float)::numeric, 0)::int AS minutes,
                   SUM(r.goals::float)::int AS goals,
                   SUM(r.assists::float)::int AS assists,
                   ROUND(SUM(r."xG"::float)::numeric,2) AS xg,
                   ROUND(SUM(r."xA"::float)::numeric,2) AS xa,
                   ROUND(CASE WHEN SUM(r.time::float)>0
                         THEN SUM(r.shots::float)/SUM(r.time::float)*90 ELSE 0 END::numeric,2) AS sh90,
                   ROUND(CASE WHEN SUM(r.time::float)>0
                         THEN SUM(r.key_passes::float)/SUM(r.time::float)*90 ELSE 0 END::numeric,2) AS kp90,
                   ROUND(CASE WHEN SUM(r.time::float)>0
                         THEN SUM(r."xG"::float)/SUM(r.time::float)*90 ELSE 0 END::numeric,3) AS xg90,
                   ROUND(CASE WHEN SUM(r.time::float)>0
                         THEN SUM(r."xA"::float)/SUM(r.time::float)*90 ELSE 0 END::numeric,3) AS xa90
            FROM rosters r
            JOIN matchcalendar mc ON mc.id=r.match_id
            WHERE r.player=:player AND mc.is_completed=true {league_clause}
            GROUP BY UPPER(r.position) ORDER BY xg DESC
        """
    else:  # season (default) — also handles shot_zones and shot_types tabs
        sql_str = f"""
            WITH ps AS (
                SELECT CASE
                           WHEN mc.match_datetime >= '2025-08-01' THEN '2025/26'
                           WHEN mc.match_datetime >= '2024-07-01' THEN '2024/25'
                           WHEN mc.match_datetime >= '2023-07-01' THEN '2023/24'
                           WHEN mc.match_datetime >= '2022-07-01' THEN '2022/23'
                           ELSE 'Older'
                       END AS season_label,
                       CASE WHEN r.team_type ILIKE 'h%%'
                            THEN mc.home_team_id ELSE mc.away_team_id END AS team_id,
                       mc.match_datetime,
                       r.match_id, r.goals::float AS goals, r.assists::float AS assists,
                       r.time::float AS minutes, r.shots::float AS shots,
                       r.key_passes::float AS key_passes,
                       r."xG"::float AS xg, r."xA"::float AS xa
                FROM rosters r
                JOIN matchcalendar mc ON mc.id=r.match_id
                WHERE r.player=:player AND mc.is_completed=true {league_clause}
            ),
            last_team AS (
                SELECT DISTINCT ON (season_label) season_label, team_id
                FROM ps ORDER BY season_label, match_datetime DESC
            )
            SELECT ps.season_label AS label,
                   t.name AS team_name,
                   COUNT(DISTINCT ps.match_id)::int AS matches,
                   ROUND(SUM(ps.minutes)::numeric,0)::int AS minutes,
                   SUM(ps.goals)::int AS goals,
                   SUM(ps.assists)::int AS assists,
                   ROUND(SUM(ps.shots)::numeric,0)::int AS shots,
                   ROUND(SUM(ps.xg)::numeric,2) AS xg,
                   ROUND(SUM(ps.xa)::numeric,2) AS xa,
                   ROUND(CASE WHEN SUM(ps.minutes)>0
                         THEN SUM(ps.shots)/SUM(ps.minutes)*90 ELSE 0 END::numeric,2) AS sh90,
                   ROUND(CASE WHEN SUM(ps.minutes)>0
                         THEN SUM(ps.key_passes)/SUM(ps.minutes)*90 ELSE 0 END::numeric,2) AS kp90,
                   ROUND(CASE WHEN SUM(ps.minutes)>0
                         THEN SUM(ps.xg)/SUM(ps.minutes)*90 ELSE 0 END::numeric,3) AS xg90,
                   ROUND(CASE WHEN SUM(ps.minutes)>0
                         THEN SUM(ps.xa)/SUM(ps.minutes)*90 ELSE 0 END::numeric,3) AS xa90
            FROM ps
            JOIN last_team lt ON lt.season_label=ps.season_label
            LEFT JOIN team t ON t.id=lt.team_id
            GROUP BY ps.season_label, t.name
            ORDER BY MIN(ps.match_datetime) DESC
        """

    async with engine.connect() as conn:
        res = await conn.execute(text(sql_str), params)
        rows = res.fetchall()
        cols = list(res.keys())
    return [dict(zip(cols, r)) for r in rows]


@router.get("/api/nerd-zone/player-shots")
async def nerd_zone_player_shots(
    player:     str       = Query(...),
    season:     str       = Query(default="2025/26"),
    league_ids: List[int] = Query(default=[]),
    situation:  str       = Query(default="All"),
    result:     str       = Query(default="All"),
):
    dr = season_range_sql(season)
    params: dict = {"player": player}
    clauses: list[str] = []

    if league_ids:
        clauses.append("AND mc.league_id = ANY(CAST(:lids AS int[]))")
        params["lids"] = league_ids
    if situation != "All":
        clauses.append("AND s.situation = :situation")
        params["situation"] = situation
    if result != "All":
        clauses.append("AND s.result = :result")
        params["result"] = result

    extra = " ".join(clauses)
    sql = text(f"""
        SELECT s."X"::float AS x, s."Y"::float AS y,
               s."xG"::float AS xg, s.result, s.situation,
               COALESCE(s.minute, 0)::int AS minute
        FROM shots s
        JOIN matchcalendar mc ON mc.id=s.match_id
        WHERE s.player=:player AND mc.is_completed=true
          AND {dr}
          {extra}
        ORDER BY mc.match_datetime
    """)
    async with engine.connect() as conn:
        res = await conn.execute(sql, params)
        rows = res.fetchall()
    return [{"x": float(r[0] or 0), "y": float(r[1] or 0), "xg": float(r[2] or 0),
             "result": r[3] or "", "situation": r[4] or "", "minute": int(r[5] or 0)}
            for r in rows]


@router.get("/api/nerd-zone/player-radar")
async def nerd_zone_player_radar(
    player:     str       = Query(...),
    season:     str       = Query(default="2025/26"),
    league_ids: List[int] = Query(default=[]),
):
    dr = season_range_sql(season)
    params: dict = {"player": player}
    league_clause = ""
    if league_ids:
        league_clause = "AND mc.league_id = ANY(CAST(:lids AS int[]))"
        params["lids"] = league_ids

    sql = text(f"""
        SELECT r.player AS name,
               ROUND((SUM(r."xG"::float)        /NULLIF(SUM(r.time::float),0)*90)::numeric,3) AS xG_p90,
               ROUND((SUM(r."xA"::float)        /NULLIF(SUM(r.time::float),0)*90)::numeric,3) AS xA_p90,
               ROUND((SUM(r.shots::float)       /NULLIF(SUM(r.time::float),0)*90)::numeric,3) AS shots_p90,
               ROUND((SUM(r.key_passes::float)  /NULLIF(SUM(r.time::float),0)*90)::numeric,3) AS key_passes_p90,
               ROUND((SUM(r."xGChain"::float)   /NULLIF(SUM(r.time::float),0)*90)::numeric,3) AS xGChain_p90,
               ROUND((SUM(r."xGBuildup"::float) /NULLIF(SUM(r.time::float),0)*90)::numeric,3) AS xGBuildup_p90,
               ROUND((SUM(r.goals::float)       /NULLIF(SUM(r.time::float),0)*90)::numeric,3) AS goals_p90,
               ROUND((SUM(r.assists::float)     /NULLIF(SUM(r.time::float),0)*90)::numeric,3) AS assists_p90
        FROM rosters r
        JOIN matchcalendar mc ON mc.id=r.match_id
        WHERE r.player=:player AND mc.is_completed=true
          AND {dr}
          {league_clause}
        GROUP BY r.player
        HAVING SUM(r.time::float) > 0
    """)
    async with engine.connect() as conn:
        res = await conn.execute(sql, params)
        row = res.fetchone()
    if not row:
        return None
    keys = ["name","xG_p90","xA_p90","shots_p90","key_passes_p90","xGChain_p90","xGBuildup_p90","goals_p90","assists_p90"]
    return {k: (float(v) if v is not None and k != "name" else (v or "")) for k, v in zip(keys, row)}


# ---------------------------------------------------------------------------
# Lab endpoint
# ---------------------------------------------------------------------------

LAB_DIM_EXPR: dict[str, str] = {
    "season":    """CASE
        WHEN mc.match_datetime >= '2025-08-01' THEN '2025/26'
        WHEN mc.match_datetime >= '2024-07-01' THEN '2024/25'
        WHEN mc.match_datetime >= '2023-07-01' THEN '2023/24'
        ELSE 'Older'
    END""",
    "position":  "UPPER(r.position)",
    "home_away": "CASE WHEN r.team_type ILIKE 'h%%' THEN 'Home' ELSE 'Away' END",
    "situation": "s.situation",
    "timing":    """CASE WHEN s.minute BETWEEN 1 AND 15 THEN '1-15'
                        WHEN s.minute BETWEEN 16 AND 30 THEN '16-30'
                        WHEN s.minute BETWEEN 31 AND 45 THEN '31-45+'
                        WHEN s.minute BETWEEN 46 AND 60 THEN '46-60'
                        WHEN s.minute BETWEEN 61 AND 75 THEN '61-75'
                        ELSE '76+' END""",
    "zone":      """CASE
        WHEN s."X" > 0.942 AND s."Y" BETWEEN 0.365 AND 0.635 THEN 'Six Yard Box'
        WHEN s."X" > 0.83  AND s."Y" BETWEEN 0.21  AND 0.79  THEN 'Penalty Area'
        ELSE 'Outside Box'
    END""",
    "result":    "s.result",
}

LAB_MET_EXPR: dict[str, str] = {
    "apps":        "COUNT(DISTINCT r.match_id)::int",
    "minutes":     "ROUND(SUM(r.time::float)::numeric,0)::int",
    "goals":       "SUM(r.goals::float)::int",
    "assists":     "SUM(r.assists::float)::int",
    "shots":       "ROUND(SUM(r.shots::float)::numeric,0)::int",
    "key_passes":  "ROUND(SUM(r.key_passes::float)::numeric,0)::int",
    "xg":          'ROUND(SUM(r."xG"::float)::numeric,2)',
    "xa":          'ROUND(SUM(r."xA"::float)::numeric,2)',
    "xgchain":     'ROUND(SUM(r."xGChain"::float)::numeric,2)',
    "xgbuildup":   'ROUND(SUM(r."xGBuildup"::float)::numeric,2)',
    "xg90":        'ROUND(SUM(r."xG"::float)/NULLIF(SUM(r.time::float),0)*90::numeric,3)',
    "xa90":        'ROUND(SUM(r."xA"::float)/NULLIF(SUM(r.time::float),0)*90::numeric,3)',
    "g90":         "ROUND(SUM(r.goals::float)/NULLIF(SUM(r.time::float),0)*90::numeric,3)",
    "sh90":        "ROUND(SUM(r.shots::float)/NULLIF(SUM(r.time::float),0)*90::numeric,3)",
    "kp90":        "ROUND(SUM(r.key_passes::float)/NULLIF(SUM(r.time::float),0)*90::numeric,3)",
    "shot_xg_sum": 'ROUND(SUM(s."xG"::float)::numeric,2)',
    "shot_goals":  "SUM(CASE WHEN s.result='Goal' THEN 1 ELSE 0 END)::int",
}

SHOT_DIMS_LAB = {"situation", "timing", "zone", "result"}
SHOT_METS_LAB = {"shot_xg_sum", "shot_goals"}


@router.get("/api/nerd-zone/lab")
async def nerd_zone_lab(
    entity:      str       = Query(default="player", pattern="^(player|team)$"),
    dimensions:  List[str] = Query(default=["season"]),
    metrics:     List[str] = Query(default=["goals","xg"]),
    league_ids:  List[int] = Query(default=[1]),
    season:      str       = Query(default="2025/26"),
    min_minutes: int       = Query(default=0, ge=0),
):
    dr = season_range_sql(season)
    params: dict = {"min_min": min_minutes}

    valid_dims = [d for d in dimensions if d in LAB_DIM_EXPR]
    valid_mets = [m for m in metrics   if m in LAB_MET_EXPR]
    if not valid_dims or not valid_mets:
        raise HTTPException(400, "Invalid dimensions or metrics")

    needs_shots = (any(d in SHOT_DIMS_LAB for d in valid_dims) or
                   any(m in SHOT_METS_LAB for m in valid_mets))

    dim_selects = ", ".join(f"{LAB_DIM_EXPR[d]} AS {d}" for d in valid_dims)
    met_selects = ", ".join(f"{LAB_MET_EXPR[m]} AS {m}" for m in valid_mets)
    group_by    = ", ".join(str(i+1) for i in range(len(valid_dims)))

    if entity == "player":
        entity_select = "r.player AS entity_name"
        entity_group  = "r.player"
    else:
        entity_select = "(CASE WHEN r.team_type ILIKE 'h%%' THEN mc.home_team_id ELSE mc.away_team_id END)::text AS entity_name"
        entity_group  = "CASE WHEN r.team_type ILIKE 'h%%' THEN mc.home_team_id ELSE mc.away_team_id END"

    shots_join = "LEFT JOIN shots s ON s.match_id = mc.id AND s.player = r.player" if needs_shots else ""

    league_clause = ""
    if league_ids:
        league_clause = "AND mc.league_id = ANY(CAST(:lids AS int[]))"
        params["lids"] = league_ids

    sql_str = f"""
        SELECT {entity_select}, {dim_selects}, {met_selects}
        FROM rosters r
        JOIN matchcalendar mc ON mc.id=r.match_id
        {shots_join}
        WHERE mc.is_completed=true
          AND {dr}
          {league_clause}
        GROUP BY {entity_group}, {group_by}
        HAVING SUM(r.time::float) >= :min_min
        ORDER BY 1
    """
    async with engine.connect() as conn:
        res = await conn.execute(text(sql_str), params)
        rows = res.fetchall()
        col_names = list(res.keys())

    return {"columns": col_names, "rows": [dict(zip(col_names, r)) for r in rows]}
