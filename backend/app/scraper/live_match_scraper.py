"""
Live match scraping orchestrator for xPalermoStat.

This module provides a periodic job that, after each match is completed, scrapes
player‑level statistics from Understat, cleans them, and upserts them into the
PostgreSQL database. It also marks the match as scraped to avoid duplicate work.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.football import MatchCalendar
from app.scraper.understat_parser import get_match_roster
from app.scraper.data_cleaner import UnderstatCleaner
from app.services.db_ingestion import upsert_players, upsert_player_match_stats

logger = logging.getLogger(__name__)


async def scrape_completed_matches(session: AsyncSession) -> None:
    """
    Find matches that have finished but not yet been scraped, fetch player stats,
    and upsert them into the Player and PlayerMatchStat tables.

    A match is considered ready for scraping when:
      - is_completed == True
      - is_scraped == False
      - match_datetime is at least 15 minutes older than the current UTC time
        (to allow Understat to update its data after the final whistle).

    The function processes matches one by one, inserting a small delay between
    requests to avoid hitting Understat's rate limits.

    Args:
        session: SQLAlchemy async session.

    Returns:
        None
    """
    # Calculate the cutoff time: matches that finished at least 15 minutes ago
    cutoff = datetime.utcnow() - timedelta(minutes=15)

    stmt = (
        select(MatchCalendar)
        .where(MatchCalendar.is_completed == True)
        .where(MatchCalendar.is_scraped == False)
        .where(MatchCalendar.match_datetime < cutoff)
        .order_by(MatchCalendar.match_datetime)
    )
    result = await session.execute(stmt)
    matches: List[MatchCalendar] = result.scalars().all()

    if not matches:
        logger.info("No completed matches ready for scraping.")
        return

    logger.info(f"Found {len(matches)} completed match(es) ready for scraping.")

    for match in matches:
        logger.info(
            f"Scraping match {match.id} ({match.home_team_id} vs {match.away_team_id}) "
            f"played at {match.match_datetime.isoformat()}"
        )

        try:
            # 1. Fetch raw roster data from Understat
            raw_roster = await asyncio.to_thread(get_match_roster, match.id)
            logger.debug(f"Retrieved roster data for match {match.id}")

            # 2. Clean the raw data into a structured DataFrame
            df = UnderstatCleaner.clean_match_roster(raw_roster, match.id)
            logger.debug(f"Cleaned DataFrame shape: {df.shape}")

            # 3. Upsert players (unique across the whole dataset)
            await upsert_players(session, df)

            # 4. Upsert player‑match statistics
            await upsert_player_match_stats(session, df)

            # 5. Mark the match as scraped and commit the session
            match.is_scraped = True
            await session.commit()

            logger.info(f"Successfully scraped and stored stats for match {match.id}")

        except Exception as e:
            logger.exception(
                f"Failed to scrape match {match.id}: {e}. "
                "The match will be retried in the next run."
            )
            # Rollback any partial changes for this match
            await session.rollback()
            # Continue with the next match

        # Polite delay to avoid rate limiting (3 seconds as suggested by Understat)
        await asyncio.sleep(3)

    logger.info("Live match scraping round completed.")


async def main() -> None:
    """
    Entrypoint for the live scraping orchestrator.
    """
    logger.info("Starting live match scraping orchestrator.")

    async with AsyncSessionLocal() as session:
        await scrape_completed_matches(session)

    logger.info("Live match scraping orchestrator finished.")


if __name__ == "__main__":
    # Configure logging to see informative messages
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    asyncio.run(main())