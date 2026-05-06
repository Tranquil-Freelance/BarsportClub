"""
Scout Engine — insidecalcio
Implementa OIS, CII, AIR, BCS, FES, PIR, PPI, PSE, SRM
su tabella `rosters` (schema reale confermato).
"""

import math
import logging
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from app.db.database import engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scout", tags=["Scout Engine"])

# ─── Normalizzazione accenti per ricerca robusta ──────────────────────────────
_FROM = "'áàâäãåçéèêëíìîïñóòôöõúùûüýÿøšćž'"
_TO   = "'aaaaaaceeeeiiiinooooouuuuyyoscz'"
NAME_NORM  = f"translate(lower(r.player), {_FROM}, {_TO})"
PARAM_NORM = f"translate(lower(:p),       {_FROM}, {_TO})"
QUERY_NORM = f"translate(lower(:q),       {_FROM}, {_TO})"

# ─── League filter constant ────────────────────────────────────────────────────
SERIE_A_LEAGUE_FILTER = "AND mc.league_id = (SELECT id FROM league WHERE name ILIKE 'Serie A' LIMIT 1)"

# ─── JOIN base usato da tutti gli endpoint ────────────────────────────────────
# team_type ILIKE 'h%' covers 'h', 'H', 'Home' variants
# lt = derived table: one row per player, latest completed match → correct team
_FROM_JOIN = """
    FROM rosters r
    JOIN matchcalendar mc ON mc.id = r.match_id
    AND mc.match_datetime >= '2025-08-01'
    LEFT JOIN player_registry pr ON pr.player_name = r.player
    LEFT JOIN (
        SELECT DISTINCT ON (ctc.player) ctc.player, t.name AS team_name
        FROM (
            SELECT player, team_id, COUNT(*) AS appearances
            FROM (
                SELECT rm.player, rm.home_team_id AS team_id
                FROM (
                    SELECT r_s.player, mc_s.home_team_id, mc_s.away_team_id,
                           ROW_NUMBER() OVER(PARTITION BY r_s.player ORDER BY mc_s.match_datetime DESC) AS rn
                    FROM rosters r_s
                    JOIN matchcalendar mc_s ON mc_s.id = r_s.match_id AND mc_s.is_completed = true
                ) rm WHERE rm.rn <= 3
                UNION ALL
                SELECT rm.player, rm.away_team_id AS team_id
                FROM (
                    SELECT r_s.player, mc_s.home_team_id, mc_s.away_team_id,
                           ROW_NUMBER() OVER(PARTITION BY r_s.player ORDER BY mc_s.match_datetime DESC) AS rn
                    FROM rosters r_s
                    JOIN matchcalendar mc_s ON mc_s.id = r_s.match_id AND mc_s.is_completed = true
                ) rm WHERE rm.rn <= 3
            ) rt
            GROUP BY player, team_id
        ) ctc
        JOIN team t ON t.id = ctc.team_id
        ORDER BY ctc.player, ctc.appearances DESC
    ) lt ON lt.player = r.player
"""

# ─── Colonne aggregate ────────────────────────────────────────────────────────
# Indici risultante: 0=player_name 1=team_name 2=position
#   3=goals 4=npg 5=shots 6=assists 7=key_passes
#   8=xg 9=npxg 10=xa 11=xgchain 12=xgbuildup
#   13=minutes 14=games 15=age 16=image_url
AGG = """
    r.player                                AS player_name,
    MAX(lt.team_name)                       AS team_name,
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
    COUNT(DISTINCT r.match_id)              AS games,
    MAX(pr.age)                             AS age,
    MAX(pr.image_url)                       AS image_url
"""


# ═══════════════════════════════════════════════════════════════════════════════
# METRICHE — implementazione fedele al documento
# ═══════════════════════════════════════════════════════════════════════════════

def offensive_impact(xg: float, xa: float, xgchain: float, shots: float) -> float:
    """OIS = 0.40·xG + 0.30·xA + 0.20·xGChain + 0.10·Shots  (valori per90)"""
    return 0.40 * xg + 0.30 * xa + 0.20 * xgchain + 0.10 * shots


def creative_influence(xa: float, key_passes: float, xgbuildup: float) -> float:
    """CII = 0.50·xA + 0.30·KeyPasses + 0.20·xGBuildup  (valori per90)"""
    return 0.50 * xa + 0.30 * key_passes + 0.20 * xgbuildup


def attacking_involvement(xgchain_total: float, minutes: float) -> float:
    """AIR = xGChain / Minutes"""
    return xgchain_total / max(minutes, 1.0)


def buildup_contribution(xgbuildup_total: float, minutes: float) -> float:
    """BCS = xGBuildup / Minutes"""
    return xgbuildup_total / max(minutes, 1.0)


def finishing_efficiency(goals: float, xg: float) -> float:
    """FES = Goals / xG"""
    if xg == 0:
        return 0.0
    return goals / xg


def player_impact(ois: float, cii: float, air: float, bcs: float, fes: float) -> float:
    """PIR = 0.30·OIS + 0.25·CII + 0.20·AIR + 0.15·BCS + 0.10·FES"""
    return 0.30 * ois + 0.25 * cii + 0.20 * air + 0.15 * bcs + 0.10 * fes


def player_potential(xg_p90: float, xa_p90: float, xgchain_p90: float,
                     xgbuildup_p90: float, xg_total: float, goals_total: float,
                     xa_total: float, assists_total: float, age: float = 23.0) -> float:
    """
    PPI = 0.50·UPS + 0.30·ConversionGap + 0.20·AgeFactor
    UPS = 0.35·xG/90 + 0.25·xA/90 + 0.20·xGChain/90 + 0.20·xGBuildup/90
    ConversionGap = (xG - Goals) + (xA - Assists)
    AgeFactor = 1 - (Age / 28)
    """
    ups = (0.35 * xg_p90 + 0.25 * xa_p90
           + 0.20 * xgchain_p90 + 0.20 * xgbuildup_p90)
    conversion_gap = (xg_total - goals_total) + (xa_total - assists_total)
    age_factor     = 1.0 - (age / 28.0)
    return 0.50 * ups + 0.30 * conversion_gap + 0.20 * age_factor


def market_value_gap(pir: float, goals: float, assists: float, xg: float, xa: float) -> float:
    """
    MVGI = PIR - ln(1 + estimated_market_value)
    estimated_market_value (millions) = (goals * 0.5 + assists * 0.3 + xg * 0.8 + xa * 0.5)
    """
    estimated_mv = max(0.1, goals * 0.5 + assists * 0.3 + xg * 0.8 + xa * 0.5)
    return pir - math.log(1 + estimated_mv)


def weighted_euclidean_distance(vec_a: list[float], vec_b: list[float], weights: list[float]) -> float:
    """Distance = √Σ(w_i * (a_i - b_i))²"""
    return math.sqrt(sum(w * ((a - b) ** 2) for a, b, w in zip(vec_a, vec_b, weights)))


def similarity_score(distance: float) -> float:
    """Similarity = 1 / (1 + Distance)"""
    return 1.0 / (1.0 + distance)


def percentile_rank(value: float, distribution: list[float]) -> float:
    """Percentile = (rank / total) × 100"""
    if not distribution:
        return 0.0
    rank = sum(v < value for v in distribution)
    return round((rank / len(distribution)) * 100, 1)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: converte una riga SQL nel dizionario completo con tutte le metriche
# ═══════════════════════════════════════════════════════════════════════════════

def _build_player(row) -> dict:
    goals      = float(row[3]  or 0)
    npg        = float(row[4]  or 0)
    shots      = float(row[5]  or 0)
    assists    = float(row[6]  or 0)
    key_passes = float(row[7]  or 0)
    xg         = float(row[8]  or 0)
    npxg       = float(row[9]  or 0)
    xa         = float(row[10] or 0)
    xgchain    = float(row[11] or 0)
    xgbuildup  = float(row[12] or 0)
    minutes    = float(row[13] or 1)
    games      = int(row[14]   or 0)

    # ESTREZIONE ETÀ E FOTO CON GESTIONE ERRORI
    raw_age   = row[15] if len(row) > 15 else None
    age       = float(raw_age) if raw_age is not None else 23.0
    image_url = row[16] if len(row) > 16 else None

    f90 = 90.0 / max(minutes, 1.0)

    # Valori per 90
    xg_p90        = xg        * f90
    npxg_p90      = npxg      * f90
    xa_p90        = xa        * f90
    xgchain_p90   = xgchain   * f90
    xgbuildup_p90 = xgbuildup * f90
    shots_p90     = shots     * f90
    key_passes_p90= key_passes* f90
    goals_p90     = goals     * f90
    assists_p90   = assists   * f90

    # Punteggi compositi (tutti calcolati su p90 dove previsto dal doc)
    ois = offensive_impact(xg_p90, xa_p90, xgchain_p90, shots_p90)
    cii = creative_influence(xa_p90, key_passes_p90, xgbuildup_p90)
    air = attacking_involvement(xgchain, minutes)
    bcs = buildup_contribution(xgbuildup, minutes)
    fes = finishing_efficiency(goals, xg)
    pir = player_impact(ois, cii, air, bcs, fes)
    mvgi = market_value_gap(pir, goals, assists, xg, xa)

    # PPI ORA USA L'ETÀ REALE INVECE DEL DEFAULT 23
    ppi = player_potential(xg_p90, xa_p90, xgchain_p90, xgbuildup_p90,
                           xg, goals, xa, assists, age=age)

    # Vettore PSE (player similarity)
    pse_vector = [xg_p90, xa_p90, xgchain_p90, xgbuildup_p90, shots_p90]

    return {
        "name":     row[0],
        "team":     row[1],
        "position": row[2] or "N/D",
        "games":    games,
        "minutes":  round(minutes),
        "age":      int(age) if raw_age is not None else "N/D",
        "image_url": image_url,
        "totals": {
            "goals":      round(goals,      1),
            "npg":        round(npg,        1),
            "shots":      round(shots,      1),
            "assists":    round(assists,    1),
            "key_passes": round(key_passes, 1),
            "xg":         round(xg,         2),
            "npxg":       round(npxg,       2),
            "xa":         round(xa,         2),
            "xgchain":    round(xgchain,    2),
            "xgbuildup":  round(xgbuildup,  2),
        },
        "p90": {
            "goals":      round(goals_p90,       2),
            "shots":      round(shots_p90,       2),
            "assists":    round(assists_p90,     2),
            "key_passes": round(key_passes_p90,  2),
            "xg":         round(xg_p90,          3),
            "npxg":       round(npxg_p90,        3),
            "xa":         round(xa_p90,          3),
            "xgchain":    round(xgchain_p90,     3),
            "xgbuildup":  round(xgbuildup_p90,   3),
        },
        "scores": {
            "OIS": round(ois, 4),
            "CII": round(cii, 4),
            "AIR": round(air, 5),
            "BCS": round(bcs, 5),
            "FES": round(fes, 3),
            "PIR": round(pir, 4),
            "MVGI": round(mvgi, 4),
            "PPI": round(ppi, 4),
        },
        "_pse_vector": pse_vector,  # usato internamente per similarity
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: /leaders  — top scorers e architects (homepage classifica)
# ═══════════════════════════════════════════════════════════════════════════════
@router.get("/leaders")
async def get_leaders(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Top scorer/architect paginati. limit max 100, offset per scorrere."""
    try:
        async with engine.connect() as conn:
            rows = (await conn.execute(
                text(f"""
                    SELECT {AGG}
                    {_FROM_JOIN}
                    GROUP BY r.player
                    HAVING SUM(r.time::float) >= 500
                """),
            )).fetchall()

        players = []
        for row in rows:
            p = _build_player(row)
            p.pop("_pse_vector", None)
            players.append(p)

        scorers_all    = sorted(players, key=lambda x: x["totals"]["goals"],   reverse=True)
        architects_all = sorted(players, key=lambda x: x["totals"]["assists"], reverse=True)

        return {
            "scorers":    [
                {"name": p["name"], "team": p["team"],
                 "value": p["totals"]["goals"],
                 "stat": f"xG {p['p90']['xg']:.3f}/90"}
                for p in scorers_all[offset: offset + limit]
            ],
            "architects": [
                {"name": p["name"], "team": p["team"],
                 "value": p["totals"]["assists"],
                 "stat": f"xA {p['p90']['xa']:.3f}/90"}
                for p in architects_all[offset: offset + limit]
            ],
            "total":  len(players),
            "limit":  limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"leaders error: {e}")
        return {"scorers": [], "architects": [], "total": 0, "limit": limit, "offset": offset}


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: /search  — ricerca giocatori per nome (accent-insensitive, prefix)
# ═══════════════════════════════════════════════════════════════════════════════
@router.get("/search")
async def search_player(
    q: str,
    limit: int = Query(default=10, ge=1, le=50),
):
    if len(q.strip()) < 2:
        return {"results": []}
    try:
        async with engine.connect() as conn:
            res = await conn.execute(
                text(f"""
                    SELECT DISTINCT ON (r.player) r.player, t.name AS team
                    FROM rosters r
                    JOIN matchcalendar mc ON mc.id = r.match_id
                    AND mc.league_id = (SELECT id FROM league WHERE name ILIKE 'Serie A' LIMIT 1)
                    AND mc.match_datetime >= '2025-08-01'
                    JOIN team t ON t.id = CASE
                        WHEN r.team_type ILIKE 'h%' THEN mc.home_team_id
                        ELSE mc.away_team_id
                    END
                    WHERE {NAME_NORM} ILIKE '%' || {QUERY_NORM} || '%'
                    ORDER BY r.player
                    LIMIT :lim
                """),
                {"q": q.strip(), "lim": limit},
            )
            return {"results": [{"name": r[0], "team": r[1] or ""} for r in res.fetchall()]}
    except Exception as e:
        logger.error(f"search error: {e}")
        return {"results": []}


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: /dna  — profilo completo con tutte le metriche
# ═══════════════════════════════════════════════════════════════════════════════
@router.get("/dna")
async def player_dna(player_name: str):
    try:
        async with engine.connect() as conn:
            res = await conn.execute(
                text(f"""
                    SELECT {AGG}
                    {_FROM_JOIN}
                    WHERE {NAME_NORM} ILIKE {PARAM_NORM}
                    GROUP BY r.player
                    ORDER BY MAX(mc.match_datetime) DESC
                    LIMIT 1
                """),
                {"p": f"%{player_name}%"},
            )
            row = res.fetchone()
            if not row:
                return {"dna": None}
            return {"dna": _build_player(row)}
    except Exception as e:
        logger.error(f"dna error: {e}")
        return {"dna": None}


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: /replacement  — Player Similarity Engine (PSE)
# ═══════════════════════════════════════════════════════════════════════════════
@router.get("/replacement")
async def find_replacement(player_name: str):
    try:
        async with engine.connect() as conn:
            meta = await conn.execute(
                text(f"""
                    SELECT MAX(r.position)
                    {_FROM_JOIN}
                    WHERE {NAME_NORM} ILIKE {PARAM_NORM}
                """),
                {"p": f"%{player_name}%"},
            )
            meta_row = meta.fetchone()
            if not meta_row or not meta_row[0]:
                raise HTTPException(status_code=404, detail="Giocatore non trovato")
            position = meta_row[0] or ""

            tgt_res = await conn.execute(
                text(f"""
                    SELECT {AGG}
                    {_FROM_JOIN}
                    WHERE {NAME_NORM} ILIKE {PARAM_NORM}
                    GROUP BY r.player
                    ORDER BY MAX(mc.match_datetime) DESC
                    LIMIT 1
                """),
                {"p": f"%{player_name}%"},
            )
            tgt_row = tgt_res.fetchone()
            if not tgt_row:
                raise HTTPException(status_code=404, detail="Giocatore non trovato")
            target = _build_player(tgt_row)

            position_groups = {
                'GK': 'GK',
                'DC': 'DF', 'DL': 'DF', 'DR': 'DF', 'DMC': 'DF', 'DML': 'DF', 'DMR': 'DF',
                'MC': 'MF', 'ML': 'MF', 'MR': 'MF', 'AMC': 'MF', 'AML': 'MF', 'AMR': 'MF',
                'FW': 'FW', 'FWL': 'FW', 'FWR': 'FW',
                'Sub': 'FW'
            }
            group = position_groups.get(position, position)
            allowed_positions = tuple(p for p, g in position_groups.items() if g == group)

            # IL FIX DEL CENSIMENTO: Aggiunto filtro per giocatori attivi in questa stagione
            pool_res = await conn.execute(
                text(f"""
                    SELECT {AGG}
                    {_FROM_JOIN}
                    WHERE r.position = ANY(CAST(:allowed_positions AS text[]))
                    GROUP BY r.player
                    HAVING SUM(r.time::float) >= 600 
                       AND MAX(mc.match_datetime) >= '2025-08-01'
                """),
                {"allowed_positions": list(allowed_positions)},
            )
            pool_rows = pool_res.fetchall()

        target_vec = target["_pse_vector"] 
        
        # IL FIX ALGORITMICO: Pesi specifici per ruolo
        if group == 'FW':
            role_weights = [3.0, 1.0, 0.5, 0.1, 2.0]
        elif group == 'MF':
            role_weights = [1.0, 2.5, 2.0, 1.5, 0.5]
        elif group == 'DF' or group == 'GK':
            role_weights = [0.2, 0.5, 1.5, 3.0, 0.1]
        else:
            role_weights = [1.0, 1.0, 1.0, 1.0, 1.0]

        results = []
        for row in pool_rows:
            p = _build_player(row)
            if p["name"].lower() == target["name"].lower():
                continue
            
            # Calcolo ponderato
            dist = weighted_euclidean_distance(target_vec, p["_pse_vector"], role_weights)
            sim  = similarity_score(dist)
            
            p["similarity"] = round(sim, 4)
            p["similarity_pct"] = round(sim * 100, 1)
            results.append(p)

        results.sort(key=lambda x: x["similarity"], reverse=True)
        substitutes = results[:50]

        target.pop("_pse_vector", None)
        for s in substitutes:
            s.pop("_pse_vector", None)

        return {"target": target, "substitutes": substitutes}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"replacement error: {e}")
        return {"target": None, "substitutes": []}


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: /compare  — confronto diretto tra due giocatori (tutte le metriche)
# ═══════════════════════════════════════════════════════════════════════════════
@router.get("/compare")
async def compare_players(p1: str, p2: str):
    try:
        async with engine.connect() as conn:
            q = text(f"""
                SELECT {AGG}
                {_FROM_JOIN}
                WHERE {NAME_NORM} ILIKE {PARAM_NORM}
                GROUP BY r.player
                ORDER BY MAX(mc.match_datetime) DESC
                LIMIT 1
            """)
            r1 = (await conn.execute(q, {"p": f"%{p1}%"})).fetchone()
            r2 = (await conn.execute(q, {"p": f"%{p2}%"})).fetchone()

        data = []
        for row in [r1, r2]:
            if row:
                p = _build_player(row)
                p.pop("_pse_vector", None)
                data.append(p)
        return {"data": data}
    except Exception as e:
        logger.error(f"compare error: {e}")
        return {"data": []}


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: /radar  — Scouting Radar Model (SRM) con percentili per posizione
# ═══════════════════════════════════════════════════════════════════════════════
@router.get("/radar")
async def scouting_radar(player_name: str):
    try:
        async with engine.connect() as conn:
            tgt_res = await conn.execute(
                text(f"""
                    SELECT {AGG}
                    {_FROM_JOIN}
                    WHERE {NAME_NORM} ILIKE {PARAM_NORM}
                    GROUP BY r.player
                    ORDER BY MAX(mc.match_datetime) DESC
                    LIMIT 1
                """),
                {"p": f"%{player_name}%"},
            )
            tgt_row = tgt_res.fetchone()
            if not tgt_row:
                return {"radar": None}
            target = _build_player(tgt_row)
            position = target["position"]

            position_groups = {
                'GK': 'GK',
                'DC': 'DF', 'DL': 'DF', 'DR': 'DF', 'DMC': 'DF', 'DML': 'DF', 'DMR': 'DF',
                'MC': 'MF', 'ML': 'MF', 'MR': 'MF', 'AMC': 'MF', 'AML': 'MF', 'AMR': 'MF',
                'FW': 'FW', 'FWL': 'FW', 'FWR': 'FW',
                'Sub': 'FW'
            }
            group = position_groups.get(position, position)
            allowed_positions = tuple(p for p, g in position_groups.items() if g == group)

            dist_res = await conn.execute(
                text(f"""
                    SELECT {AGG}
                    {_FROM_JOIN}
                    WHERE r.position = ANY(CAST(:allowed_positions AS text[]))
                    GROUP BY r.player
                    HAVING SUM(r.time::float) >= 600
                       AND MAX(mc.match_datetime) >= '2025-08-01'
                """),
                {"allowed_positions": list(allowed_positions)},
            )
            pool = [_build_player(r) for r in dist_res.fetchall()]

        metrics = ["xg", "goals", "xa", "xgchain", "shots"]
        distributions = {m: [p["p90"][m] for p in pool] for m in metrics}
        percentiles = {
            m: percentile_rank(target["p90"][m], distributions[m])
            for m in metrics
        }

        target.pop("_pse_vector", None)
        return {
            "radar": {
                "player": target,
                "percentiles": percentiles,
                "axes": {
                    "xg":      {"label": "xG/90",     "value": target["p90"]["xg"],      "percentile": percentiles["xg"]},
                    "goals":   {"label": "Goals/90",  "value": target["p90"]["goals"],   "percentile": percentiles["goals"]},
                    "xa":      {"label": "xA/90",     "value": target["p90"]["xa"],      "percentile": percentiles["xa"]},
                    "xgchain": {"label": "xGChain/90", "value": target["p90"]["xgchain"], "percentile": percentiles["xgchain"]},
                    "shots":   {"label": "Shots/90",   "value": target["p90"]["shots"],   "percentile": percentiles["shots"]},
                },
                "pool_size": len(pool),
            }
        }
    except Exception as e:
        logger.error(f"radar error: {e}")
        return {"radar": None}


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: /discover  — Talent Radar: top talenti per PPI nella stagione corrente
# ═══════════════════════════════════════════════════════════════════════════════
@router.get("/discover")
async def discover_talent(pos: str = "ALL", limit: int = 20):
    try:
        async with engine.connect() as conn:
            pos_filter = ""
            params: dict = {}
            if pos.upper() != "ALL":
                pos_filter = "AND r.position ILIKE :pos_val"
                params["pos_val"] = f"%{pos.upper()}%"

            res = await conn.execute(
                text(f"""
                    SELECT {AGG}
                    {_FROM_JOIN}
                    {pos_filter}
                    GROUP BY r.player
                    HAVING SUM(r.time::float) >= 700
                """),
                params,
            )
            rows = res.fetchall()

        players = []
        for row in rows:
            p = _build_player(row)
            p.pop("_pse_vector", None)
            players.append(p)

        players.sort(key=lambda x: x["scores"]["PPI"], reverse=True)
        return {"talents": players[:limit], "season": 2025}

    except Exception as e:
        logger.error(f"discover error: {e}")
        return {"talents": [], "season": 0}


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: /talent-radar  — 5 intelligence categories across Top 5 leagues
# ═══════════════════════════════════════════════════════════════════════════════

_LEAGUE_NAMES = {
    "serie_a":   "Serie A",
    "pl":        "Premier League",
    "bundesliga":"Bundesliga",
    "liga":      "La Liga",
    "ligue1":    "Ligue 1",
}

_TALENT_CATEGORIES = {
    "diamonds": {
        "having": """
            SUM(r.time::float) BETWEEN 300 AND 1200
            AND SUM(r."xGChain"::float) / NULLIF(SUM(r.time::float), 0) * 90 > 0.40
        """,
        "sort_key": lambda p: p["p90"]["xgchain"],
    },
    "moneyball": {
        "having": """
            SUM(r."xGBuildup"::float) / NULLIF(SUM(r.time::float), 0) * 90 > 0.20
            AND SUM(r."xG"::float) < 2.0
        """,
        "sort_key": lambda p: p["p90"]["xgbuildup"],
    },
    "engine": {
        "having": """
            SUM(r.key_passes::float) / NULLIF(SUM(r.time::float), 0) * 90 > 1.5
            AND SUM(r."xGBuildup"::float) / NULLIF(SUM(r.time::float), 0) * 90 > 0.15
        """,
        "sort_key": lambda p: p["p90"]["xgbuildup"],
    },
    "unlucky": {
        "having": """
            SUM(r."xG"::float) > 3.0
            AND SUM(r.goals::float) <= 1
        """,
        "sort_key": lambda p: p["totals"]["xg"],
    },
    "overperformers": {
        "having": """
            SUM(r.goals::float) > SUM(r."xG"::float) * 1.5
            AND SUM(r.shots::float) >= 5
        """,
        "sort_key": lambda p: p["totals"]["goals"] - p["totals"]["xg"],
    },
}


def _build_league_filter(league: str) -> str:
    league_name = _LEAGUE_NAMES.get(league.lower(), "Serie A")
    return f"AND mc.league_id = (SELECT id FROM league WHERE name ILIKE '{league_name}' LIMIT 1)"


@router.get("/talent-radar")
async def talent_radar(
    category: str = Query(default="diamonds"),
    league: str = Query(default="serie_a"),
    pos: str = Query(default="ALL"),
    limit: int = Query(default=24, ge=1, le=100),
):
    cat = _TALENT_CATEGORIES.get(category.lower())
    if not cat:
        return {"talents": [], "category": category, "error": "unknown category"}

    league_filter = _build_league_filter(league)
    pos_filter = ""
    params: dict = {}
    if pos.upper() != "ALL":
        pos_filter = "AND r.position ILIKE :pos_val"
        params["pos_val"] = f"%{pos.upper()}%"

    from_join_dynamic = f"""
        FROM rosters r
        JOIN matchcalendar mc ON mc.id = r.match_id
        {league_filter}
        AND mc.match_datetime >= '2025-08-01'
        LEFT JOIN player_registry pr ON pr.player_name = r.player
        LEFT JOIN (
            SELECT DISTINCT ON (ctc.player) ctc.player, t.name AS team_name
            FROM (
                SELECT player, team_id, COUNT(*) AS appearances
                FROM (
                    SELECT rm.player, rm.home_team_id AS team_id
                    FROM (
                        SELECT r_s.player, mc_s.home_team_id, mc_s.away_team_id,
                               ROW_NUMBER() OVER(PARTITION BY r_s.player ORDER BY mc_s.match_datetime DESC) AS rn
                        FROM rosters r_s
                        JOIN matchcalendar mc_s ON mc_s.id = r_s.match_id AND mc_s.is_completed = true
                    ) rm WHERE rm.rn <= 3
                    UNION ALL
                    SELECT rm.player, rm.away_team_id AS team_id
                    FROM (
                        SELECT r_s.player, mc_s.home_team_id, mc_s.away_team_id,
                               ROW_NUMBER() OVER(PARTITION BY r_s.player ORDER BY mc_s.match_datetime DESC) AS rn
                        FROM rosters r_s
                        JOIN matchcalendar mc_s ON mc_s.id = r_s.match_id AND mc_s.is_completed = true
                    ) rm WHERE rm.rn <= 3
                ) rt
                GROUP BY player, team_id
            ) ctc
            JOIN team t ON t.id = ctc.team_id
            ORDER BY ctc.player, ctc.appearances DESC
        ) lt ON lt.player = r.player
    """

    try:
        async with engine.connect() as conn:
            res = await conn.execute(
                text(f"""
                    SELECT {AGG}
                    {from_join_dynamic}
                    {pos_filter}
                    GROUP BY r.player
                    HAVING {cat['having']}
                """),
                params,
            )
            rows = res.fetchall()

        players = []
        for row in rows:
            p = _build_player(row)
            p.pop("_pse_vector", None)
            players.append(p)

        players.sort(key=cat["sort_key"], reverse=True)
        return {
            "talents": players[:limit],
            "category": category,
            "league": league,
            "total": len(players),
        }

    except Exception as e:
        logger.error(f"talent-radar error [{category}/{league}]: {e}")
        return {"talents": [], "category": category, "league": league, "total": 0}


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT: /report  — report completo con tutti i punteggi e testo
# ═══════════════════════════════════════════════════════════════════════════════
@router.get("/report")
async def scout_report(player_name: str):
    try:
        async with engine.connect() as conn:
            res = await conn.execute(
                text(f"""
                    SELECT {AGG}
                    {_FROM_JOIN}
                    WHERE {NAME_NORM} ILIKE {PARAM_NORM}
                    GROUP BY r.player
                    ORDER BY MAX(mc.match_datetime) DESC
                    LIMIT 1
                """),
                {"p": f"%{player_name}%"},
            )
            row = res.fetchone()
            if not row:
                return {"report": None}

        data = _build_player(row)
        data.pop("_pse_vector", None)

        position = data["position"]
        position_groups = {
            'GK': 'GK',
            'DC': 'DF', 'DL': 'DF', 'DR': 'DF', 'DMC': 'DF', 'DML': 'DF', 'DMR': 'DF',
            'MC': 'MF', 'ML': 'MF', 'MR': 'MF', 'AMC': 'MF', 'AML': 'MF', 'AMR': 'MF',
            'FW': 'FW', 'FWL': 'FW', 'FWR': 'FW',
            'Sub': 'FW'
        }
        group = position_groups.get(position, position)
        allowed_positions = tuple(p for p, g in position_groups.items() if g == group)

        async with engine.connect() as conn2:
            dist_res = await conn2.execute(
                text(f"""
                    SELECT {AGG}
                    {_FROM_JOIN}
                    WHERE r.position = ANY(CAST(:allowed_positions AS text[]))
                    GROUP BY r.player
                    HAVING SUM(r.time::float) >= 600
                       AND MAX(mc.match_datetime) >= '2025-08-01'
                """),
                {"allowed_positions": list(allowed_positions)},
            )
            pool = [_build_player(r) for r in dist_res.fetchall()]

        metrics = ["xg", "goals", "xa", "xgchain", "shots"]
        distributions = {m: [p["p90"][m] for p in pool] for m in metrics}
        percentiles = {m: percentile_rank(data["p90"][m], distributions[m]) for m in metrics}

        data["radar"] = {
            "percentiles": percentiles,
            "axes": {
                "xg":      {"label": "xG/90",     "value": data["p90"]["xg"],      "percentile": percentiles["xg"]},
                "goals":   {"label": "Goals/90",  "value": data["p90"]["goals"],   "percentile": percentiles["goals"]},
                "xa":      {"label": "xA/90",     "value": data["p90"]["xa"],      "percentile": percentiles["xa"]},
                "xgchain": {"label": "xGChain/90", "value": data["p90"]["xgchain"], "percentile": percentiles["xgchain"]},
                "shots":   {"label": "Shots/90",   "value": data["p90"]["shots"],   "percentile": percentiles["shots"]},
            },
            "pool_size": len(pool),
        }

        sc  = data["scores"]
        p90 = data["p90"]

        def _profile_text() -> str:
            lines = [f"{data['name']} ({data['team']}, {data['position']}) — {data['games']} presenze, {data['minutes']} minuti."]
            lines.append(f"PIR: {sc['PIR']:.4f} | OIS: {sc['OIS']:.4f} | CII: {sc['CII']:.4f} | FES: {sc['FES']:.3f}")
            lines.append(f"npxG/90: {p90['npxg']} — xA/90: {p90['xa']} — xGChain/90: {p90['xgchain']}")
            return " | ".join(lines)

        def _strength() -> str:
            if sc["OIS"] > 0.4 and sc["FES"] > 1.0:
                return "Finalizzatore efficiente con alto impatto offensivo."
            if sc["CII"] > sc["OIS"]:
                return "Creatore di gioco superiore alla media. Alto CII indica un contributo associativo eccezionale."
            if sc["AIR"] > 0.01:
                return "Partecipazione offensiva costante."
            return "Profilo bilanciato."

        def _weakness() -> str:
            if p90["xg"] < 0.10:
                return "Basso npxG/90. Produzione di tiri nell'area limitata."
            if p90["xa"] < 0.06:
                return "Scarsa produzione di xA/90."
            if sc["FES"] < 0.80:
                return "FES < 0.80: segna meno di quanto suggeriscano gli xG."
            return "Contributo difensivo fuori dalla zona offensiva da valutare."

        data["report_text"] = {
            "profilo": _profile_text(),
            "forza":   _strength(),
            "limiti":  _weakness(),
        }
        return {"report": data}

    except Exception as e:
        logger.error(f"report error: {e}")
        return {"report": None}


# ═══════════════════════════════════════════════════════════════════════════════
# DRAFT ROUTER  — War Room endpoint
# ═══════════════════════════════════════════════════════════════════════════════

draft_router = APIRouter(prefix="/api/draft", tags=["Fanta Draft"])

_POS_NORMALIZE = {
    "GK": "GK",
    "DC": "DF", "DL": "DF", "DR": "DF", "DMC": "DF", "DML": "DF", "DMR": "DF",
    "MC": "MF", "ML": "MF", "MR": "MF", "AMC": "MF", "AML": "MF", "AMR": "MF",
    "FW": "FW", "FWL": "FW", "FWR": "FW", "Sub": "FW",
}

_DRAFT_POS_FILTER = {
    "GK": ["GK"],
    "DF": ["DC", "DL", "DR", "DMC", "DML", "DMR"],
    "MF": ["MC", "ML", "MR", "AMC", "AML", "AMR"],
    "FW": ["FW", "FWL", "FWR"],
}


@draft_router.get("/players")
async def get_draft_players(
    position: str = Query(default="ALL"),
    limit: int = Query(default=80, ge=1, le=200),
):
    pos_filter_sql = ""
    params: dict = {"lim": limit}

    pos_upper = position.upper()
    if pos_upper != "ALL":
        allowed = _DRAFT_POS_FILTER.get(pos_upper, [])
        if allowed:
            pos_filter_sql = "AND r.position = ANY(CAST(:positions AS text[]))"
            params["positions"] = allowed

    try:
        async with engine.connect() as conn:
            rows = (await conn.execute(
                text(f"""
                    SELECT
                        r.player,
                        MAX(lt.team_name)                                       AS team,
                        MODE() WITHIN GROUP (ORDER BY r.position)
                            FILTER (WHERE r.position NOT IN ('Sub', 'SUB')
                                    AND r.position IS NOT NULL)         AS position,
                        COALESCE(SUM(r.goals::float),       0)          AS goals,
                        COALESCE(SUM(r.assists::float),     0)          AS assists,
                        COALESCE(AVG(r."xG"::float),        0)          AS xg_avg,
                        COALESCE(AVG(r."xA"::float),        0)          AS xa_avg,
                        COALESCE(AVG(r."xGChain"::float),   0)          AS xgchain_avg,
                        COALESCE(AVG(r."xGBuildup"::float), 0)          AS xgbuildup_avg,
                        COALESCE(SUM(r.time::float),        0)          AS minutes
                    {_FROM_JOIN}
                    WHERE mc.is_completed = true {pos_filter_sql}
                    GROUP BY r.player
                    HAVING SUM(r.time::float) >= 450
                    ORDER BY AVG(r."xG"::float) DESC
                    LIMIT :lim
                """),
                params,
            )).fetchall()

        return [
            {
                "player":    row[0],
                "team":      row[1] or "—",
                "position":  _POS_NORMALIZE.get(row[2] or "", "N/D"),
                "goals":     int(float(row[3] or 0)),
                "assists":   int(float(row[4] or 0)),
                "xg":        round(float(row[5] or 0), 3),
                "xa":        round(float(row[6] or 0), 3),
                "xgchain":   round(float(row[7] or 0), 3),
                "xgbuildup": round(float(row[8] or 0), 3),
                "minutes":   int(float(row[9] or 0)),
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"draft players error: {e}")
        return []