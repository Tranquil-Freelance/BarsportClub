"""
FastAPI router for scraping Understat match and team data.
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.services.understat_service import scrape_and_save_match, UnderstatService

router = APIRouter(prefix="/api/scraper", tags=["scraper"])
logger = logging.getLogger(__name__)


async def _scrape_match_background(match_id: int, force: bool = False) -> None:
    """
    Background task that scrapes a single match and upserts its data.
    """
    async with AsyncSessionLocal() as session:
        try:
            await scrape_and_save_match(session, match_id, force=force)
            logger.info(f"Successfully scraped match {match_id} (force={force})")
        except Exception as e:
            logger.error(f"Failed to scrape match {match_id} (force={force}): {e}")
            # Re-raise to let FastAPI log the error (background tasks capture exceptions)
            raise


@router.post("/match/{match_id}", status_code=202)
async def scrape_match(match_id: int, background_tasks: BackgroundTasks, force: bool = False) -> Dict[str, Any]:
    """
    Trigger scraping of a single Understat match by its ID.
    The scraping runs in background to avoid blocking the request.
    """
    try:
        background_tasks.add_task(_scrape_match_background, match_id, force)
        return {
            "message": f"Scraping triggered for match {match_id} (force={force})",
            "match_id": match_id,
            "status": "accepted"
        }
    except Exception as e:
        logger.error(f"Failed to schedule scraping for match {match_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/team/como", status_code=202)
async def scrape_team_como(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Scrape the Como team page to discover match IDs for the current season,
    then trigger scraping for each match.
    """
    try:
        # Get match IDs where Como participates (Serie A 2024/25 season)
        match_ids = await UnderstatService.get_como_match_ids(season_year=2025)
        if not match_ids:
            logger.warning("No Como matches found for the specified season")
            return {
                "message": "No Como matches found for the current season.",
                "match_ids": [],
                "status": "completed"
            }

        # Schedule background scraping for each match
        for match_id in match_ids:
            background_tasks.add_task(_scrape_match_background, match_id)

        logger.info(f"Scheduled scraping for {len(match_ids)} Como matches")
        return {
            "message": f"Scraping triggered for {len(match_ids)} Como matches",
            "match_ids": match_ids,
            "status": "accepted"
        }
    except Exception as e:
        logger.error(f"Failed to scrape Como team page: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger", status_code=200)
async def trigger_scrape() -> Dict[str, Any]:
    """
    Manually trigger scraping of the latest Como match.
    Executes synchronously (awaits completion) and returns a success message.
    """
    try:
        # Hardcode match 30116 (Cagliari vs Como) as the latest Como match for now
        match_id = 30116
        
        async with AsyncSessionLocal() as session:
            result = await scrape_and_save_match(session, match_id)
        
        return {
            "status": "success",
            "message": "Scraping triggered manually.",
            "match_id": match_id,
            "home_team": result["home_team"],
            "away_team": result["away_team"],
            "total_shots": result["total_shots"]
        }
    except Exception as e:
        logger.error(f"Manual trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def scraper_health() -> Dict[str, str]:
    """
    Health endpoint for the scraper routes.
    """
    return {"status": "healthy", "service": "understat-scraper"}