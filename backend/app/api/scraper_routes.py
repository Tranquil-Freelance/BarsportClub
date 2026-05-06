"""
Scraper Controller – FastAPI router for triggering scraping jobs.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.football import MatchCalendar
from app.scraper.understat import UnderstatScraper
from app.scraper.sniper_protocol import run_sniper_protocol

router = APIRouter()
logger = logging.getLogger(__name__)


# In‑memory status tracking (for demo purposes; in production use Redis or DB)
_scraper_status = {
    "status": "idle",  # 'idle', 'running', 'error'
    "last_run": None,
    "last_error": None,
}


async def _update_status(status: str, error: str = None):
    """Update the global scraper status."""
    _scraper_status["status"] = status
    _scraper_status["last_run"] = datetime.utcnow().isoformat() + "Z"
    if error:
        _scraper_status["last_error"] = error
    else:
        _scraper_status["last_error"] = None


async def _run_scraper_for_match(match_id: int) -> None:
    """
    Background task that scrapes a single match and upserts its data.
    """
    async with AsyncSessionLocal() as session:
        try:
            scraper = UnderstatScraper()
            await scraper.scrape_and_save_match(session, match_id)
            # Mark match as scraped (optional)
            match = await session.get(MatchCalendar, match_id)
            if match:
                match.is_scraped = True
                await session.commit()
            logger.info(f"Successfully scraped match {match_id}")
        except Exception as e:
            logger.error(f"Failed to scrape match {match_id}: {e}")
            await _update_status("error", str(e))
            raise


async def _run_scraper_for_last_matches(limit: int = 5) -> None:
    """
    Scrape the last `limit` completed matches that have not been scraped yet.
    """
    async with AsyncSessionLocal() as session:
        # Find completed matches not yet scraped, ordered by date descending
        stmt = (
            select(MatchCalendar)
            .where(MatchCalendar.is_completed == True)
            .where(MatchCalendar.is_scraped == False)
            .order_by(MatchCalendar.match_datetime.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        matches = result.scalars().all()

        if not matches:
            logger.info("No unscraped completed matches found.")
            return

        logger.info(f"Found {len(matches)} matches to scrape.")
        for match in matches:
            await _run_scraper_for_match(match.id)


async def _run_scraper_for_latest_round(league_name: str, season: str) -> None:
    """
    Scrape all matches in the latest round for a given league and season.
    """
    # Mapping from UI league names to league IDs (hardcoded for now)
    league_map = {
        "Serie A": 1,
        "Premier League": 2,
        "La Liga": 3,
        "Bundesliga": 4,
        "Ligue 1": 5,
    }
    # Understat slugs mapping (optional)
    slug_map = {
        "Serie A": "Serie_A",
        "Premier League": "EPL",
        "La Liga": "La_Liga",
        "Bundesliga": "Bundesliga",
        "Ligue 1": "Ligue_1",
    }
    
    league_id = league_map.get(league_name)
    if league_id is None:
        raise ValueError(f"Unsupported league: {league_name}")
    
    try:
        season_year = int(season)
    except ValueError:
        raise ValueError(f"Invalid season: {season}")

    async with AsyncSessionLocal() as session:
        # Determine the latest round for this league/season
        # We'll filter matches where league_id matches and match_datetime year is season_year (or season_year-1)
        # Since a season spans two calendar years, we'll approximate by checking year >= season_year-1 and year <= season_year
        stmt = (
            select(MatchCalendar.id, MatchCalendar.round)
            .where(MatchCalendar.league_id == league_id)
            .where(extract('year', MatchCalendar.match_datetime).between(season_year - 1, season_year))
            .where(MatchCalendar.round.isnot(None))
            .order_by(MatchCalendar.round.desc())
        )
        result = await session.execute(stmt)
        rows = result.all()
        if not rows:
            logger.warning(f"No matches found for league {league_name} season {season}")
            return
        
        # Latest round is the maximum round among filtered matches
        latest_round = max(row.round for row in rows)
        logger.info(f"Latest round for {league_name} {season}: {latest_round}")
        
        # Get match IDs for that round
        match_ids = [row.id for row in rows if row.round == latest_round]
        logger.info(f"Found {len(match_ids)} matches in round {latest_round}")
        
        if not match_ids:
            logger.warning(f"No matches in round {latest_round}")
            return
        
        # Scrape each match
        for match_id in match_ids:
            await _run_scraper_for_match(match_id)
        
        logger.info(f"Scraping completed for round {latest_round}")
@router.post(
    "/api/v1/scraper/sync",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["scraper"],
    summary="Trigger calendar synchronization",
)
async def trigger_sync(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Start calendar synchronization for a given league and season.

    Request body must contain:
        - league: string, e.g., "Serie A"
        - season: string, e.g., "2024"

    This endpoint currently only logs the request; a full implementation would
    call the existing `sync_league_calendar` function.
    """
    league = payload.get("league")
    season = payload.get("season")

    if not league or not season:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both 'league' and 'season' are required.",
        )

    # Mock implementation – just log the request
    logger.info(f"Sync requested for league={league}, season={season}")
    background_tasks.add_task(
        lambda: logger.info(f"Background sync started for {league} {season}")
    )

    return {
        "message": "Calendar synchronization started in background.",
        "league": league,
        "season": season,
    }


@router.post(
    "/api/v1/scraper/scrape",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["scraper"],
    summary="Trigger live scraping of the last 5 matches",
)
async def trigger_scrape(
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Start scraping player statistics for the last 5 completed matches.

    The endpoint returns immediately and schedules the scraping as a background
    task. Each match is processed sequentially with a built‑in delay to avoid
    rate limiting.
    """
    await _update_status("running")
    background_tasks.add_task(_run_scraper_for_last_matches)
    return {
        "message": "Live match scraping started in background.",
        "matches_to_scrape": 5,
    }


@router.post(
    "/api/v1/scraper/scrape-latest-round",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["scraper"],
    summary="Scrape all matches in the latest round for a given league and season",
)
async def trigger_scrape_latest_round(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Start scraping player statistics for the latest round of matches.
    
    Request body must contain:
        - league: string, e.g., "Serie A"
        - season: string, e.g., "2025"
    
    NOTE: This endpoint now runs the Sniper Protocol (scrapes finished matches
    from all five major leagues) regardless of the provided league/season.
    The parameters are kept for backward compatibility.
    """
    league = payload.get("league")
    season = payload.get("season")

    if not league or not season:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both 'league' and 'season' are required.",
        )

    await _update_status("running")
    background_tasks.add_task(run_sniper_protocol)
    return {
        "message": f"Sniper Protocol started for all five leagues (ignoring {league} {season}).",
        "league": league,
        "season": season,
    }


@router.get(
    "/api/v1/scraper/status",
    tags=["scraper"],
    summary="Get the current status of the scraper",
)
async def get_scraper_status() -> Dict[str, Any]:
    """
    Return the current scraper status and the timestamp of the last run.
    """
    return {
        "status": _scraper_status["status"],
        "last_run": _scraper_status["last_run"],
        "last_error": _scraper_status["last_error"],
    }


# Integration note:
# To connect this router to the main FastAPI app, add the following line in
# `backend/app/main.py` after the existing router inclusion:
#
#     from app.api.scraper_routes import router as scraper_router
#     app.include_router(scraper_router)
#
# This will make the endpoints available under `/api/v1/scraper/...`.