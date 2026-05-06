"""
Upcoming Match Preview – FastAPI Router
=========================================
Phase 2 endpoints that expose the Phase 1 preview engine to the frontend.

- GET /api/matches/upcoming   → list of upcoming matches (lightweight)
- GET /api/matches/{id}/preview → full match detail + stats comparison + ai_verdict
- GET /api/matches/{id}/lineups → match lineups (starters & bench) + events
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.db.database import engine as local_engine
from app.services.preview_service import (
    generate_preview_for_match,
    get_last_n_completed_avg,
    get_team_name,
    get_team_season_stats,
)

logger = logging.getLogger("matches_preview")
router = APIRouter(tags=["matches-preview"])


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


def _sanitize(val: Any) -> float:
    """Null‑safe float conversion matching main.py's sanitize_metric."""
    if val is None:
        return 0.0
    try:
        fv = float(val)
        import math
        if math.isnan(fv) or math.isinf(fv):
            return 0.0
        return round(fv, 3)
    except (ValueError, TypeError):
        return 0.0


# ---------------------------------------------------------------------------
# GET /api/matches/upcoming
# ---------------------------------------------------------------------------


@router.get("/matches/upcoming")
async def get_upcoming_matches_list(limit: int = 20):
    """
    Return the next *limit* upcoming matches with team names, date, league.
    Lightweight payload suitable for a ticker / dashboard sidebar.
    """
    now = datetime.now(timezone.utc)
    query = text(
        """
        SELECT
            m.id,
            m.match_datetime,
            l.name          AS league,
            th.id           AS home_id,
            th.name         AS home_team,
            ta.id           AS away_id,
            ta.name         AS away_team,
            m."round",
            m.is_completed
        FROM matchcalendar m
        JOIN league l  ON m.league_id = l.id
        JOIN team   th ON m.home_team_id = th.id
        JOIN team   ta ON m.away_team_id = ta.id
        WHERE m.is_completed = false
          AND m.match_datetime > :now
        ORDER BY m.match_datetime ASC
        LIMIT :limit
        """
    )
    try:
        async with local_engine.connect() as conn:
            rows = await conn.execute(query, {"now": now, "limit": limit})
            results: List[Dict[str, Any]] = []
            for r in rows:
                # ── NORMALIZZAZIONE NOMI PER IL FRONTEND ──
                raw_league = r[2]
                if raw_league and raw_league.lower() == "la liga":
                    normalized_league = "La Liga"
                else:
                    normalized_league = raw_league

                results.append(
                    {
                        "id": r[0],
                        "date": r[1].isoformat() if r[1] else None,
                        "league": normalized_league,
                        "home_id": r[3],
                        "home_team": r[4],
                        "away_id": r[5],
                        "away_team": r[6],
                        "round": r[7],
                        "is_completed": r[8],
                    }
                )
            return {"matches": results, "count": len(results)}
    except Exception as exc:
        logger.exception("Failed to fetch upcoming matches")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# GET /api/matches/{match_id}/preview
# ---------------------------------------------------------------------------


async def _generate_verdict_bg(match_id: int) -> None:
    """Background task: generate and persist AI verdict for a match."""
    async_session_factory = sessionmaker(
        local_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        try:
            await generate_preview_for_match(match_id, session)
            await session.commit()
        except Exception:
            logger.exception("Background verdict generation failed for match %s", match_id)


@router.post("/matches/{match_id}/verdict", status_code=202)
async def trigger_verdict_generation(match_id: int, background_tasks: BackgroundTasks):
    """
    Trigger AI verdict generation for a match. Non-blocking — returns 202 immediately.
    """
    background_tasks.add_task(_generate_verdict_bg, match_id)
    return {"status": "accepted", "match_id": match_id}


@router.get("/matches/{match_id}/preview")
async def get_match_preview(match_id: int, background_tasks: BackgroundTasks):
    """
    Return full match detail + computed stats comparison + cached ai_verdict.
    """
    try:
        async with local_engine.connect() as conn:
            header_q = text(
                """
                SELECT
                    m.id, m.match_datetime,
                    l.name          AS league,
                    th.id           AS home_id,  th.name AS home_team,
                    ta.id           AS away_id,  ta.name AS away_team,
                    m."round",
                    m.home_goals, m.away_goals,
                    m."home_xG",   m."away_xG",
                    m.is_completed,
                    m.ai_verdict
                FROM matchcalendar m
                JOIN league l  ON m.league_id = l.id
                JOIN team   th ON m.home_team_id = th.id
                JOIN team   ta ON m.away_team_id = ta.id
                WHERE m.id = :id
                """
            )
            row = (await conn.execute(header_q, {"id": match_id})).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Match not found")

            match_info = {
                "id": row[0],
                "date": row[1].isoformat() if row[1] else None,
                "league": row[2],
                "home_id": row[3],
                "home_team": row[4],
                "away_id": row[5],
                "away_team": row[6],
                "round": row[7],
                "goals": {"home": row[8], "away": row[9]},
                "xg": {
                    "home": _sanitize(row[10]),
                    "away": _sanitize(row[11]),
                },
                "is_completed": row[12],
                "ai_verdict": row[13],
            }

            home_id = match_info["home_id"]
            away_id = match_info["away_id"]

        async_session_factory = sessionmaker(
            local_engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session_factory() as session:
            home_t = await get_team_name(session, home_id)
            away_t = await get_team_name(session, away_id)

            home_stats = await get_last_n_completed_avg(session, home_id, n=5)
            away_stats = await get_last_n_completed_avg(session, away_id, n=5)

            if home_stats.get("ppda") is None or home_stats.get("deep_completions") is None:
                home_season = await get_team_season_stats(session, home_id)
                home_stats["ppda"] = home_stats["ppda"] if home_stats["ppda"] is not None else home_season.get("ppda", 0.0)
                home_stats["deep_completions"] = home_stats["deep_completions"] if home_stats["deep_completions"] is not None else home_season.get("deep_completions", 0)
            if away_stats.get("ppda") is None or away_stats.get("deep_completions") is None:
                away_season = await get_team_season_stats(session, away_id)
                away_stats["ppda"] = away_stats["ppda"] if away_stats["ppda"] is not None else away_season.get("ppda", 0.0)
                away_stats["deep_completions"] = away_stats["deep_completions"] if away_stats["deep_completions"] is not None else away_season.get("deep_completions", 0)

        if not match_info["ai_verdict"]:
            background_tasks.add_task(_generate_verdict_bg, match_id)

        return {
            "match": match_info,
            "comparison": {
                "home": {
                    "team": home_t,
                    "avg_xG": home_stats.get("avg_xG", 0),
                    "avg_xG_conceded": home_stats.get("avg_xG_conceded", 0),
                    "avg_goals_scored": home_stats.get("avg_goals_scored", 0),
                    "avg_goals_conceded": home_stats.get("avg_goals_conceded", 0),
                    "ppda": home_stats.get("ppda", 0.0),
                    "deep_completions": home_stats.get("deep_completions", 0),
                },
                "away": {
                    "team": away_t,
                    "avg_xG": away_stats.get("avg_xG", 0),
                    "avg_xG_conceded": away_stats.get("avg_xG_conceded", 0),
                    "avg_goals_scored": away_stats.get("avg_goals_scored", 0),
                    "avg_goals_conceded": away_stats.get("avg_goals_conceded", 0),
                    "ppda": away_stats.get("ppda", 0.0),
                    "deep_completions": away_stats.get("deep_completions", 0),
                },
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to build preview for match %s", match_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# GET /api/matches/{match_id}/lineups (NUOVO ENDPOINT)
# ---------------------------------------------------------------------------

@router.get("/matches/{match_id}/lineups")
async def get_match_lineups(match_id: int):
    """
    Estrae le formazioni (titolari e panchina) con eventi per la partita specificata.
    """
    query = text("""
        SELECT 
            player, 
            position, 
            time, 
            goals, 
            yellow_card, 
            red_card, 
            team_type
        FROM rosters
        WHERE match_id = :match_id
        ORDER BY 
            CASE WHEN position IN ('Sub', 'SUB') THEN 1 ELSE 0 END,
            player ASC
    """)
    
    try:
        async with local_engine.connect() as conn:
            rows = await conn.execute(query, {"match_id": match_id})
            
            lineups = {
                "home": {"starters": [], "bench": []},
                "away": {"starters": [], "bench": []}
            }
            
            for r in rows:
                pos = str(r[1]).strip()
                is_sub = pos in ('Sub', 'SUB')
                minutes = r[2] or 0
                
                player_data = {
                    "name": r[0],
                    "position": pos,
                    "minutes": minutes,
                    "goals": r[3] or 0,
                    "yellow_cards": r[4] or 0,
                    "red_cards": r[5] or 0,
                    "subbed_in": True if (is_sub and minutes > 0) else False
                }
                
                # 'h' sta per Home, altrimenti Away
                t_type = "home" if str(r[6]).lower().startswith('h') else "away"
                
                if is_sub:
                    lineups[t_type]["bench"].append(player_data)
                else:
                    lineups[t_type]["starters"].append(player_data)
                    
            return lineups
            
    except Exception as exc:
        logger.exception(f"Failed to fetch lineups for match {match_id}")
        raise HTTPException(status_code=500, detail="Errore nel caricamento formazioni")