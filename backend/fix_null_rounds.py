#!/usr/bin/env python3
"""
Fix NULL round values in MatchCalendar by computing round number based on chronological order.
Assumes each league season has exactly 380 matches (20 teams, 38 rounds) and matches are sorted by datetime.
"""
import asyncio
import logging
import sys
sys.path.insert(0, '.')

from app.db.database import AsyncSessionLocal
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_null_rounds():
    async with AsyncSessionLocal() as session:
        # First, count null rounds
        result = await session.execute(
            text("SELECT COUNT(*) FROM matchcalendar WHERE round IS NULL")
        )
        null_count = result.scalar()
        logger.info(f"Found {null_count} matches with NULL round.")
        if null_count == 0:
            logger.info("Nothing to fix.")
            return
        
        # We'll update using a window function to assign round numbers per league.
        # For each league, order by match_datetime, assign row number, compute round = floor(rn / 10) + 1
        # Assuming 10 matches per round (20 teams).
        # We'll only update rows where round IS NULL.
        update_sql = """
        WITH numbered AS (
            SELECT id,
                   league_id,
                   match_datetime,
                   ROW_NUMBER() OVER (PARTITION BY league_id ORDER BY match_datetime) - 1 AS rn
            FROM matchcalendar
            WHERE round IS NULL
        )
        UPDATE matchcalendar mc
        SET round = FLOOR(numbered.rn / 10) + 1
        FROM numbered
        WHERE mc.id = numbered.id
        """
        await session.execute(text(update_sql))
        await session.commit()
        logger.info(f"Updated {null_count} matches with computed round numbers.")
        
        # Verify
        result = await session.execute(
            text("SELECT COUNT(*) FROM matchcalendar WHERE round IS NULL")
        )
        remaining = result.scalar()
        logger.info(f"Remaining NULL rounds: {remaining}")

async def main():
    try:
        await fix_null_rounds()
    except Exception as e:
        logger.exception("Failed to fix NULL rounds")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())