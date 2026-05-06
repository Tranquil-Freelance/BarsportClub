"""
Calendar synchronization orchestrator for xPalermoStat.

This module provides the daily cronjob that fetches match calendars from Understat
for Serie A and Premier League, cleans the data, and upserts it into the PostgreSQL
database. It ensures the database always knows which matches are scheduled and which
are already completed.
"""

import asyncio
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.scraper.understat_parser import get_league_season_data
from app.scraper.data_cleaner import UnderstatCleaner
from app.services.db_ingestion import upsert_teams, upsert_match_calendar, upsert_league, UNDERSTAT_SLUG_TO_NAME

logger = logging.getLogger(__name__)


async def sync_league_calendar(
    session: AsyncSession,
    league_slug: str,
    season_year: int,
    league_id: int,
) -> None:
    """
    Fetch, clean, and upsert a single league's match calendar.

    Args:
        session: SQLAlchemy async session.
        league_slug: Understat league identifier (e.g., 'Serie_A', 'EPL').
        season_year: Calendar year the season ends (e.g., 2024 for 2023/24).
        league_id: Internal league ID used in the database (1 for Serie A, 2 for EPL).

    Raises:
        Exception: Any error that occurs during fetching, cleaning, or upserting
            is caught, logged, and re‑raised.
    """
    logger.info(
        "Starting calendar sync for league '%s' (season %d, db league_id %d)",
        league_slug,
        season_year,
        league_id,
    )

    try:
        # 1. Fetch raw JSON from Understat
        logger.debug("Fetching raw data from Understat...")
        raw_data = await get_league_season_data(league_slug, season_year)
        logger.debug("Received %d match entries", len(raw_data))

        # 2. Clean the raw data into a structured DataFrame
        logger.debug("Cleaning raw data with UnderstatCleaner...")
        df = UnderstatCleaner.clean_match_calendar(raw_data)
        logger.debug("Cleaned DataFrame shape: %s", str(df.shape))

        # 2.5 Ensure the league exists in the database
        league_name = UNDERSTAT_SLUG_TO_NAME.get(league_slug)
        if league_name is None:
            # Fallback: convert slug to readable name (e.g., Serie_A -> Serie A)
            league_name = league_slug.replace('_', ' ')
        logger.debug("Upserting league record (id=%d, name=%s)...", league_id, league_name)
        await upsert_league(session, league_id, league_name, league_slug)

        # 3. Upsert teams (home and away) into the Team table
        logger.debug("Upserting teams...")
        await upsert_teams(session, df, league_id)

        # 4. Upsert matches into the MatchCalendar table
        logger.debug("Upserting matches...")
        await upsert_match_calendar(session, df, league_id)

        logger.info(
            "Successfully synced calendar for league '%s' (season %d)",
            league_slug,
            season_year,
        )

    except Exception as e:
        logger.exception(
            "Failed to sync calendar for league '%s' (season %d): %s",
            league_slug,
            season_year,
            e,
        )
        try:
            await session.rollback()
        except Exception:
            # rollback may fail if there is no active transaction
            pass
        raise


async def run_daily_sync(season_year: int = 2025) -> None:
    """
    Main entrypoint for the daily calendar synchronization.

    Creates a database session and calls `sync_league_calendar` for each
    target league (Serie A and Premier League).

    Args:
        season_year: Calendar year the season ends. Defaults to the current
            season (2024).
    """
    logger.info("Starting daily calendar sync for season %d", season_year)

    async with AsyncSessionLocal() as session:
        # Serie A
        await sync_league_calendar(session, "Serie_A", season_year, league_id=1)

        # Premier League (EPL)
        await sync_league_calendar(session, "EPL", season_year, league_id=2)

    logger.info("Daily calendar sync completed successfully")


if __name__ == "__main__":
    # Configure basic logging for standalone script execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        asyncio.run(run_daily_sync())
    except KeyboardInterrupt:
        logger.warning("Calendar sync interrupted by user")
    except Exception as e:
        logger.critical("Unhandled error in calendar sync: %s", e, exc_info=True)
        raise