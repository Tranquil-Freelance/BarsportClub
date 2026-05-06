#!/usr/bin/env python3
"""
Loop the scraper orchestrator until all pending matches are processed.
"""
import asyncio
import sys
import logging

sys.path.insert(0, 'backend')

from app.scraper.scraper_orchestrator import run_once
from app.db.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def count_pending_matches():
    """Return number of matches with scraping_status = 'PENDING' and status = 'finito'."""
    from sqlalchemy import select, func
    from app.db.models import Match
    async with AsyncSessionLocal() as session:
        stmt = select(func.count(Match.id)).where(
            Match.status == 'finito',
            Match.scraping_status == 'PENDING',
            Match.understat_id.isnot(None)
        )
        result = await session.execute(stmt)
        return result.scalar()

async def main():
    max_cycles = 50  # safety limit
    for cycle in range(1, max_cycles + 1):
        pending = await count_pending_matches()
        if pending == 0:
            logger.info(f"No pending matches remaining. Exiting.")
            break
        logger.info(f"Cycle {cycle}: {pending} pending matches.")
        try:
            await run_once()
        except Exception as e:
            logger.error(f"Error in cycle {cycle}: {e}")
        # Wait a bit before next cycle
        await asyncio.sleep(5)
    else:
        logger.warning(f"Reached max cycles ({max_cycles}). Stopping.")
    
    # Final report
    pending = await count_pending_matches()
    logger.info(f"Final pending matches: {pending}")

if __name__ == "__main__":
    asyncio.run(main())