"""
BARSPORT SCOUT ENGINE — Porta 9000
Server dedicato allo Scout Engine e al finder.html

Avvio:
    cd backend
    uvicorn scoutengine:app --port 9000 --reload

Endpoint esposti:
    GET /health
    GET /api/scout/search?q=
    GET /api/scout/leaders
    GET /api/scout/player/{player_name}
    GET /api/shots/{player_name}
    GET /api/undervalued?category=&league_id=&size=
    GET /api/h2h?p1=&p2=
    GET /replacement/{player_name}
"""

import math
import logging
import pandas as pd
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# ── SETUP ─────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SCOUT-9000] %(levelname)s %(message)s"
)
logger = logging.getLogger("ScoutEngine")

DB_URL = "postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat"
engine = create_async_engine(DB_URL, pool_size=10, max_overflow=5, pool_pre_ping=True)

app = FastAPI(title="Barsport Scout Engine", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── HELPERS ───────────────────────────────────────────────────────────────────

def safe_float(val, default: float = 0.0) -> float:
    """Converte qualsiasi valore in float sicuro (no NaN, no Inf)."""
    if val is None:
        return default
    try:
        f = float(val)
        return default if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return default


def per90(total: float, minutes: float) -> float:
    """Normalizza un valore su 90 minuti."""
    if minutes < 1:
        return 0.0
    return (total / minutes) * 90


def percentile_rank(value: float, distribution: list) -> float:
    """Calcola il percentile di un valore su una distribuzione."""
    if not distribution:
        return 0.0
    rank = sum(v < value for v in distribution)
    return round((rank / len(distribution)) * 100, 1)


# ── 1. HEALTH ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "Scout Engine 9000 Online", "version": "2.0.0"}


# ── 2. RICERCA GIOCATORI ──────────────────────────────────────────────────────

@app.get("/api/scout/search")
async def search_players(q: str = Query("")):
    """Ricerca per nome con ILIKE. Ritorna lista di stringhe."""
    if len(q) < 2:
        return []
    try:
        async with engine.connect() as conn:
            res = await conn.execute(
                text("SELECT DISTINCT player FROM rosters WHERE player ILIKE :q ORDER BY player LIMIT 12"),
                {"q": f"%{q}%"}
            )
            return [row[0] for row in res.fetchall()]
    except Exception as e:
        logger.error(f"search error: {e}")
        return []


# ── 3. LEADERS (TOP SCORER / ARCHITECT) ───────────────────────────────────────

@app.get("/api/scout/leaders")
async def get_leaders():
    """Top 5 scorer e top 5 assist della stagione 25/26."""
    try:
        async with engine.connect() as conn:
            res_s = await conn.execute(text("""
                SELECT r.player,
                       SUM(r.goals) AS g,
                       (SUM(r."xG") / NULLIF(SUM(r.time), 0)) * 90 AS xg90
                FROM rosters r
                JOIN matchcalendar m ON r.match_id = m.id
                WHERE m.match_datetime >= '2025-08-01'
                GROUP BY r.player
                HAVING SUM(r.time) > 200
                ORDER BY g DESC
                LIMIT 5
            """))
            res_a = await conn.execute(text("""
                SELECT r.player,
                       SUM(r.assists) AS a,
                       (SUM(r."xA") / NULLIF(SUM(r.time), 0)) * 90 AS xa90
                FROM rosters r
                JOIN matchcalendar m ON r.match_id = m.id
                WHERE m.match_datetime >= '2025-08-01'
                GROUP BY r.player
                HAVING SUM(r.time) > 200
                ORDER BY a DESC
                LIMIT 5
            """))

        scorers = [
            {
                "name":  r[0],
                "team":  "Stagione 25/26",
                "value": f"{r[1]} Goal",
                "stat":  f"{round(safe_float(r[2]), 2)} xG/90",
            }
            for r in res_s.fetchall()
        ]
        architects = [
            {
                "name":  r[0],
                "team":  "Stagione 25/26",
                "value": f"{r[1]} Assist",
                "stat":  f"{round(safe_float(r[2]), 2)} xA/90",
            }
            for r in res_a.fetchall()
        ]
        return {"scorers": scorers, "architects": architects}

    except Exception as e:
        logger.error(f"leaders error: {e}")
        return {"scorers": [], "architects": []}


# ── 4. PROFILO GIOCATORE ──────────────────────────────────────────────────────

@app.get("/api/scout/player/{player_name}")
async def get_player_profile(player_name: str):
    """
    Profilo completo del giocatore nel formato atteso da finder.html.
    Calcola: statistiche p90, Field Tilt, TSI, DNA tiri per stagione,
    trend xG/xA su 3 stagioni, radar percentili.
    """
    try:
        async with engine.connect() as conn:

            # 1. Statistiche aggregate totali (query base - must succeed)
            # MAX(CASE...) ignora 'Sub' così non sovrascrive il ruolo reale
            r = (await conn.execute(text("""
                SELECT player,
                       MAX(CASE WHEN UPPER(TRIM(position)) NOT IN ('SUB','') AND position IS NOT NULL
                                THEN position END) AS pos,
                       SUM(time)          AS mins,
                       SUM(goals)         AS g,
                       SUM(assists)       AS a,
                       SUM(shots)         AS sh,
                       SUM(key_passes)    AS kp,
                       SUM("xG")          AS xg,
                       SUM("xA")          AS xa,
                       SUM("xGChain")     AS chain,
                       SUM("xGBuildup")   AS build,
                       SUM(yellow_card)   AS yc,
                       SUM(red_card)      AS rc
                FROM rosters
                WHERE player ILIKE :n
                GROUP BY player
                LIMIT 1
            """), {"n": player_name})).fetchone()

            if not r:
                return {"error": "Giocatore non trovato nel database"}

            mins  = max(safe_float(r[2]), 1.0)
            g     = safe_float(r[3])
            a     = safe_float(r[4])
            sh    = safe_float(r[5])
            kp    = safe_float(r[6])
            xg    = safe_float(r[7])
            xa    = safe_float(r[8])
            chain = safe_float(r[9])
            build = safe_float(r[10])
            yc    = int(r[11] or 0)
            rc    = int(r[12] or 0)

            # 2. Nome squadra e lega (query opzionale — fallback graceful)
            team_name = "N/D"
            league_name = "N/D"
            try:
                team_row = (await conn.execute(text("""
                    SELECT
                        CASE WHEN LOWER(TRIM(COALESCE(ros.team_type,''))) = 'h' THEN th.name ELSE ta.name END AS team_name,
                        l.name AS league_name
                    FROM rosters ros
                    JOIN matchcalendar mc ON ros.match_id = mc.id
                    JOIN team th ON mc.home_team_id = th.id
                    JOIN team ta ON mc.away_team_id = ta.id
                    JOIN league l ON mc.league_id = l.id
                    WHERE ros.player ILIKE :n
                    ORDER BY mc.match_datetime DESC
                    LIMIT 1
                """), {"n": player_name})).fetchone()
                if team_row:
                    team_name   = team_row[0] or "N/D"
                    league_name = team_row[1] or "N/D"
            except Exception as e2:
                logger.warning(f"team/league query failed for '{player_name}': {e2}")

            # 3. Field Tilt e TSI (query opzionale — fallback graceful)
            tilt = 50.0
            tsi_label = "N/D"
            try:
                ctx_row = (await conn.execute(text("""
                    SELECT
                        AVG(CASE WHEN LOWER(TRIM(COALESCE(ros.team_type,''))) = 'h' THEN mc."home_xG" ELSE mc."away_xG" END) AS xg_for,
                        AVG(CASE WHEN LOWER(TRIM(COALESCE(ros.team_type,''))) = 'h' THEN mc."away_xG" ELSE mc."home_xG" END) AS xg_against,
                        AVG(CASE WHEN LOWER(TRIM(COALESCE(ros.team_type,''))) = 'h' THEN mc.home_ppda  ELSE mc.away_ppda  END) AS ppda,
                        AVG(CASE WHEN LOWER(TRIM(COALESCE(ros.team_type,''))) = 'h' THEN mc.home_deep  ELSE mc.away_deep  END) AS deep
                    FROM rosters ros
                    JOIN matchcalendar mc ON ros.match_id = mc.id
                    WHERE ros.player ILIKE :n AND mc.is_completed = True
                """), {"n": player_name})).fetchone()
                if ctx_row:
                    xg_for     = safe_float(ctx_row[0])
                    xg_against = safe_float(ctx_row[1])
                    ppda       = safe_float(ctx_row[2])
                    deep       = safe_float(ctx_row[3])
                    tilt = round(xg_for / (xg_for + xg_against) * 100, 1) if (xg_for + xg_against) > 0 else 50.0
                    tsi_label = f"PPDA {round(ppda, 2)} | Deep {int(deep)}"
            except Exception as e3:
                logger.warning(f"context/tilt query failed for '{player_name}': {e3}")

            # 4. DNA tiri per stagione (query opzionale — fallback graceful)
            dna: dict = {}
            try:
                dna_row = (await conn.execute(text("""
                    SELECT
                        SUM(CASE WHEN COALESCE(s."shotType", s.shot_type) ILIKE '%right%'
                                  AND mc.match_datetime >= '2023-07-01'
                                  AND mc.match_datetime <  '2024-07-01' THEN 1 ELSE 0 END) AS r24,
                        SUM(CASE WHEN COALESCE(s."shotType", s.shot_type) ILIKE '%right%'
                                  AND mc.match_datetime >= '2024-07-01'
                                  AND mc.match_datetime <  '2025-07-01' THEN 1 ELSE 0 END) AS r25,
                        SUM(CASE WHEN COALESCE(s."shotType", s.shot_type) ILIKE '%right%'
                                  AND mc.match_datetime >= '2025-07-01' THEN 1 ELSE 0 END) AS r26,
                        SUM(CASE WHEN COALESCE(s."shotType", s.shot_type) ILIKE '%left%'
                                  AND mc.match_datetime >= '2023-07-01'
                                  AND mc.match_datetime <  '2024-07-01' THEN 1 ELSE 0 END) AS l24,
                        SUM(CASE WHEN COALESCE(s."shotType", s.shot_type) ILIKE '%left%'
                                  AND mc.match_datetime >= '2024-07-01'
                                  AND mc.match_datetime <  '2025-07-01' THEN 1 ELSE 0 END) AS l25,
                        SUM(CASE WHEN COALESCE(s."shotType", s.shot_type) ILIKE '%left%'
                                  AND mc.match_datetime >= '2025-07-01' THEN 1 ELSE 0 END) AS l26,
                        SUM(CASE WHEN COALESCE(s."shotType", s.shot_type) ILIKE '%head%'
                                  AND mc.match_datetime >= '2023-07-01'
                                  AND mc.match_datetime <  '2024-07-01' THEN 1 ELSE 0 END) AS h24,
                        SUM(CASE WHEN COALESCE(s."shotType", s.shot_type) ILIKE '%head%'
                                  AND mc.match_datetime >= '2024-07-01'
                                  AND mc.match_datetime <  '2025-07-01' THEN 1 ELSE 0 END) AS h25,
                        SUM(CASE WHEN COALESCE(s."shotType", s.shot_type) ILIKE '%head%'
                                  AND mc.match_datetime >= '2025-07-01' THEN 1 ELSE 0 END) AS h26
                    FROM shots s
                    JOIN matchcalendar mc ON s.match_id = mc.id
                    WHERE s.player ILIKE :n
                """), {"n": player_name})).fetchone()
                if dna_row:
                    def dv(val): return int(val or 0)
                    r24, r25, r26 = dv(dna_row[0]), dv(dna_row[1]), dv(dna_row[2])
                    l24, l25, l26 = dv(dna_row[3]), dv(dna_row[4]), dv(dna_row[5])
                    h24, h25, h26 = dv(dna_row[6]), dv(dna_row[7]), dv(dna_row[8])
                    dna = {
                        "right_24": r24, "right_25": r25, "right_26": r26, "right_tot": r24 + r25 + r26,
                        "left_24":  l24, "left_25":  l25, "left_26":  l26, "left_tot":  l24 + l25 + l26,
                        "head_24":  h24, "head_25":  h25, "head_26":  h26, "head_tot":  h24 + h25 + h26,
                    }
            except Exception as e4:
                logger.warning(f"dna query failed for '{player_name}': {e4}")

            # 5. Trend xG/90 e xA/90 su 3 stagioni (query opzionale — fallback graceful)
            trend_xg = [0.0, 0.0, 0.0]
            trend_xa = [0.0, 0.0, 0.0]
            try:
                trend_row = (await conn.execute(text("""
                    SELECT
                        SUM(CASE WHEN mc.match_datetime >= '2023-07-01' AND mc.match_datetime < '2024-07-01' THEN r."xG" ELSE 0 END),
                        SUM(CASE WHEN mc.match_datetime >= '2023-07-01' AND mc.match_datetime < '2024-07-01' THEN r.time ELSE 0 END),
                        SUM(CASE WHEN mc.match_datetime >= '2024-07-01' AND mc.match_datetime < '2025-07-01' THEN r."xG" ELSE 0 END),
                        SUM(CASE WHEN mc.match_datetime >= '2024-07-01' AND mc.match_datetime < '2025-07-01' THEN r.time ELSE 0 END),
                        SUM(CASE WHEN mc.match_datetime >= '2025-07-01' THEN r."xG" ELSE 0 END),
                        SUM(CASE WHEN mc.match_datetime >= '2025-07-01' THEN r.time ELSE 0 END),
                        SUM(CASE WHEN mc.match_datetime >= '2023-07-01' AND mc.match_datetime < '2024-07-01' THEN r."xA" ELSE 0 END),
                        SUM(CASE WHEN mc.match_datetime >= '2024-07-01' AND mc.match_datetime < '2025-07-01' THEN r."xA" ELSE 0 END),
                        SUM(CASE WHEN mc.match_datetime >= '2025-07-01' THEN r."xA" ELSE 0 END)
                    FROM rosters r
                    JOIN matchcalendar mc ON r.match_id = mc.id
                    WHERE r.player ILIKE :n
                """), {"n": player_name})).fetchone()

                def s90(xg_val, min_val):
                    return round(per90(safe_float(xg_val), max(safe_float(min_val), 1)), 2)

                if trend_row:
                    trend_xg = [s90(trend_row[0], trend_row[1]), s90(trend_row[2], trend_row[3]), s90(trend_row[4], trend_row[5])]
                    trend_xa = [s90(trend_row[6], trend_row[1]), s90(trend_row[7], trend_row[3]), s90(trend_row[8], trend_row[5])]
            except Exception as e5:
                logger.warning(f"trend query failed for '{player_name}': {e5}")

            # 6. Radar percentili (query opzionale — fallback graceful)
            radar = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            try:
                distrib_rows = (await conn.execute(text("""
                    SELECT SUM("xG"), SUM("xA"), SUM("xGChain"), SUM("xGBuildup"), SUM(shots), SUM(time)
                    FROM rosters
                    GROUP BY player
                    HAVING SUM(time) > 500
                """))).fetchall()

                def radar_pct(my_total, col_idx):
                    dist = [per90(safe_float(row[col_idx]), max(safe_float(row[5]), 1)) for row in distrib_rows]
                    return percentile_rank(per90(my_total, mins), dist)

                radar = [
                    radar_pct(xg,    0),
                    radar_pct(xa,    1),
                    radar_pct(sh,    4),
                    radar_pct(chain, 2),
                    radar_pct(build, 3),
                    0.0,
                ]
            except Exception as e6:
                logger.warning(f"radar query failed for '{player_name}': {e6}")

            # 7. Costruzione risposta piatta per finder.html
            eff = round(g / xg, 2) if xg > 0 else 0.0

            return {
                "name":       r[0],
                "team":       team_name,
                "league":     league_name,
                "age":        "--",
                "foot":       "--",
                "mins":       int(mins),
                "role":       r[1] or "N/A",
                "ai_verdict": (
                    f"Giocatore con {int(mins)} minuti in {league_name}. "
                    f"xG totale {round(xg, 2)} vs {int(g)} gol reali "
                    f"(efficienza {eff}x). Field Tilt squadra: {tilt}%."
                ),
                "team_poss":  f"{tilt}% Field Tilt",
                "team_ppda":  tsi_label,
                "xg90":       round(per90(xg,    mins), 3),
                "eff":        eff,
                "xa90":       round(per90(xa,    mins), 3),
                "shots90":    round(per90(sh,    mins), 2),
                "kp90":       round(per90(kp,    mins), 2),
                "chain":      round(per90(chain, mins), 3),
                "build":      round(per90(build, mins), 3),
                "cards":      f"{yc}/{rc}",
                "dna":        dna,
                "radar":      radar,
                "trend_xg":   trend_xg,
                "trend_xa":   trend_xa,
            }

    except Exception as e:
        logger.error(f"player profile error '{player_name}': {e}")
        return {"error": str(e)}


# ── 5. TIRI DEL GIOCATORE ─────────────────────────────────────────────────────

@app.get("/api/shots/{player_name}")
async def get_player_shots(player_name: str):
    """Lista tiri del giocatore per la Shot Map (coordinate X/Y, xG, result)."""
    try:
        async with engine.connect() as conn:
            res = await conn.execute(text("""
                SELECT minute, "xG", result, "X", "Y", situation,
                       COALESCE("shotType", shot_type) AS shot_type
                FROM shots
                WHERE player ILIKE :n
                ORDER BY minute ASC
            """), {"n": player_name})
            return [
                {
                    "minute":    r[0],
                    "xG":        safe_float(r[1]),
                    "result":    r[2] or "",
                    "X":         safe_float(r[3]),
                    "Y":         safe_float(r[4]),
                    "situation": r[5] or "Open Play",
                    "shotType":  r[6] or "",
                }
                for r in res.fetchall()
            ]
    except Exception as e:
        logger.error(f"shots error '{player_name}': {e}")
        return []


# ── 6. SOTTOVALUTATI ──────────────────────────────────────────────────────────

@app.get("/api/undervalued")
async def get_undervalued(
    category: str = Query("generale"),
    league_id: int = Query(0),
    size: int = Query(50),
):
    """
    Analisi sottovalutati per categoria. Filtro opzionale per lega.
    Categorie: generale, bomber, registi, motori, costruttori, sprecatori, trap_over
    """
    try:
        # Join con matchcalendar solo se filtro lega attivo
        join_clause  = "JOIN matchcalendar mc ON rosters.match_id = mc.id" if league_id > 0 else ""
        where_clause = "WHERE mc.league_id = :lid" if league_id > 0 else ""
        params: dict = {"size": size}
        if league_id > 0:
            params["lid"] = league_id

        # Alias lowercase (PostgreSQL abbassa gli alias non quotati: AS xG → xg)
        # position: MAX(CASE...) esclude 'Sub' per mostrare il ruolo reale
        pos_expr = "MAX(CASE WHEN UPPER(TRIM(rosters.position)) NOT IN ('SUB','') AND rosters.position IS NOT NULL THEN rosters.position END) AS position"

        queries = {
            "generale": f"""
                SELECT rosters.player, {pos_expr},
                       SUM(rosters.time) AS time, SUM(rosters.goals) AS goals,
                       SUM(rosters."xG") AS xg,
                       SUM(rosters."xG") - SUM(rosters.goals) AS xg_debt
                FROM rosters {join_clause} {where_clause}
                GROUP BY rosters.player
                HAVING SUM(rosters.time) > 500
                   AND SUM(rosters."xG") > SUM(rosters.goals)
                   AND SUM(rosters."xG") > 0.5
                ORDER BY xg_debt DESC
                LIMIT :size
            """,
            "bomber": f"""
                SELECT rosters.player, {pos_expr},
                       SUM(rosters.time) AS time, SUM(rosters.goals) AS goals,
                       SUM(rosters."xG") AS xg,
                       SUM(rosters."xG") - SUM(rosters.goals) AS xg_debt
                FROM rosters {join_clause} {where_clause}
                GROUP BY rosters.player
                HAVING SUM(rosters.time) > 500
                   AND SUM(rosters."xG") - SUM(rosters.goals) > 2.0
                ORDER BY xg_debt DESC
                LIMIT :size
            """,
            "registi": f"""
                SELECT rosters.player, {pos_expr},
                       SUM(rosters.time) AS time, SUM(rosters.goals) AS goals,
                       SUM(rosters."xG") AS xg,
                       SUM(rosters."xA") - SUM(rosters.assists) AS xg_debt
                FROM rosters {join_clause} {where_clause}
                GROUP BY rosters.player
                HAVING SUM(rosters.time) > 500
                   AND SUM(rosters."xA") - SUM(rosters.assists) > 1.5
                ORDER BY xg_debt DESC
                LIMIT :size
            """,
            "motori": f"""
                SELECT rosters.player, {pos_expr},
                       SUM(rosters.time) AS time, SUM(rosters.goals) AS goals,
                       SUM(rosters."xG") AS xg,
                       SUM(rosters."xGChain") / NULLIF(SUM(rosters.time), 0) * 90 AS xg_debt
                FROM rosters {join_clause} {where_clause}
                GROUP BY rosters.player
                HAVING SUM(rosters.time) > 500
                   AND SUM(rosters."xGChain") / NULLIF(SUM(rosters.time), 0) * 90 > 0.4
                ORDER BY xg_debt DESC
                LIMIT :size
            """,
            "costruttori": f"""
                SELECT rosters.player, {pos_expr},
                       SUM(rosters.time) AS time, SUM(rosters.goals) AS goals,
                       SUM(rosters."xG") AS xg,
                       SUM(rosters."xGBuildup") / NULLIF(SUM(rosters.time), 0) * 90 AS xg_debt
                FROM rosters {join_clause} {where_clause}
                GROUP BY rosters.player
                HAVING SUM(rosters.time) > 500
                   AND SUM(rosters."xGBuildup") / NULLIF(SUM(rosters.time), 0) * 90 > 0.3
                ORDER BY xg_debt DESC
                LIMIT :size
            """,
            "sprecatori": f"""
                SELECT rosters.player, {pos_expr},
                       SUM(rosters.time) AS time, SUM(rosters.goals) AS goals,
                       SUM(rosters."xG") AS xg,
                       SUM(rosters."xG") - SUM(rosters.goals) AS xg_debt
                FROM rosters {join_clause} {where_clause}
                GROUP BY rosters.player
                HAVING SUM(rosters.time) > 500
                   AND SUM(rosters."xG") > 3
                   AND SUM(rosters.goals)::float / NULLIF(SUM(rosters."xG"), 0) < 0.5
                ORDER BY xg_debt DESC
                LIMIT :size
            """,
            "trap_over": f"""
                SELECT rosters.player, {pos_expr},
                       SUM(rosters.time) AS time, SUM(rosters.goals) AS goals,
                       SUM(rosters."xG") AS xg,
                       SUM(rosters.goals) - SUM(rosters."xG") AS xg_debt
                FROM rosters {join_clause} {where_clause}
                GROUP BY rosters.player
                HAVING SUM(rosters.time) > 500
                   AND SUM(rosters.goals) > SUM(rosters."xG") * 1.5
                   AND SUM(rosters."xG") > 1.0
                ORDER BY xg_debt DESC
                LIMIT :size
            """,
        }

        sql = queries.get(category, queries["generale"])

        async with engine.connect() as conn:
            res = await conn.execute(text(sql), params)
            rows = res.mappings().all()

        return [
            {
                "player":   row["player"],
                "position": row.get("position") or "N/A",
                "time":     int(row["time"] or 0),
                "goals":    int(row["goals"] or 0),
                "xG":       round(safe_float(row["xg"]), 2),
                "xg_debt":  round(safe_float(row["xg_debt"]), 2),
            }
            for row in rows
        ]

    except Exception as e:
        logger.error(f"undervalued error (category={category}): {e}")
        return {"error": str(e)}


# ── 7. HEAD TO HEAD ───────────────────────────────────────────────────────────

@app.get("/api/h2h")
async def head_to_head(p1: str = Query(...), p2: str = Query(...)):
    """
    Confronto diretto tra due giocatori.
    Ritorna xG/90, xA/90 e radar percentili per Chart.js.
    """
    async def get_player_data(conn, name: str) -> dict:
        r = (await conn.execute(text("""
            SELECT SUM("xG"), SUM("xA"), SUM("xGChain"), SUM("xGBuildup"),
                   SUM(shots), SUM(time), SUM(goals), SUM(assists)
            FROM rosters
            WHERE player ILIKE :n
        """), {"n": f"%{name}%"})).fetchone()

        if not r or not r[5]:
            return {"xg": 0.0, "xa": 0.0, "radar": [0, 0, 0, 0, 0, 0]}

        xg, xa, chain, build, sh, mins, g, a = [safe_float(x) for x in r]
        mins = max(mins, 1.0)

        # Percentili vs distribuzione globale
        distrib = (await conn.execute(text("""
            SELECT SUM("xG"), SUM("xA"), SUM("xGChain"), SUM("xGBuildup"), SUM(shots), SUM(time)
            FROM rosters
            GROUP BY player
            HAVING SUM(time) > 500
        """))).fetchall()

        def pct(my_val, col):
            dist = [per90(safe_float(row[col]), max(safe_float(row[5]), 1)) for row in distrib]
            return percentile_rank(per90(my_val, mins), dist)

        return {
            "xg":   round(per90(xg, mins), 3),
            "xa":   round(per90(xa, mins), 3),
            "radar": [
                pct(xg,    0),  # Finishing
                pct(xa,    1),  # Creation
                pct(sh,    4),  # Dribbling (shots proxy)
                pct(chain, 2),  # xGChain
                pct(build, 3),  # Link-up
                0.0,             # Defense
            ],
        }

    try:
        async with engine.connect() as conn:
            d1 = await get_player_data(conn, p1)
            d2 = await get_player_data(conn, p2)
        return {"p1": d1, "p2": d2}
    except Exception as e:
        logger.error(f"h2h error: {e}")
        return {"error": str(e)}


# ── 8. CLONI / REPLACEMENT ────────────────────────────────────────────────────

@app.get("/replacement/{player_name}")
async def get_clones(player_name: str):
    """
    Player Similarity Engine con distanza euclidea sui percentili p90.
    Più preciso della correlazione di Pearson che dava valori spuriamente alti.
    Ritorna i 5 giocatori più simili al target.
    """
    try:
        async with engine.connect() as conn:
            res = await conn.execute(text("""
                SELECT player,
                       MAX(CASE WHEN UPPER(TRIM(position)) NOT IN ('SUB','') AND position IS NOT NULL
                                THEN position END) AS position,
                       SUM("xG") / NULLIF(SUM(time), 0) * 90  AS xg90,
                       SUM("xA") / NULLIF(SUM(time), 0) * 90  AS xa90,
                       SUM("xGChain") / NULLIF(SUM(time), 0) * 90   AS chain90,
                       SUM("xGBuildup") / NULLIF(SUM(time), 0) * 90 AS build90,
                       SUM(time) AS total_mins
                FROM rosters
                GROUP BY player
                HAVING SUM(time) > 200
            """))
            rows = res.mappings().all()

        if not rows:
            return {"error": "Tabella rosters vuota."}

        df = pd.DataFrame(rows)
        features = ['xg90', 'xa90', 'chain90', 'build90']
        df[features] = df[features].apply(pd.to_numeric).fillna(0)
        df['player'] = df['player'].astype(str).str.strip()

        # Percentili su valori p90 (non sui totali — più equo tra titolari e riserve)
        for f in features:
            df[f'p_{f}'] = df[f].rank(pct=True) * 100

        target = df[df['player'].str.lower().str.contains(player_name.lower(), na=False)]
        if target.empty:
            return {"error": f"Giocatore '{player_name}' non trovato."}

        target_name = target['player'].iloc[0]
        p_cols = [f'p_{f}' for f in features]
        target_vec = target[p_cols].iloc[0].values

        # Distanza euclidea nello spazio percentili (max teorico = sqrt(4*100²) = 200)
        diff = df[p_cols].values - target_vec
        df['distance'] = (diff ** 2).sum(axis=1) ** 0.5
        MAX_DIST = 200.0
        df['similarity_score'] = ((1 - df['distance'] / MAX_DIST) * 100).round(1).clip(0, 100)

        clones = (
            df[df['player'] != target_name]
            .sort_values('similarity_score', ascending=False)
            .head(5)
            # Rinomino per compatibilità con finder.html (si aspetta p_xg, p_xa, ecc.)
            .rename(columns={
                'p_xg90': 'p_xg', 'p_xa90': 'p_xa',
                'p_chain90': 'p_xgchain', 'p_build90': 'p_xgbuildup'
            })
        )

        return clones[['player', 'position', 'p_xg', 'p_xa', 'p_xgchain', 'p_xgbuildup', 'similarity_score']].to_dict(orient='records')

    except Exception as e:
        logger.error(f"clones error '{player_name}': {e}")
        return {"error": str(e)}


# ── DEBUG ────────────────────────────────────────────────────────────────────

@app.get("/debug/player/{player_name}")
async def debug_player(player_name: str):
    """Diagnosi rapida: mostra cosa funziona e cosa no per un giocatore."""
    result = {"player_searched": player_name, "steps": {}}

    async with engine.connect() as conn:

        # Step 1: esiste in rosters?
        try:
            r = (await conn.execute(text(
                "SELECT player, MAX(position), SUM(time), SUM(goals), SUM(\"xG\") FROM rosters WHERE player ILIKE :n GROUP BY player LIMIT 1"
            ), {"n": player_name})).fetchone()
            result["steps"]["1_rosters_basic"] = {"ok": bool(r), "row": list(r) if r else None}
        except Exception as e:
            result["steps"]["1_rosters_basic"] = {"ok": False, "error": str(e)}

        # Step 2: key_passes + yellow/red card
        try:
            r2 = (await conn.execute(text(
                "SELECT SUM(key_passes), SUM(yellow_card), SUM(red_card) FROM rosters WHERE player ILIKE :n"
            ), {"n": player_name})).fetchone()
            result["steps"]["2_rosters_extra_cols"] = {"ok": True, "row": list(r2) if r2 else None}
        except Exception as e:
            result["steps"]["2_rosters_extra_cols"] = {"ok": False, "error": str(e)}

        # Step 3: match_id JOIN
        try:
            r3 = (await conn.execute(text(
                "SELECT mc.id FROM rosters ros JOIN matchcalendar mc ON ros.match_id = mc.id WHERE ros.player ILIKE :n LIMIT 1"
            ), {"n": player_name})).fetchone()
            result["steps"]["3_join_matchcalendar"] = {"ok": bool(r3)}
        except Exception as e:
            result["steps"]["3_join_matchcalendar"] = {"ok": False, "error": str(e)}

        # Step 4: team_type + home/away columns
        try:
            r4 = (await conn.execute(text(
                "SELECT ros.team_type, mc.\"home_xG\", mc.\"away_xG\" FROM rosters ros JOIN matchcalendar mc ON ros.match_id = mc.id WHERE ros.player ILIKE :n LIMIT 1"
            ), {"n": player_name})).fetchone()
            result["steps"]["4_team_type_and_xg_cols"] = {"ok": True, "row": list(r4) if r4 else None}
        except Exception as e:
            result["steps"]["4_team_type_and_xg_cols"] = {"ok": False, "error": str(e)}

        # Step 5: is_completed + ppda/deep
        try:
            r5 = (await conn.execute(text(
                "SELECT mc.is_completed, mc.home_ppda, mc.home_deep FROM matchcalendar mc LIMIT 1"
            ))).fetchone()
            result["steps"]["5_matchcalendar_cols"] = {"ok": True, "row": list(r5) if r5 else None}
        except Exception as e:
            result["steps"]["5_matchcalendar_cols"] = {"ok": False, "error": str(e)}

        # Step 6: shots table
        try:
            r6 = (await conn.execute(text(
                "SELECT COUNT(*) FROM shots WHERE player ILIKE :n"
            ), {"n": player_name})).fetchone()
            result["steps"]["6_shots_count"] = {"ok": True, "count": r6[0] if r6 else 0}
        except Exception as e:
            result["steps"]["6_shots_count"] = {"ok": False, "error": str(e)}

    return result


# ── AVVIO DIRETTO ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000, reload=True)
