#!/usr/bin/env python3
"""
Batch scrape shot data for all real matches (understat_id > 20000, status 'finito').
Uses the UnderstatService with force=True to bypass missing data.
"""
import asyncio
import sys
import time
from typing import List

sys.path.insert(0, 'backend')

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.db.models import Match
from app.services.understat_service import scrape_and_save_match

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/xpalermostat_db"
engine = create_async_engine(DATABASE_URL, echo=False)

async def get_real_matches(session: AsyncSession) -> List[Match]:
    """Retrieve matches that need shot data."""
    stmt = (
        select(Match)
        .where(Match.understat_id > 20000)
        .where(Match.status == 'finito')
        .order_by(Match.understat_id)
    )
    result = await session.execute(stmt)
    matches = result.scalars().all()
    return matches

async def process_match(session: AsyncSession, match: Match) -> bool:
    """Scrape and save shot data for a single match."""
    understat_id = match.understat_id
    print(f"Processing match ID {match.id} (Understat ID {understat_id})...")
    try:
        await scrape_and_save_match(session, understat_id, force=True)
        # Update scraping_status to SUCCESS (optional)
        match.scraping_status = 'SUCCESS'
        match.error_log = None
        await session.commit()
        print(f"  Successfully scraped match {understat_id}")
        return True
    except Exception as e:
        print(f"  Failed to scrape match {understat_id}: {e}")
        match.scraping_status = 'ERROR'
        match.error_log = str(e)
        await session.commit()
        return False

async def main():
    print("Starting batch shot scraping...")
    async with AsyncSession(engine) as session:
        matches = await get_real_matches(session)
        total = len(matches)
        print(f"Found {total} matches to process.")
        
        success = 0
        failed = 0
        for idx, match in enumerate(matches, start=1):
            print(f"[{idx}/{total}] ", end="")
            result = await process_match(session, match)
            if result:
                success += 1
            else:
                failed += 1
            
            # Small delay to avoid rate limiting (1 second)
            if idx < total:
                await asyncio.sleep(1)
        
        print(f"\nBatch completed. Success: {success}, Failed: {failed}")
        
        # Final status summary
        await session.commit()
        result = await session.execute(
            select(Match.scraping_status, Match.understat_id)
            .where(Match.understat_id > 20000)
            .where(Match.status == 'finito')
        )
        rows = result.fetchall()
        status_count = {}
        for row in rows:
            status_count[row.scraping_status] = status_count.get(row.scraping_status, 0) + 1
        print("Final scraping_status distribution:")
        for status, count in status_count.items():
            print(f"  {status}: {count}")

if __name__ == "__main__":
    asyncio.run(main())