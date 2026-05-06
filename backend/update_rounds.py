#!/usr/bin/env python3
"""
Update round numbers for existing matches by triggering a calendar sync.
This will re-fetch data from Understat and upsert with computed rounds.
"""
import asyncio
import logging
import sys

sys.path.insert(0, '.')

from app.db.session import AsyncSessionLocal
from app.scraper.sync_calendar import sync_league_calendar

logging.basicConfig(level=logging.INFO)

async def main():
    async with AsyncSessionLocal() as session:
        try:
            logging.info("Starting calendar sync for Serie_A 2025...")
            await sync_league_calendar(session, "Serie_A", 2025, league_id=1)
            logging.info("Sync completed successfully.")
        except Exception as e:
            logging.error(f"Sync failed: {e}", exc_info=True)
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())