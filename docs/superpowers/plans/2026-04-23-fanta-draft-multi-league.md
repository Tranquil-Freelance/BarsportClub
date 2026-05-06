# Fanta Draft Multi-League Refactoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Segment Fanta Draft by 5 European leagues with total data isolation, fix wrong team associations in both Fanta Draft and Scout Engine, normalize positions, and add xG/xA Delta breakout algorithm.

**Architecture:** Backend adds `league_id` filtering to all fanta endpoints via a `_resolve_league_id` helper + `latest_team` CTE using `DISTINCT ON (player_id)`. Scout Engine gets a targeted correlated subquery fix for team resolution. Frontend adds league state in the hero section and propagates `&league=` to all API calls.

**Tech Stack:** FastAPI + SQLAlchemy async (backend), Next.js 16 + React 19 + TypeScript (frontend), PostgreSQL (`rosters`, `matchcalendar`, `team`, `league` tables).

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `backend/app/api/fanta_routes.py` | Modify | All fanta endpoints: league filter, team CTE, position norm, xG delta |
| `backend/app/api/scout_routes.py` | Modify | Fix `MAX(t.name)` bug with correlated subquery |
| `frontend/app/fanta-draft/page.tsx` | Modify | League state, hero tabs, API propagation, DataTable columns, BREAKOUT badge |

---

## Task 1: Backend helpers in `fanta_routes.py`

**Files:**
- Modify: `backend/app/api/fanta_routes.py`

These helpers are used by every subsequent task. Implement them first.

- [ ] **Step 1.1 — Add `_POS_NORM` dict and `_normalize_position` function**

Open `backend/app/api/fanta_routes.py`. After the `FANTASY_PTS_ASSIST = 3.0` line, add:

```python
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
```

- [ ] **Step 1.2 — Add `_resolve_league_id`, `_latest_team_cte_sql`, `_combine_cte`**

Immediately after `_normalize_position`, add:

```python
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
```

- [ ] **Step 1.3 — Modify `build_filter_parts` to accept `with_league` parameter**

Find the existing `build_filter_parts` function. Replace it entirely with:

```python
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
    else:  # current
        return (
            "",
            "",
            "AND EXTRACT(YEAR FROM mc.match_datetime) = "
            "(SELECT EXTRACT(YEAR FROM MAX(match_datetime)) FROM matchcalendar)"
        )
```

- [ ] **Step 1.4 — Verify helpers load without syntax errors**

```bash
cd "backend" && python -c "from app.api.fanta_routes import _normalize_position, _latest_team_cte_sql, _combine_cte, build_filter_parts; print('OK')"
```

Expected output: `OK`

- [ ] **Step 1.5 — Commit**

```bash
git add backend/app/api/fanta_routes.py
git commit -m "feat(fanta): add league/team helpers and position normalization"
```

---

## Task 2: Fix `/players` endpoint

**Files:**
- Modify: `backend/app/api/fanta_routes.py` (the `get_fanta_players` function)

- [ ] **Step 2.1 — Replace `get_fanta_players` function body**

Find `@router.get("/players")` and replace the entire function with:

```python
@router.get("/players")
async def get_fanta_players(
    filter: str = Query("current", regex="^(current|previous|last5)$"),
    league: str = Query("Serie A"),
):
    try:
        cte, extra_join, where = build_filter_parts(filter, with_league=True)
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
                MAX(t_curr.name)                   AS team_name
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
            result = await conn.execute(text(query_sql), {"league_id": league_id})
            rows = result.fetchall()

        players = []
        for row in rows:
            mins     = safe_float(row[11])
            xg       = safe_float(row[4])
            xa       = safe_float(row[5])
            shots    = safe_float(row[6])
            xgchain  = safe_float(row[7])
            keypasses= safe_float(row[8])
            goals    = int(row[9] or 0)
            assists  = int(row[10] or 0)
            matches  = int(row[3] or 0)

            xg_p90      = p90(xg, mins)
            xa_p90      = p90(xa, mins)
            shots_p90   = p90(shots, mins)
            xgchain_p90 = p90(xgchain, mins)
            keypasses_p90 = p90(keypasses, mins)
            goals_p90   = p90(goals, mins)
            assists_p90 = p90(assists, mins)
            production  = round(xg_p90 + xa_p90, 3)
            value       = xg_p90 * FANTASY_PTS_GOAL + xa_p90 * FANTASY_PTS_ASSIST

            xg_delta_p90 = round(max(0.0, xg_p90 - goals_p90), 3)
            xa_delta_p90 = round(max(0.0, xa_p90 - assists_p90), 3)
            breakout_score = round(
                xg_delta_p90 * FANTASY_PTS_GOAL + xa_delta_p90 * FANTASY_PTS_ASSIST, 2
            )
            is_breakout = breakout_score >= 0.25 and xg_p90 >= 0.05

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
                "xg_delta_p90":   xg_delta_p90,
                "xa_delta_p90":   xa_delta_p90,
                "breakout_score": breakout_score,
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
```

- [ ] **Step 2.2 — Test endpoint returns Serie A players with correct teams**

With the backend running (`uvicorn backend.app.main:app --reload --port 8000` from project root):

```bash
curl -s "http://localhost:8000/api/fanta/players?filter=current&league=Serie%20A" | python -m json.tool | head -60
```

Expected: JSON array, each item has `"team"` matching a real Serie A club, `"position"` one of `GK/DF/MF/FW/N/D`, and `"is_breakout"` bool field present.

- [ ] **Step 2.3 — Test Premier League isolation**

```bash
curl -s "http://localhost:8000/api/fanta/players?filter=current&league=Premier%20League" | python -m json.tool | python -c "import sys,json; data=json.load(sys.stdin); teams=set(p['team'] for p in data[:10]); print('PL teams:', teams)"
```

Expected: teams should be Premier League clubs (Arsenal, Chelsea, Man City, etc.) — none should be Serie A clubs.

- [ ] **Step 2.4 — Commit**

```bash
git add backend/app/api/fanta_routes.py
git commit -m "feat(fanta): league filter + team CTE fix + xG delta in /players"
```

---

## Task 3: Fix `_compute_percentiles` and `/player/{id}` endpoint

**Files:**
- Modify: `backend/app/api/fanta_routes.py`

- [ ] **Step 3.1 — Update `_compute_percentiles` signature to include `league_id`**

Find the `_compute_percentiles` function. Replace it entirely with:

```python
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
```

- [ ] **Step 3.2 — Update `get_team_attack_index` to accept `league_id`**

Find `get_team_attack_index`. Replace it entirely with:

```python
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
```

- [ ] **Step 3.3 — Replace `get_fanta_player_profile` function**

Find `@router.get("/player/{player_id}")` and replace the entire function:

```python
@router.get("/player/{player_id}")
async def get_fanta_player_profile(
    player_id: str,
    filter: str = Query("current", regex="^(current|previous|last5)$"),
    league: str = Query("Serie A"),
):
    try:
        cte, extra_join, where = build_filter_parts(filter, with_league=True)
        full_cte = _combine_cte(cte, _latest_team_cte_sql())
        min_min = MIN_MINUTES_LAST5 if filter == "last5" else MIN_MINUTES

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
            # Note: _latest_team_cte_sql() returns the CTE body without WITH keyword
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
```

- [ ] **Step 3.4 — Test player profile with league isolation**

```bash
# Find a player_id first
curl -s "http://localhost:8000/api/fanta/players?league=Serie%20A" | python -c "import sys,json; data=json.load(sys.stdin); print(data[0]['player'], data[0]['player_id'], data[0]['team'])"
# Use the player_id from above (replace PLAYER_ID below)
curl -s "http://localhost:8000/api/fanta/player/PLAYER_ID?league=Serie%20A" | python -m json.tool | grep -E '"team"|"position"|"league"'
```

Expected: `team` is a real Serie A club, `position` is `GK/DF/MF/FW`, `league` is `"Serie A"`.

- [ ] **Step 3.5 — Commit**

```bash
git add backend/app/api/fanta_routes.py
git commit -m "feat(fanta): league-scoped percentiles, player profile, TAI"
```

---

## Task 4: Fix `/search`, `/dashboard`, `/auction-strategy` endpoints

**Files:**
- Modify: `backend/app/api/fanta_routes.py`

- [ ] **Step 4.1 — Replace `search_fanta_players` function**

Find `@router.get("/search")` and replace the function:

```python
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
```

- [ ] **Step 4.2 — Replace `get_fanta_dashboard` function**

Find `@router.get("/dashboard")` and replace it:

```python
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
            """), {"league_id": league_id}))
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
                "breakout_multiplier": round(breakout, 2),
                "value_score": round(value, 1), "labels": labels,
                "latest_xg": seasons[0]["xg"] if seasons else 0,
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
```

- [ ] **Step 4.3 — Replace `get_auction_strategy` function**

Find `@router.get("/auction-strategy")` and replace it:

```python
@router.get("/auction-strategy")
async def get_auction_strategy(
    budget: float = Query(500),
    participants: int = Query(8),
    filter: str = Query("current", regex="^(current|previous|last5)$"),
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
```

- [ ] **Step 4.4 — Test search returns only league-scoped results**

```bash
curl -s "http://localhost:8000/api/fanta/search?q=Mo&league=Premier%20League" | python -m json.tool
```

Expected: results like Salah, Trossard, etc. — only Premier League players.

```bash
curl -s "http://localhost:8000/api/fanta/search?q=Mo&league=Serie%20A" | python -m json.tool
```

Expected: different results (Serie A players with "Mo" in name), no overlap with PL results.

- [ ] **Step 4.5 — Commit**

```bash
git add backend/app/api/fanta_routes.py
git commit -m "feat(fanta): league filter for search, dashboard, auction-strategy"
```

---

## Task 5: Fix Scout Engine team resolution

**Files:**
- Modify: `backend/app/api/scout_routes.py`

The bug: `MAX(t.name) AS team_name` in `AGG` (line 39) picks alphabetically last team across all matches/seasons. Fix: replace with a correlated subquery that returns the team from the player's most recent match.

- [ ] **Step 5.1 — Replace `MAX(t.name)` in `AGG` constant with correlated subquery**

Find the `AGG` constant at the top of `scout_routes.py`. Replace only the `MAX(t.name) AS team_name,` line:

```python
AGG = """
    r.player                                AS player_name,
    (
        SELECT t2.name
        FROM rosters r2
        JOIN matchcalendar mc2 ON mc2.id = r2.match_id AND mc2.is_completed = true
        JOIN team t2 ON (
            CASE WHEN r2.team_type ILIKE 'h%'
                 THEN mc2.home_team_id ELSE mc2.away_team_id END
        ) = t2.id
        WHERE r2.player = r.player
        ORDER BY mc2.match_datetime DESC
        LIMIT 1
    )                                       AS team_name,
    MODE() WITHIN GROUP (ORDER BY r.position)
        FILTER (WHERE r.position NOT IN ('Sub', 'SUB') AND r.position IS NOT NULL)
                                            AS position,
    COALESCE(SUM(r.goals::float),       0)  AS goals,
    0                                       AS npg,
    COALESCE(SUM(r.shots::float),       0)  AS shots,
    COALESCE(SUM(r.assists::float),     0)  AS assists,
    COALESCE(SUM(r.key_passes::float),  0)  AS key_passes,
    COALESCE(SUM(r."xG"::float),        0)  AS xg,
    0                                       AS npxg,
    COALESCE(SUM(r."xA"::float),        0)  AS xa,
    COALESCE(SUM(r."xGChain"::float),   0)  AS xgchain,
    COALESCE(SUM(r."xGBuildup"::float), 0)  AS xgbuildup,
    COALESCE(SUM(r.time::float),        1)  AS minutes,
    COUNT(DISTINCT r.match_id)              AS games
"""
```

- [ ] **Step 5.2 — Fix `MAX(t.name)` in `/search` endpoint of scout_routes**

Find the scout `/search` endpoint (around line 282). Replace the `MAX(t.name)` in that specific query:

```python
@router.get("/search")
async def search_player(q: str):
    try:
        async with engine.connect() as conn:
            res = await conn.execute(
                text(f"""
                    SELECT r.player,
                           (
                               SELECT t2.name
                               FROM rosters r2
                               JOIN matchcalendar mc2 ON mc2.id = r2.match_id AND mc2.is_completed = true
                               JOIN team t2 ON (
                                   CASE WHEN r2.team_type ILIKE 'h%'
                                        THEN mc2.home_team_id ELSE mc2.away_team_id END
                               ) = t2.id
                               WHERE r2.player = r.player
                               ORDER BY mc2.match_datetime DESC
                               LIMIT 1
                           )                    AS team,
                           SUM(r.time::float)   AS total_min
                    {_FROM_JOIN}
                    WHERE {NAME_NORM} ILIKE {QUERY_NORM}
                    GROUP BY r.player
                    HAVING SUM(r.time::float) > 500
                    ORDER BY total_min DESC
                    LIMIT 12
                """),
                {"q": f"%{q.strip().replace(' ', '%')}%"},
            )
            return {"results": [{"name": r[0], "team": r[1]} for r in res.fetchall()]}
    except Exception as e:
        logger.error(f"search error: {e}")
        return {"results": []}
```

Note: the `_FROM_JOIN` still includes `JOIN team t` — that's fine, it's used by other AGG aggregations. The correlated subquery uses aliases `r2`, `mc2`, `t2` to avoid conflicts.

- [ ] **Step 5.3 — Test Scout Engine team fix**

```bash
# Search for a player known to have had the bug (e.g., "kane", "dybala")
curl -s "http://localhost:8000/api/scout/search?q=kane" | python -m json.tool
```

Expected: Harry Kane shows team as "Bayern München" (or current club), NOT "Wolverhampton".

```bash
curl -s "http://localhost:8000/api/scout/search?q=dybala" | python -m json.tool
```

Expected: Dybala shows team as "AS Roma" (or current club), NOT "Sassuolo".

- [ ] **Step 5.4 — Test Scout leaders endpoint**

```bash
curl -s "http://localhost:8000/api/scout/leaders" | python -m json.tool | grep -A2 '"name"' | head -40
```

Expected: each player entry has a realistic current team name (not an alphabetically random past club).

- [ ] **Step 5.5 — Commit**

```bash
git add backend/app/api/scout_routes.py
git commit -m "fix(scout): replace MAX(t.name) with latest-match correlated subquery"
```

---

## Task 6: Frontend — League state, hero tabs, API propagation

**Files:**
- Modify: `frontend/app/fanta-draft/page.tsx`

- [ ] **Step 6.1 — Add `LeagueId` type and `LEAGUES` constant**

At the top of `page.tsx`, after the existing `type TimeFilter` line, add:

```typescript
type LeagueId = "Serie A" | "Premier League" | "La Liga" | "Bundesliga" | "Ligue 1";

const LEAGUES: { id: LeagueId; flag: string }[] = [
  { id: "Serie A",        flag: "🇮🇹" },
  { id: "Premier League", flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿" },
  { id: "La Liga",        flag: "🇪🇸" },
  { id: "Bundesliga",     flag: "🇩🇪" },
  { id: "Ligue 1",        flag: "🇫🇷" },
];
```

- [ ] **Step 6.2 — Add `league` state and update `FPlayer` type**

In `FPlayer` type, replace the closing `}` after `max_bid_pct: number;` with:

```typescript
  xg_delta_p90: number;
  xa_delta_p90: number;
  breakout_score: number;
  is_breakout: boolean;
};
```

Inside `FantaDraftPage` component, after `const [timeFilter, setTimeFilter] = useState<TimeFilter>("current");` add:

```typescript
const [league, setLeague] = useState<LeagueId>("Serie A");
```

- [ ] **Step 6.3 — Add league tabs to hero section**

In the hero `<div>` (the one with `bg-[#060F1E] border-b-4 border-[#FF2A6D]`), find the `<p className="text-slate-500 font-black...">` subtitle line. After it, add the league tab row:

```tsx
          {/* League tabs */}
          <div className="flex flex-wrap gap-2 mt-4">
            {LEAGUES.map(l => (
              <button
                key={l.id}
                onClick={() => {
                  setLeague(l.id);
                  setProfile(null);
                  setAuctionTargets([]);
                }}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all border ${
                  league === l.id
                    ? "bg-[#FF2A6D] border-[#FF2A6D] text-white shadow-[0_0_10px_rgba(255,42,109,0.3)]"
                    : "border-slate-700 text-slate-400 hover:border-slate-500 hover:text-white"
                }`}
              >
                <span>{l.flag}</span>
                <span>{l.id}</span>
              </button>
            ))}
          </div>
```

- [ ] **Step 6.4 — Update `/players` useEffect to include `league`**

Find the `useEffect` that calls `${API}/players`. Replace it with:

```typescript
  useEffect(() => {
    setPlayersLoading(true);
    setPlayersError(null);
    fetch(`${API}/players?filter=${timeFilter}&league=${encodeURIComponent(league)}`)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(data => { setPlayers(Array.isArray(data) ? data : []); setPlayersLoading(false); })
      .catch(() => { setPlayersError("Backend non raggiungibile (porta 8000)."); setPlayersLoading(false); });
  }, [timeFilter, league]);
```

- [ ] **Step 6.5 — Update `loadProfile` to include `league`**

Find the `loadProfile` callback. Replace it:

```typescript
  const loadProfile = useCallback(async (pid: string, name: string) => {
    setSuggestions([]); setQuery(name); setProfileLoading(true); setProfile(null); setProfileName(name);
    try {
      const r = await fetch(`${API}/player/${pid}?filter=${timeFilter}&league=${encodeURIComponent(league)}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setProfile(await r.json());
    } catch { setProfile(null); } finally { setProfileLoading(false); }
  }, [timeFilter, league]);
```

- [ ] **Step 6.6 — Update search autocomplete `useEffect` to include `league`**

Find the `useEffect` for autocomplete (the one with `debounceRef`). Replace:

```typescript
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (query.length < 2) { setSuggestions([]); return; }
    debounceRef.current = setTimeout(() => {
      fetch(`${API}/search?q=${encodeURIComponent(query)}&league=${encodeURIComponent(league)}`)
        .then(r => r.json())
        .then(d => setSuggestions(Array.isArray(d) ? d : []))
        .catch(() => setSuggestions([]));
    }, 300);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [query, league]);
```

- [ ] **Step 6.7 — Update `calcAuction` to include `league`**

Find `const calcAuction = async () => {`. Replace the fetch URL inside:

```typescript
  const calcAuction = async () => {
    setAuctionLoading(true);
    try {
      const r = await fetch(
        `${API}/auction-strategy?budget=${auctionBudget}&participants=${auctionParticipants}&filter=${timeFilter}&league=${encodeURIComponent(league)}`
      );
      const data = await r.json();
      setAuctionTargets(data.targets ?? []);
    } catch { setAuctionTargets([]); } finally { setAuctionLoading(false); }
  };
```

- [ ] **Step 6.8 — Commit**

```bash
git add frontend/app/fanta-draft/page.tsx
git commit -m "feat(fanta-ui): league state, hero tabs, API propagation"
```

---

## Task 7: Frontend — DataTable columns + BREAKOUT badge

**Files:**
- Modify: `frontend/app/fanta-draft/page.tsx`

- [ ] **Step 7.1 — Update `SortKey` type and `COLS` array**

Find `type SortKey = keyof Pick<FPlayer, ...>`. Replace it:

```typescript
type SortKey = keyof Pick<FPlayer,
  "xg_p90" | "xa_p90" | "shots_p90" | "xg_delta_p90" | "xa_delta_p90" | "production" | "max_bid_pct" | "matches"
>;
```

Find the `COLS` array. Replace it entirely:

```typescript
const COLS: { key: SortKey; label: string; hint?: string }[] = [
  { key: "matches",      label: "G",      hint: "Partite" },
  { key: "xg_p90",      label: "xG/90" },
  { key: "xa_p90",      label: "xA/90" },
  { key: "shots_p90",   label: "Sh/90" },
  { key: "xg_delta_p90",label: "xGΔ/90", hint: "xG atteso − Gol reali /90 (positivo = candidato breakout)" },
  { key: "xa_delta_p90",label: "xAΔ/90", hint: "xA atteso − Assist reali /90" },
  { key: "max_bid_pct", label: "Bid %",  hint: "% budget consigliata" },
];
```

- [ ] **Step 7.2 — Update DataTable row rendering to show BREAKOUT badge and delta columns**

Inside `DataTable`, find the `<tbody>` row rendering. Replace the full `<tr>` content:

```tsx
                <tr key={p.player_id}
                  onClick={() => onSelect(p)}
                  className="hover:bg-slate-800/30 transition-colors cursor-pointer group">
                  <td className="py-3 pl-4 text-[10px] font-black text-slate-700">{page * PAGE_SIZE + i + 1}</td>
                  <td className="py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-black text-sm text-white group-hover:text-[#FF2A6D] transition-colors truncate block max-w-[140px]"
                        style={{ fontFamily: "var(--font-oswald, sans-serif)" }}>
                        {p.player}
                      </span>
                      {p.is_breakout && (
                        <span className="text-[8px] font-black uppercase tracking-widest px-2 py-0.5 rounded border text-amber-400 bg-amber-500/10 border-amber-500/25 whitespace-nowrap">
                          BREAKOUT
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-3 text-[10px] font-bold text-slate-500 hidden md:table-cell">{p.team}</td>
                  <td className="py-3">
                    <span className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded"
                      style={{ color: posColor, background: `${posColor}18` }}>
                      {p.position}
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-right text-[11px] font-black text-slate-400">{p.matches}</td>
                  <td className="py-3 pr-4 text-right text-[11px] font-black text-[#FF2A6D]">{fmt(p.xg_p90)}</td>
                  <td className="py-3 pr-4 text-right text-[11px] font-black text-[#007AFF]">{fmt(p.xa_p90)}</td>
                  <td className="py-3 pr-4 text-right text-[11px] font-black text-slate-400">{fmt(p.shots_p90)}</td>
                  <td className="py-3 pr-4 text-right text-[11px] font-black"
                    style={{ color: p.xg_delta_p90 > 0 ? "#F59E0B" : "#475569" }}>
                    {p.xg_delta_p90 > 0 ? `+${fmt(p.xg_delta_p90)}` : fmt(p.xg_delta_p90)}
                  </td>
                  <td className="py-3 pr-4 text-right text-[11px] font-black"
                    style={{ color: p.xa_delta_p90 > 0 ? "#F59E0B" : "#475569" }}>
                    {p.xa_delta_p90 > 0 ? `+${fmt(p.xa_delta_p90)}` : fmt(p.xa_delta_p90)}
                  </td>
                  <td className="py-3 pr-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-12 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div className="h-full bg-[#FF2A6D] rounded-full" style={{ width: `${Math.min(p.max_bid_pct * 5, 100)}%` }} />
                      </div>
                      <span className="text-[11px] font-black text-white w-8 text-right">{fmt(p.max_bid_pct, 1)}%</span>
                    </div>
                  </td>
                </tr>
```

- [ ] **Step 7.3 — Add `useEffect` for pagination reset inside `DataTable`**

Inside the `DataTable` function, after the `useState` declarations, add:

```typescript
  useEffect(() => {
    setPage(0);
  }, [players]);
```

- [ ] **Step 7.4 — Update DataTable header to show amber color on delta columns**

In the `<thead>` of DataTable, the columns are rendered from `COLS`. Find the `{COLS.map(col => (` section and update it to color delta headers amber:

```tsx
              {COLS.map(col => (
                <th key={col.key} className="py-3 pr-4 text-right" title={col.hint}>
                  <button onClick={() => toggleSort(col.key)}
                    className={`flex items-center gap-1 ml-auto text-[9px] font-black uppercase tracking-widest transition-colors hover:text-white ${
                      col.key === "xg_delta_p90" || col.key === "xa_delta_p90"
                        ? "text-amber-500"
                        : "text-slate-500"
                    }`}>
                    {col.label} <SortIcon k={col.key} />
                  </button>
                </th>
              ))}
```

- [ ] **Step 7.5 — TypeScript build check**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

Expected: no errors. If errors appear, check type mismatches in `FPlayer` — `xg_delta_p90`, `xa_delta_p90`, `breakout_score`, `is_breakout` must all be present.

- [ ] **Step 7.6 — Commit**

```bash
git add frontend/app/fanta-draft/page.tsx
git commit -m "feat(fanta-ui): xGΔ/xAΔ columns, BREAKOUT badge, pagination reset"
```

---

## Task 8: Integration smoke test

- [ ] **Step 8.1 — Start backend**

```bash
cd "backend" && uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 8.2 — Start frontend**

In a second terminal:

```bash
cd "frontend" && npm run dev
```

Open `http://localhost:3000/fanta-draft`.

- [ ] **Step 8.3 — Verify league tabs appear in hero**

Expected: 5 flag+name tabs visible below the "Arbitraggio Statistico · xG · xA..." subtitle. Active tab has red background.

- [ ] **Step 8.4 — Verify data isolation**

1. Select **Serie A** → wait for table → note first 5 players and their teams
2. Select **Premier League** → verify table reloads, players are different, teams are English clubs
3. Select **La Liga** → verify Spanish clubs
4. Switch back to **Serie A** → same players as step 1

- [ ] **Step 8.5 — Verify search isolation**

1. While on **Serie A**: type "Mo" in search → suggestions should be Serie A players only
2. Switch to **Premier League**: type "Mo" → should show Mo Salah, not the same Serie A results

- [ ] **Step 8.6 — Verify BREAKOUT badge and delta columns**

In the DataTable: columns `xGΔ/90` and `xAΔ/90` visible (amber headers). Players with high delta show amber `+0.xx` values and "BREAKOUT" badge next to name.

- [ ] **Step 8.7 — Verify Scout Engine fix**

```bash
curl -s "http://localhost:8000/api/scout/search?q=dybala" | python -m json.tool
```

Expected: `"team": "AS Roma"` (not "Sassuolo").

- [ ] **Step 8.8 — Final commit**

```bash
git add -A
git commit -m "feat: fanta draft multi-league refactoring complete"
```
