"""
Daily scheduler for xPalermoStat Understat scraper.

Uses APScheduler with a cron trigger to run the scraper once a day at 02:00 AM.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from scrapers.understat_lib import scrape_latest_como_match

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


async def run_daily_update() -> None:
    """
    Job that runs daily at 02:00 AM.
    Scrapes the latest Como match (match 30116) and saves to database.
    """
    logger.info("Starting daily scraping job")
    try:
        success = await scrape_latest_como_match()
        if success:
            logger.info("Daily scraping job completed successfully")
        else:
            logger.error("Daily scraping job failed (see previous logs)")
    except Exception as e:
        logger.error(f"Daily scraping job raised an exception: {e}", exc_info=True)
        raise


@asynccontextmanager
async def lifespan_manager(app):
    """
    Lifespan context manager for FastAPI.
    Starts the scheduler on startup and stops it on shutdown.
    """
    # Start a one‑time immediate scrape in background (optional)
    asyncio.create_task(scrape_latest_como_match())

    # Schedule daily job at 02:00 UTC
    trigger = CronTrigger(hour=2, minute=0, timezone="UTC")
    scheduler.add_job(
        run_daily_update,
        trigger=trigger,
        id="daily_scrape",
        name="Daily scrape of latest Como match",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started with daily cron job at 02:00 UTC")

    yield

    scheduler.shutdown()
    logger.info("Scheduler stopped")


if __name__ == "__main__":
    # For testing: run the job once immediately
    import sys
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(scrape_latest_como_match())
    else:
        print("Scheduler module loaded. Use as part of FastAPI lifespan.")