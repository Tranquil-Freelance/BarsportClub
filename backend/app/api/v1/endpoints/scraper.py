"""
Administrative API endpoints for manually triggering data extraction scripts.
"""

from typing import Dict, Any
from fastapi import APIRouter, BackgroundTasks, status

from app.db.session import AsyncSessionLocal
from app.scraper.sync_calendar import sync_league_calendar
from app.scraper.live_match_scraper import scrape_completed_matches

router = APIRouter()


async def run_sync_calendar_task(
    league_slug: str,
    season_year: int,
    league_id: int,
) -> None:
    """
    Background task wrapper for sync_league_calendar.
    Creates its own database session because FastAPI's get_db closes the session
    after the HTTP response.
    """
    async with AsyncSessionLocal() as session:
        await sync_league_calendar(session, league_slug, season_year, league_id)


async def run_scrape_live_matches_task() -> None:
    """
    Background task wrapper for scrape_completed_matches.
    Creates its own database session because FastAPI's get_db closes the session
    after the HTTP response.
    """
    async with AsyncSessionLocal() as session:
        await scrape_completed_matches(session)


@router.post(
    "/trigger-sync",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["admin_scraper"],
    summary="Manually trigger calendar synchronization",
)
async def trigger_sync(
    league_slug: str,
    season_year: int,
    league_id: int,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Start calendar synchronization in the background.

    - **league_slug**: Understat league identifier (e.g., 'Serie_A', 'EPL').
    - **season_year**: Calendar year the season ends (e.g., 2024 for 2023/24).
    - **league_id**: Internal league ID used in the database (1 for Serie A, 2 for EPL).
    """
    background_tasks.add_task(
        run_sync_calendar_task,
        league_slug,
        season_year,
        league_id,
    )
    return {
        "message": "Calendar synchronization started in background.",
        "league": league_slug,
        "season": season_year,
    }


@router.post(
    "/trigger-scrape",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["admin_scraper"],
    summary="Manually trigger live match scraping",
)
async def trigger_scrape(
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Start live match scraping in the background.
    """
    background_tasks.add_task(run_scrape_live_matches_task)
    return {
        "message": "Live match scraping started in background.",
    }