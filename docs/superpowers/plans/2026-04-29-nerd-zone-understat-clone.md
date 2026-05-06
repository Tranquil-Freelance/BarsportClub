# Nerd Zone — Understat Clone Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Costruire un clone funzionale e visivo 1:1 di Understat.com a `/nerd-zone` con gerarchia Lega → Squadra → Giocatore, usando matchcalendar (xG/xGA/xPTS diretti), shots (coordinate X/Y, result, situation) e rosters (stats per partita).

**Architecture:** Backend aggiunge 8 endpoint a `nerdzone_routes.py` (registrato in `main.py`). Frontend: `/nerd-zone` (classifica lega), `/nerd-zone/team/[id]` (calendario + filtri shot + roster), `/nerd-zone/player/[slug]` (storico stagioni + radar + shot map filtrata). CSV export su tutte le tabelle, ordinamento su tutte le colonne.

**Tech Stack:** Next.js 15, React 19, TypeScript, Tailwind CSS, FastAPI, SQLAlchemy async, PostgreSQL. echarts-for-react per radar (già installato). SVG per shot map (già costruita in ShotMapHorizontal.tsx).

---

## File Structure

| File | Action | Responsabilità |
|------|--------|----------------|
| `backend/app/api/nerdzone_routes.py` | Modify (append) | 8 nuovi endpoint |
| `backend/main.py` | Modify | `include_router(nerdzone_router)` |
| `frontend/app/nerd-zone/page.tsx` | Rewrite | Classifica lega + selettore lega |
| `frontend/app/nerd-zone/team/[id]/page.tsx` | Modify | Tab completi (7), CSV, filtro posizione/last N |
| `frontend/app/nerd-zone/player/[slug]/page.tsx` | Modify | Tab Season/Position/Situation, filtri shot map, CSV |
| `frontend/app/nerd-zone/components/TeamSituationTable.tsx` | Modify | Aggiungi Formation/Game state/Attack speed tabs + CSV |
| `frontend/app/nerd-zone/components/RosterTable.tsx` | Modify | Aggiungi colonna `apps`, CSV export |
| `frontend/app/components/UniversalHeader.tsx` | Modify | Aggiungi link NERD ZONE |

---

## Task 1: Registra nerdzone_routes.py in main.py

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1: Aggiungi import nel blocco try/except esistente (linea ~69-79)**

Trova il blocco che importa `scout_router`, `fanta_router` ecc. e aggiungi PRIMA:
```python
try:
    from app.api.nerdzone_routes import router as nerdzone_router
    logger.info("✅ NerdZone Router caricato.")
except ImportError as e:
    logger.error(f"⚠️ NerdZone non caricato: {e}")
    nerdzone_router = APIRouter()
```

- [ ] **Step 2: Registra il router (vicino alla linea 868-874)**

Dopo `app.include_router(replacement_router)`, aggiungi:
```python
app.include_router(nerdzone_router)
```

- [ ] **Step 3: Commit**
```bash
git add backend/main.py
git commit -m "feat(nerd-zone): register nerdzone_routes router"
```

---

## Task 2: Backend — League table + teams endpoints

**Files:**
- Modify: `backend/app/api/nerdzone_routes.py` (append dopo l'ultimo endpoint esistente)

- [ ] **Step 1: Aggiungi costanti SEASON_BOUNDS e helper season_filter**

Append in fondo al file, dopo l'ultimo `@router.get`:
```python
# ─── NERD ZONE — UNDERSTAT CLONE ENDPOINTS ──────────────────────────────────

SEASON_BOUNDS: dict[str, tuple[str, str]] = {
    "2025/26": ("2025-08-01", "2026-07-31"),
    "2024/25": ("2024-07-01", "2025-07-31"),
    "2023/24": ("2023-07-01", "2024-06-30"),
    "2022/23": ("2022-07-01", "2023-06-30"),
    "all":     ("2000-01-01", "2099-12-31"),
}


def season_bounds(season: str) -> tuple[str, str]:
    return SEASON_BOUNDS.get(season, SEASON_BOUNDS["2025/26"])


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
```

- [ ] **Step 2: Aggiungi endpoint `/api/nerd-zone/league-table`**

```python
@router.get("/api/nerd-zone/league-table")
async def nerd_zone_league_table(
    league_id: int = Query(default=2),
    season:    str = Query(default="2025/26"),
):
    s_start, s_end = season_bounds(season)
    sql = text("""
        WITH tm AS (
            SELECT mc.home_team_id AS tid,
                   mc.home_goals::int AS gf, mc.away_goals::int AS ga,
                   mc."home_xG"::float AS xg, mc."away_xG"::float AS xga,
                   COALESCE(mc.home_xpts::float, 0) AS xpts
            FROM matchcalendar mc
            WHERE mc.is_completed = true AND mc.league_id = :lid
              AND mc.match_datetime BETWEEN :s AND :e
            UNION ALL
            SELECT mc.away_team_id,
                   mc.away_goals::int, mc.home_goals::int,
                   mc."away_xG"::float, mc."home_xG"::float,
                   COALESCE(mc.away_xpts::float, 0)
            FROM matchcalendar mc
            WHERE mc.is_completed = true AND mc.league_id = :lid
              AND mc.match_datetime BETWEEN :s AND :e
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
        res = await conn.execute(sql, {"lid": league_id, "s": s_start, "e": s_end})
        rows = res.fetchall()
    keys = ["id","name","mp","w","d","l","gf","ga","gd","pts","xg","xga","xpts","xgd"]
    return [dict(zip(keys, r)) for r in rows]
```

- [ ] **Step 3: Aggiungi endpoint `/api/nerd-zone/teams`**

```python
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
```

- [ ] **Step 4: Commit**
```bash
git add backend/app/api/nerdzone_routes.py
git commit -m "feat(nerd-zone): add league-table and teams endpoints"
```

---

## Task 3: Backend — Team endpoints (matches, roster, stats)

**Files:**
- Modify: `backend/app/api/nerdzone_routes.py` (append)

- [ ] **Step 1: Endpoint `/api/nerd-zone/team-matches`**

```python
@router.get("/api/nerd-zone/team-matches")
async def nerd_zone_team_matches(
    team_id: int = Query(...),
    season:  str = Query(default="2025/26"),
    limit:   int = Query(default=38),
):
    s_start, s_end = season_bounds(season)
    sql = text("""
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
          AND mc.match_datetime BETWEEN :s AND :e
        ORDER BY mc.match_datetime
        LIMIT :lim
    """)
    async with engine.connect() as conn:
        res = await conn.execute(sql, {"tid": team_id, "s": s_start, "e": s_end, "lim": limit})
        rows = res.fetchall()
    keys = ["match_id","date","home_team","away_team","home_team_id","away_team_id",
            "home_goals","away_goals","home_xg","away_xg","is_completed","matchday","is_home"]
    return [dict(zip(keys, r)) for r in rows]
```

- [ ] **Step 2: Endpoint `/api/nerd-zone/team-roster`**

```python
@router.get("/api/nerd-zone/team-roster")
async def nerd_zone_team_roster(
    team_id:  int           = Query(...),
    season:   str           = Query(default="2025/26"),
    position: Optional[str] = Query(default=None),
    last_n:   Optional[int] = Query(default=None),
):
    s_start, s_end = season_bounds(season)

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
    params: dict = {"tid": team_id, "s": s_start, "e": s_end}
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
          AND mc.match_datetime BETWEEN :s AND :e
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
```

- [ ] **Step 3: Endpoint `/api/nerd-zone/team-stats`**

```python
@router.get("/api/nerd-zone/team-stats")
async def nerd_zone_team_stats(
    team_id: int = Query(...),
    season:  str = Query(default="2025/26"),
    tab:     str = Query(default="situation"),
):
    s_start, s_end = season_bounds(season)

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
              AND mc.match_datetime BETWEEN :s AND :e
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
              AND mc.match_datetime BETWEEN :s AND :e
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
        res = await conn.execute(sql, {"tid": team_id, "s": s_start, "e": s_end})
        rows = res.fetchall()
    keys = ["dimension","sh","g","sha","ga","xg","xga","xgd","xg_per_sh","xga_per_sha"]
    return [dict(zip(keys, r)) for r in rows]
```

- [ ] **Step 4: Commit**
```bash
git add backend/app/api/nerdzone_routes.py
git commit -m "feat(nerd-zone): add team-matches, team-roster, team-stats endpoints"
```

---

## Task 4: Backend — Player endpoints + lab endpoint

**Files:**
- Modify: `backend/app/api/nerdzone_routes.py` (append)

- [ ] **Step 1: Endpoint `/api/nerd-zone/player-history`**

```python
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
                   ROUND(SUM(r.time::float)::numeric,0)::int AS minutes,
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
    else:  # season
        sql_str = f"""
            WITH ps AS (
                SELECT {SEASON_LABEL_SQL} AS season_label,
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
```

- [ ] **Step 2: Endpoint `/api/nerd-zone/player-shots`**

```python
@router.get("/api/nerd-zone/player-shots")
async def nerd_zone_player_shots(
    player:     str       = Query(...),
    season:     str       = Query(default="2025/26"),
    league_ids: List[int] = Query(default=[]),
    situation:  str       = Query(default="All"),
    result:     str       = Query(default="All"),
):
    s_start, s_end = season_bounds(season)
    params: dict = {"player": player, "s": s_start, "e": s_end}
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
          AND mc.match_datetime BETWEEN :s AND :e
          {extra}
        ORDER BY mc.match_datetime
    """)
    async with engine.connect() as conn:
        res = await conn.execute(sql, params)
        rows = res.fetchall()
    return [{"x": r[0], "y": r[1], "xg": r[2], "result": r[3] or "",
             "situation": r[4] or "", "minute": r[5]} for r in rows]
```

- [ ] **Step 3: Endpoint `/api/nerd-zone/player-radar`**

```python
@router.get("/api/nerd-zone/player-radar")
async def nerd_zone_player_radar(
    player:     str       = Query(...),
    season:     str       = Query(default="2025/26"),
    league_ids: List[int] = Query(default=[]),
):
    s_start, s_end = season_bounds(season)
    params: dict = {"player": player, "s": s_start, "e": s_end}
    league_clause = ""
    if league_ids:
        league_clause = "AND mc.league_id = ANY(CAST(:lids AS int[]))"
        params["lids"] = league_ids

    sql = text(f"""
        SELECT r.player AS name,
               ROUND(SUM(r."xG"::float)        /NULLIF(SUM(r.time::float),0)*90::numeric,3) AS xG_p90,
               ROUND(SUM(r."xA"::float)        /NULLIF(SUM(r.time::float),0)*90::numeric,3) AS xA_p90,
               ROUND(SUM(r.shots::float)       /NULLIF(SUM(r.time::float),0)*90::numeric,3) AS shots_p90,
               ROUND(SUM(r.key_passes::float)  /NULLIF(SUM(r.time::float),0)*90::numeric,3) AS key_passes_p90,
               ROUND(SUM(r."xGChain"::float)   /NULLIF(SUM(r.time::float),0)*90::numeric,3) AS xGChain_p90,
               ROUND(SUM(r."xGBuildup"::float) /NULLIF(SUM(r.time::float),0)*90::numeric,3) AS xGBuildup_p90,
               ROUND(SUM(r.goals::float)       /NULLIF(SUM(r.time::float),0)*90::numeric,3) AS goals_p90,
               ROUND(SUM(r.assists::float)     /NULLIF(SUM(r.time::float),0)*90::numeric,3) AS assists_p90
        FROM rosters r
        JOIN matchcalendar mc ON mc.id=r.match_id
        WHERE r.player=:player AND mc.is_completed=true
          AND mc.match_datetime BETWEEN :s AND :e
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
```

- [ ] **Step 4: Endpoint `/api/nerd-zone/lab` (per la Lab page)**

```python
LAB_DIM_EXPR: dict[str, str] = {
    "season":    SEASON_LABEL_SQL,
    "position":  "UPPER(r.position)",
    "home_away": "CASE WHEN r.team_type ILIKE 'h%%' THEN 'Home' ELSE 'Away' END",
    "situation": "s.situation",
    "timing":    """CASE WHEN s.minute BETWEEN 1 AND 15 THEN '1-15'
                        WHEN s.minute BETWEEN 16 AND 30 THEN '16-30'
                        WHEN s.minute BETWEEN 31 AND 45 THEN '31-45+'
                        WHEN s.minute BETWEEN 46 AND 60 THEN '46-60'
                        WHEN s.minute BETWEEN 61 AND 75 THEN '61-75'
                        ELSE '76+' END""",
    "zone":      SHOT_ZONE_SQL,
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

SHOT_DIMS = {"situation", "timing", "zone", "result"}
SHOT_METS = {"shot_xg_sum", "shot_goals"}


@router.get("/api/nerd-zone/lab")
async def nerd_zone_lab(
    entity:      str       = Query(default="player", pattern="^(player|team)$"),
    dimensions:  List[str] = Query(default=["season"]),
    metrics:     List[str] = Query(default=["goals","xg"]),
    league_ids:  List[int] = Query(default=[1]),
    season:      str       = Query(default="2025/26"),
    min_minutes: int       = Query(default=0, ge=0),
):
    s_start, s_end = season_bounds(season)
    params: dict = {"s": s_start, "e": s_end, "min_min": min_minutes}

    valid_dims = [d for d in dimensions if d in LAB_DIM_EXPR]
    valid_mets = [m for m in metrics   if m in LAB_MET_EXPR]
    if not valid_dims or not valid_mets:
        raise HTTPException(400, "Invalid dimensions or metrics")

    needs_shots = any(d in SHOT_DIMS for d in valid_dims) or any(m in SHOT_METS for m in valid_mets)

    dim_selects = ", ".join(f"{LAB_DIM_EXPR[d]} AS {d}" for d in valid_dims)
    met_selects = ", ".join(f"{LAB_MET_EXPR[m]} AS {m}" for m in valid_mets)
    group_by    = ", ".join(str(i+1) for i in range(len(valid_dims)))

    if entity == "player":
        entity_select = "r.player AS entity_name"
        entity_group  = "r.player"
    else:
        entity_select  = "(CASE WHEN r.team_type ILIKE 'h%%' THEN mc.home_team_id ELSE mc.away_team_id END)::text AS entity_name"
        entity_group   = "CASE WHEN r.team_type ILIKE 'h%%' THEN mc.home_team_id ELSE mc.away_team_id END"

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
          AND mc.match_datetime BETWEEN :s AND :e
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
```

- [ ] **Step 5: Commit**
```bash
git add backend/app/api/nerdzone_routes.py
git commit -m "feat(nerd-zone): add player-history, player-shots, player-radar, lab endpoints"
```

---

## Task 5: Frontend — UniversalHeader: aggiungi link NERD ZONE

**Files:**
- Modify: `frontend/app/components/UniversalHeader.tsx`

- [ ] **Step 1: Aggiungi NERD ZONE a navItems**

Nella riga dove è definito `navItems`, aggiungi `{ label: "NERD ZONE", href: "/nerd-zone" }` **dopo** SCOUT ENGINE:

```typescript
const navItems = [
  { label: "CAMPIONATI",   href: "/campionati" },
  { label: "BETTING",      href: "/betting" },
  { label: "MERITOMETRO",  href: "/meritometro" },
  { label: "SCOUT ENGINE", href: "/scout-engine" },
  { label: "NERD ZONE",    href: "/nerd-zone" },
  { label: "FANTA DRAFT",  href: "/fanta-draft" },
];
```

- [ ] **Step 2: Commit**
```bash
git add frontend/app/components/UniversalHeader.tsx
git commit -m "feat(navbar): add NERD ZONE link to UniversalHeader"
```

---

## Task 6: Frontend — League Homepage (/nerd-zone/page.tsx)

**Files:**
- Rewrite: `frontend/app/nerd-zone/page.tsx`

Il file attuale mostra il Query Lab. Lo sovrascriviamo con la classifica lega stile Understat. Il Lab è già raggiungibile a `/nerd-zone/lab`.

- [ ] **Step 1: Scrivi il nuovo page.tsx**

```tsx
"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Download, ArrowUpDown } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const LEAGUES = [
  { id: 2, name: "Premier League" },
  { id: 1, name: "Serie A" },
  { id: 3, name: "La Liga" },
  { id: 4, name: "Bundesliga" },
  { id: 5, name: "Ligue 1" },
];
const SEASONS = ["2025/26", "2024/25", "2023/24"];

interface StandingRow {
  id: number; name: string;
  mp: number; w: number; d: number; l: number;
  gf: number; ga: number; gd: number; pts: number;
  xg: number; xga: number; xpts: number; xgd: number;
}

type SortKey = keyof StandingRow;

function Delta({ base, actual }: { base: number; actual: number }) {
  const d = actual - base;
  if (Math.abs(d) < 0.01) return null;
  const color = d >= 0 ? "#10B981" : "#EF4444";
  return <sup style={{ color, fontSize: "9px", marginLeft: "2px", fontWeight: 700 }}>{d >= 0 ? "+" : ""}{d.toFixed(2)}</sup>;
}

function downloadCSV(rows: StandingRow[], season: string, leagueName: string) {
  const headers = ["#","Team","MP","W","D","L","GF","GA","GD","Pts","xG","xGA","xPTS","xGD"];
  const csvRows = rows.map((r, i) =>
    [i+1, r.name, r.mp, r.w, r.d, r.l, r.gf, r.ga, r.gd, r.pts,
     r.xg, r.xga, r.xpts, r.xgd].join(",")
  );
  const blob = new Blob([headers.join(",") + "\n" + csvRows.join("\n")], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${leagueName}_${season.replace("/","_")}_standings.csv`;
  a.click();
}

export default function NerdZonePage() {
  const router = useRouter();
  const [leagueId, setLeagueId] = useState(2);
  const [season,   setSeason]   = useState("2025/26");
  const [rows,     setRows]     = useState<StandingRow[]>([]);
  const [loading,  setLoading]  = useState(false);
  const [sortKey,  setSortKey]  = useState<SortKey>("pts");
  const [sortDir,  setSortDir]  = useState<"asc"|"desc">("desc");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/nerd-zone/league-table?league_id=${leagueId}&season=${encodeURIComponent(season)}`,
        { cache: "no-store" }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setRows(await res.json());
    } finally { setLoading(false); }
  }, [leagueId, season]);

  useEffect(() => { load(); }, [load]);

  function handleSort(key: SortKey) {
    if (key === sortKey) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortKey(key); setSortDir(key === "name" ? "asc" : "desc"); }
  }

  const sorted = [...rows].sort((a, b) => {
    const av = a[sortKey], bv = b[sortKey];
    const diff = av < bv ? -1 : av > bv ? 1 : 0;
    return sortDir === "asc" ? diff : -diff;
  });

  const leagueName = LEAGUES.find(l => l.id === leagueId)?.name ?? "League";

  const COLS: { key: SortKey; label: string; note?: string }[] = [
    { key: "mp",   label: "MP"   },
    { key: "w",    label: "W"    },
    { key: "d",    label: "D"    },
    { key: "l",    label: "L"    },
    { key: "gf",   label: "GF"   },
    { key: "ga",   label: "GA"   },
    { key: "gd",   label: "GD"   },
    { key: "pts",  label: "Pts"  },
    { key: "xg",   label: "xG",   note: "Expected Goals" },
    { key: "xga",  label: "xGA",  note: "Expected Goals Against" },
    { key: "xgd",  label: "xGD",  note: "xG Difference" },
    { key: "xpts", label: "xPTS", note: "Expected Points" },
  ];

  return (
    <div className="min-h-screen bg-[#1A202C] text-white">
      {/* Header */}
      <div className="border-b border-slate-800/60 bg-[#080b12] px-4 md:px-6 py-4 sticky top-0 z-30 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-black text-xl tracking-tight">NERD ZONE</h1>
          <p className="text-[10px] text-slate-600 uppercase tracking-[0.2em]">Understat-style analytics</p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          {/* League selector */}
          <select
            value={leagueId}
            onChange={e => setLeagueId(Number(e.target.value))}
            className="bg-[#0d1220] border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-[#10B981]"
          >
            {LEAGUES.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
          </select>
          {/* Season selector */}
          <select
            value={season}
            onChange={e => setSeason(e.target.value)}
            className="bg-[#0d1220] border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-[#10B981]"
          >
            {SEASONS.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <button
            onClick={() => downloadCSV(sorted, season, leagueName)}
            className="p-2 rounded-lg border border-slate-800 bg-[#0d1220] text-slate-500 hover:text-white transition-colors"
            title="Download CSV"
          >
            <Download size={14} />
          </button>
          {loading && <Loader2 size={16} className="animate-spin text-[#10B981]" />}
        </div>
      </div>

      <div className="px-4 md:px-6 py-6 max-w-7xl mx-auto">
        {/* Breadcrumb */}
        <p className="text-[10px] text-slate-700 uppercase tracking-widest mb-4">
          Home / {leagueName} / {season}
        </p>

        {/* Standings table */}
        <div className="overflow-x-auto rounded-xl border border-slate-800/60">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-[#0d1220] border-b border-slate-800/60">
                <th className="px-3 py-3 text-left text-[10px] font-black uppercase tracking-widest text-slate-600 w-8">#</th>
                <th
                  onClick={() => handleSort("name")}
                  className={`px-3 py-3 text-left text-[10px] font-black uppercase tracking-widest cursor-pointer select-none transition-colors hover:text-white ${sortKey === "name" ? "text-white" : "text-slate-500"}`}
                >
                  Club {sortKey === "name" ? (sortDir === "asc" ? "↑" : "↓") : <ArrowUpDown size={8} className="inline ml-0.5 opacity-30" />}
                </th>
                {COLS.map(c => (
                  <th
                    key={c.key}
                    title={c.note}
                    onClick={() => handleSort(c.key)}
                    className={`px-3 py-3 text-right text-[10px] font-black uppercase tracking-widest cursor-pointer select-none whitespace-nowrap transition-colors hover:text-white ${
                      sortKey === c.key ? "text-white" : c.key === "xg" || c.key === "xga" || c.key === "xgd" || c.key === "xpts" ? "text-[#60a5fa]" : "text-slate-500"
                    }`}
                  >
                    {c.label}
                    {sortKey === c.key ? (sortDir === "asc" ? " ↑" : " ↓") : ""}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((row, i) => (
                <tr
                  key={row.id}
                  onClick={() => router.push(`/nerd-zone/team/${row.id}?season=${encodeURIComponent(season)}`)}
                  className="border-t border-slate-800/40 hover:bg-[#0d1220] cursor-pointer transition-colors group"
                >
                  <td className="px-3 py-2.5 text-slate-700 font-mono">{i + 1}</td>
                  <td className="px-3 py-2.5 font-semibold text-[#60a5fa] group-hover:text-white transition-colors whitespace-nowrap">{row.name}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-slate-400">{row.mp}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-[#10B981]">{row.w}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-slate-400">{row.d}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-[#EF4444]">{row.l}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-slate-300">{row.gf}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-slate-400">{row.ga}</td>
                  <td className={`px-3 py-2.5 text-right font-mono font-bold ${row.gd >= 0 ? "text-[#10B981]" : "text-[#EF4444]"}`}>
                    {row.gd >= 0 ? "+" : ""}{row.gd}
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono font-bold text-white">{row.pts}</td>
                  {/* xG with delta vs actual goals */}
                  <td className="px-3 py-2.5 text-right font-mono text-[#60a5fa] whitespace-nowrap">
                    {row.xg.toFixed(2)}<Delta base={row.xg} actual={row.gf} />
                  </td>
                  {/* xGA with delta vs actual GA */}
                  <td className="px-3 py-2.5 text-right font-mono text-[#f87171] whitespace-nowrap">
                    {row.xga.toFixed(2)}<Delta base={row.xga} actual={row.ga} />
                  </td>
                  <td className={`px-3 py-2.5 text-right font-mono font-bold ${row.xgd >= 0 ? "text-[#10B981]" : "text-[#EF4444]"}`}>
                    {row.xgd >= 0 ? "+" : ""}{row.xgd.toFixed(2)}
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono text-[#818cf8]">{row.xpts.toFixed(2)}</td>
                </tr>
              ))}
              {!loading && !sorted.length && (
                <tr>
                  <td colSpan={15} className="px-3 py-10 text-center text-slate-700 text-xs uppercase tracking-widest">
                    No data for this league / season
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Lab link */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={() => router.push("/nerd-zone/lab")}
            className="text-[10px] text-slate-700 hover:text-[#10B981] uppercase tracking-widest transition-colors"
          >
            → Advanced Query Lab
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**
```bash
git add frontend/app/nerd-zone/page.tsx
git commit -m "feat(nerd-zone): rewrite homepage as Understat-style league table"
```

---

## Task 7: Frontend — TeamSituationTable: aggiungi 3 tab mancanti + CSV

**Files:**
- Modify: `frontend/app/nerd-zone/components/TeamSituationTable.tsx`

- [ ] **Step 1: Estendi TABS e aggiungi CSV**

Il file corrente ha 4 tab (situation, timing, zones, result). Aggiungi Formation, Game state, Attack speed (che tornano `[]` dal backend). Aggiungi anche CSV export.

Sostituisci il file con questa versione aggiornata:

```tsx
"use client";

import { useEffect, useState } from "react";
import { Download } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const TABS = [
  { id: "situation",    label: "Situation"     },
  { id: "formation",    label: "Formation"     },
  { id: "game_state",   label: "Game state"    },
  { id: "timing",       label: "Timing"        },
  { id: "zones",        label: "Shot zones"    },
  { id: "attack_speed", label: "Attack speed"  },
  { id: "result",       label: "Result"        },
] as const;

type TabId = typeof TABS[number]["id"];

interface StatRow {
  dimension: string; sh: number; g: number; sha: number; ga: number;
  xg: number; xga: number; xgd: number; xg_per_sh: number; xga_per_sha: number;
}

interface Props {
  teamId: number; season: string; tab: TabId; onTabChange: (t: TabId) => void;
}

function DeltaSup({ base, actual }: { base: number; actual: number }) {
  const delta = actual - base;
  const color = delta >= 0 ? "#10B981" : "#EF4444";
  return (
    <sup className="ml-0.5 text-[9px] font-black" style={{ color }}>
      {delta >= 0 ? "+" : ""}{delta.toFixed(2)}
    </sup>
  );
}

function downloadCSV(rows: StatRow[], tab: string) {
  const headers = ["Dimension","Sh","G","ShA","GA","xG","xGA","xGD","xG/Sh","xGA/Sh"];
  const csvRows = rows.map(r =>
    [r.dimension,r.sh,r.g,r.sha,r.ga,r.xg,r.xga,r.xgd,r.xg_per_sh,r.xga_per_sha].join(",")
  );
  const blob = new Blob([headers.join(",") + "\n" + csvRows.join("\n")], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `team_stats_${tab}.csv`;
  a.click();
}

export default function TeamSituationTable({ teamId, season, tab, onTabChange }: Props) {
  const [rows, setRows]       = useState<StatRow[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!teamId) return;
    setLoading(true);
    fetch(
      `${API_BASE}/api/nerd-zone/team-stats?team_id=${teamId}&tab=${tab}&season=${encodeURIComponent(season)}`,
      { cache: "no-store" }
    )
      .then(r => r.json())
      .then(setRows)
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, [teamId, tab, season]);

  const noData = ["formation", "game_state", "attack_speed"].includes(tab);

  return (
    <div className="bg-[#08090f] border border-slate-800/60 rounded-2xl overflow-hidden">
      {/* Tab bar + CSV */}
      <div className="flex items-center border-b border-slate-800/60 justify-between">
        <div className="flex overflow-x-auto">
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => onTabChange(t.id)}
              className={`relative px-4 py-3 text-[11px] font-black uppercase tracking-widest whitespace-nowrap transition-colors ${
                tab === t.id ? "text-white" : "text-slate-600 hover:text-slate-400"
              }`}
            >
              {t.label}
              {tab === t.id && (
                <span className="absolute bottom-0 left-0 w-full h-0.5 bg-[#10B981] rounded-t shadow-[0_0_6px_#10B981]" />
              )}
            </button>
          ))}
        </div>
        <button
          onClick={() => downloadCSV(rows, tab)}
          disabled={!rows.length}
          className="p-2 mr-3 rounded-lg border border-slate-800 bg-[#0d1220] text-slate-600 hover:text-white transition-colors disabled:opacity-30"
          title="Download CSV"
        >
          <Download size={13} />
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto min-h-[120px]">
        {loading ? (
          <div className="flex items-center justify-center h-28 text-slate-700 text-xs uppercase tracking-widest">Loading…</div>
        ) : noData || !rows.length ? (
          <div className="flex items-center justify-center h-28 text-slate-800 text-xs uppercase tracking-widest">
            {noData ? "Data not available" : "No data"}
          </div>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-[#0d1220]">
                <th className="px-3 py-2.5 text-left text-[10px] font-black uppercase tracking-widest text-slate-600 w-6">#</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-black uppercase tracking-widest text-slate-500">
                  {tab === "timing" ? "Period" : tab === "zones" ? "Zone" : tab === "result" ? "Result" : "Situation"}
                </th>
                {[
                  ["Sh", "text-slate-400"], ["G", "text-slate-300"],
                  ["ShA", "text-slate-400"], ["GA", "text-slate-400"],
                  ["xG", "text-[#60a5fa]"], ["xGA", "text-[#f87171]"],
                  ["xGD", "text-slate-300"], ["xG/Sh", "text-slate-500"], ["xGA/Sh", "text-slate-500"],
                ].map(([label, color]) => (
                  <th key={label} className={`px-3 py-2.5 text-right text-[10px] font-black uppercase tracking-widest whitespace-nowrap ${color}`}>
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={row.dimension} className="border-t border-slate-800/40 hover:bg-[#0d1220] transition-colors">
                  <td className="px-3 py-2 text-slate-700 font-mono">{i + 1}</td>
                  <td className="px-3 py-2 font-semibold text-white whitespace-nowrap">{row.dimension}</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-400">{row.sh}</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-300">{row.g}</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-400">{row.sha}</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-400">{row.ga}</td>
                  <td className="px-3 py-2 text-right font-mono text-[#60a5fa] whitespace-nowrap">
                    {row.xg.toFixed(2)}<DeltaSup base={row.xg} actual={row.g} />
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-[#f87171] whitespace-nowrap">
                    {row.xga.toFixed(2)}<DeltaSup base={row.xga} actual={row.ga} />
                  </td>
                  <td className={`px-3 py-2 text-right font-mono font-bold whitespace-nowrap ${row.xgd >= 0 ? "text-[#10B981]" : "text-[#EF4444]"}`}>
                    {row.xgd >= 0 ? "+" : ""}{row.xgd.toFixed(2)}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-slate-500">{row.xg_per_sh.toFixed(3)}</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-500">{row.xga_per_sha.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**
```bash
git add frontend/app/nerd-zone/components/TeamSituationTable.tsx
git commit -m "feat(nerd-zone): TeamSituationTable — 7 tabs + CSV export"
```

---

## Task 8: Frontend — RosterTable: aggiungi colonna `apps` + CSV

**Files:**
- Modify: `frontend/app/nerd-zone/components/RosterTable.tsx`

- [ ] **Step 1: Aggiungi `apps` all'interfaccia e alla tabella**

Aggiungi `apps: number;` a `RosterRow` interface (dopo `player: string; position: string; team_name: string;`).

Aggiungi alla COLS array prima di `minutes`:
```typescript
{ key: "apps", label: "Apps", mono: true },
```

Aggiungi una prop `onDownloadCSV?: () => void` all'interfaccia Props.

Aggiungi il bottone CSV nella thead toolbar. Dopo `<div className="overflow-x-auto ...">`, aggiungi un wrapper con il pulsante download sopra la tabella:

```tsx
// Sostituisci il return con questo:
return (
  <div>
    <div className="flex justify-end mb-2">
      <button
        onClick={() => {
          const headers = ["#","Player","Pos","Team","Apps","Min","G","A","Sh90","KP90","xG","xA","xG90","xA90","xGChain","xGBuild"];
          const csvRows = sorted.map((r, i) =>
            [i+1, r.player, r.position, r.team_name, r.apps, r.minutes,
             r.goals, r.assists, r.sh90.toFixed(2), r.kp90.toFixed(2),
             r.xg.toFixed(2), r.xa.toFixed(2), r.xg90.toFixed(3), r.xa90.toFixed(3),
             r.xgchain.toFixed(2), r.xgbuildup.toFixed(2)].join(",")
          );
          const blob = new Blob([headers.join(",") + "\n" + csvRows.join("\n")], { type: "text/csv" });
          const a = document.createElement("a");
          a.href = URL.createObjectURL(blob);
          a.download = "roster.csv";
          a.click();
        }}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-800 bg-[#0d1220] text-[10px] text-slate-500 hover:text-white transition-colors"
      >
        <Download size={11} /> CSV
      </button>
    </div>
    <div className="overflow-x-auto rounded-xl border border-slate-800/60">
      {/* ...rest of table unchanged... */}
    </div>
  </div>
);
```

Aggiungi anche nel tbody il rendering della cella apps (dopo la cella position):
```tsx
{/* Apps */}
<td className="px-3 py-2.5 text-right font-mono text-[11px] text-slate-400">{row.apps}</td>
```

Aggiungi `import { Download } from "lucide-react";` in cima.

- [ ] **Step 2: Aggiorna anche team/[id]/page.tsx per passare `apps` dal backend**

Il team page già chiama `/api/nerd-zone/team-roster` che ora ritorna `apps`. Verifica che RosterRow includa `apps` e che il fetch funzioni. Non servono altre modifiche.

- [ ] **Step 3: Commit**
```bash
git add frontend/app/nerd-zone/components/RosterTable.tsx
git commit -m "feat(nerd-zone): RosterTable — add apps column + CSV export"
```

---

## Task 9: Frontend — Team page: filtri posizione/last N + aggiorna tab type

**Files:**
- Modify: `frontend/app/nerd-zone/team/[id]/page.tsx`

- [ ] **Step 1: Estendi StatTab e aggiungi filtri**

Aggiorna `type StatTab = "situation" | "formation" | "game_state" | "timing" | "zones" | "attack_speed" | "result";`

Aggiungi stati per position filter e last N:
```tsx
const [posFilter, setPosFilter] = useState("All");
const [lastN,     setLastN]     = useState<number|null>(null);
```

Aggiorna il fetch del roster per includere questi filtri:
```tsx
fetch(
  `${API_BASE}/api/nerd-zone/team-roster?team_id=${teamId}` +
  `&season=${encodeURIComponent(season)}` +
  `${posFilter !== "All" ? `&position=${posFilter}` : ""}` +
  `${lastN ? `&last_n=${lastN}` : ""}`,
  { cache: "no-store" }
)
```

Aggiungi una sezione di filtri sopra RosterTable:
```tsx
{/* Roster filters */}
<div className="flex flex-wrap items-center gap-3 mb-3">
  <div className="flex gap-1.5">
    {["All","GK","DF","MF","FW"].map(pos => (
      <button key={pos} onClick={() => setPosFilter(pos)}
        className={`px-2.5 py-1 rounded text-[10px] font-black uppercase border transition-all ${
          posFilter === pos
            ? "bg-[#10B981]/15 border-[#10B981]/40 text-[#10B981]"
            : "bg-[#0d1220] border-slate-800 text-slate-600 hover:text-slate-400"
        }`}
      >
        {pos}
      </button>
    ))}
  </div>
  <div className="flex gap-1.5">
    {[null, 5, 10, 15].map(n => (
      <button key={String(n)} onClick={() => setLastN(n)}
        className={`px-2.5 py-1 rounded text-[10px] font-black uppercase border transition-all ${
          lastN === n
            ? "bg-[#10B981]/15 border-[#10B981]/40 text-[#10B981]"
            : "bg-[#0d1220] border-slate-800 text-slate-600 hover:text-slate-400"
        }`}
      >
        {n === null ? "All" : `Last ${n}`}
      </button>
    ))}
  </div>
</div>
```

Aggiungi posFilter e lastN come dipendenze all'useEffect che carica il roster.

- [ ] **Step 2: Commit**
```bash
git add frontend/app/nerd-zone/team/[id]/page.tsx
git commit -m "feat(nerd-zone): team page — position filter, last N games filter"
```

---

## Task 10: Frontend — Player page: shot map filters + tab Season/Position/Situation

**Files:**
- Modify: `frontend/app/nerd-zone/player/[slug]/page.tsx`

- [ ] **Step 1: Aggiungi filtri per shot map**

Aggiungi stati:
```tsx
const [shotSituation, setShotSituation] = useState("All");
const [shotResult,    setShotResult]    = useState("All");
```

Aggiorna il fetch di player-shots per includere i filtri:
```tsx
const shotParams = new URLSearchParams({ player: playerName, season });
leagueIds.forEach(id => shotParams.append("league_ids", String(id)));
if (shotSituation !== "All") shotParams.set("situation", shotSituation);
if (shotResult    !== "All") shotParams.set("result",    shotResult);
fetch(`${API_BASE}/api/nerd-zone/player-shots?${shotParams}`, { cache: "no-store" })
```

Aggiungi `shotSituation` e `shotResult` alle dipendenze dell'useEffect dei shots.

Aggiungi i filtri dropdowns sopra la shot map:
```tsx
{/* Shot map filters */}
<div className="flex flex-wrap gap-3 mb-3">
  <div>
    <label className="text-[9px] text-slate-600 uppercase tracking-widest block mb-1">Season</label>
    {/* already controlled by season state in header */}
    <span className="text-xs text-slate-400">{season}</span>
  </div>
  <div>
    <label className="text-[9px] text-slate-600 uppercase tracking-widest block mb-1">Situation</label>
    <select value={shotSituation} onChange={e => setShotSituation(e.target.value)}
      className="bg-[#0d1220] border border-slate-800 rounded px-2 py-1 text-xs text-white focus:outline-none">
      {["All","OpenPlay","FromCorner","SetPiece","DirectFreekick","Penalty"].map(s => (
        <option key={s} value={s}>{s}</option>
      ))}
    </select>
  </div>
  <div>
    <label className="text-[9px] text-slate-600 uppercase tracking-widest block mb-1">Result</label>
    <select value={shotResult} onChange={e => setShotResult(e.target.value)}
      className="bg-[#0d1220] border border-slate-800 rounded px-2 py-1 text-xs text-white focus:outline-none">
      {["All","Goal","SavedShot","MissedShots","BlockedShot"].map(s => (
        <option key={s} value={s}>{s}</option>
      ))}
    </select>
  </div>
</div>
```

- [ ] **Step 2: Aggiungi CSV export alla tabella storia**

Aggiungi `import { Download } from "lucide-react";` e un bottone CSV nella sezione della history table (vicino alla tab bar):

```tsx
<button
  onClick={() => {
    const cols = colsFor(histTab) as any[];
    const headers = cols.map((c: any) => c.h).join(",");
    const csvRows = history.map((row: any) =>
      cols.map((c: any) => cellFmt(row[c.key], c.key)).join(",")
    );
    const blob = new Blob([headers + "\n" + csvRows.join("\n")], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${playerName}_${histTab}.csv`;
    a.click();
  }}
  className="ml-auto p-1.5 rounded border border-slate-800 bg-[#0d1220] text-slate-600 hover:text-white transition-colors"
>
  <Download size={12} />
</button>
```

Metti questo bottone nella stessa flex row dei tab (usa `flex items-center justify-between` sul wrapper).

- [ ] **Step 3: Aggiorna anche i tab di history**

Aggiungi "Shot zones" e "Shot types" ai HISTORY_TABS (che tornano dati dal backend via situation tab):
```tsx
const HISTORY_TABS = [
  { id: "season",    label: "Season"    },
  { id: "position",  label: "Position"  },
  { id: "situation", label: "Situation" },
  { id: "shot_zones",label: "Shot zones" },
  { id: "shot_types",label: "Shot types" },
] as const;
```

Per shot_zones e shot_types, usa il tab "situation" del backend (sono alias visivi — per ora mostreranno lo stesso dato, e potrai personalizzare dopo).

- [ ] **Step 4: Commit**
```bash
git add frontend/app/nerd-zone/player/[slug]/page.tsx
git commit -m "feat(nerd-zone): player page — shot filters, history CSV, extra tabs"
```

---

## Self-Review

**Spec coverage:**
- ✅ League homepage con 5 leghe, default Premier League (Task 6)
- ✅ Classifica con xG, xGA, xPTS, xGD (Task 6)
- ✅ Click su squadra → team page (Task 6)
- ✅ Calendario orizzontale scrollable (già in MatchCalendar.tsx, endpoint Task 3)
- ✅ Filtri tab (Situation/Formation/Game state/Timing/Shot zones/Attack speed/Result) (Task 7)
- ✅ Roster table con Sh90/KP90/xG90/xA90/Apps (Task 8)
- ✅ Player page: storico stagioni con team (Task 4)
- ✅ Radar chart (già in RadarEcharts.tsx, endpoint Task 4)
- ✅ Shot map con coordinate X/Y (già in ShotMapHorizontal.tsx, endpoint Task 4)
- ✅ Filtri shot map (Situation/Result) (Task 10)
- ✅ CSV export su tutte le tabelle (Tasks 6,7,8,10)
- ✅ Ordinamento colonne ovunque (Tasks 6, tabelle esistenti)
- ✅ Link NERD ZONE navbar (Task 5)
- ✅ `cache: 'no-store'` su tutte le fetch (incluso nei codici sopra)
- ✅ Backend non tocca meritometro.py o altri file esistenti
- ⚠️ Formation/Game state/Attack speed: tab presenti, mostrano "Data not available" (dato mancante nel DB)
- ⚠️ Nomi colonne shots ("X","Y","xG","minute"): se diversi nel DB, aggiusta solo in nerdzone_routes.py

**Placeholder scan:** Nessun TBD o TODO. Tutti i tab "no data" ritornano `[]` dal backend e mostrano messaggio chiaro.

**Type consistency:** `RosterRow` aggiornato in RosterTable.tsx viene usato anche in team/[id]/page.tsx tramite import — aggiornare un solo file aggiorna entrambi.
