#!/usr/bin/env python3
"""
Batch scrape shot data using the UnderstatService with force=True.
Creates a new database session for each match to avoid session issues.
"""
import asyncio
import sys
import time

sys.path.insert(0, 'backend')

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.db.database import AsyncSessionLocal
from app.db.models import Match
from app.services.understat_service import scrape_and_save_match

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/xpalermostat_db"
engine = create_async_engine(DATABASE_URL, echo=False)

async def get_real_match_ids(session: AsyncSession, limit=None):
    """Return list of (match_id, understat_id) for matches needing shots."""
    stmt = (
        select(Match.id, Match.understat_id)
        .where(Match.understat_id > 20000)
        .where(Match.status == 'finito')
        .where(Match.scraping_status == 'PENDING')
        .order_by(Match.understat_id)
    )
    if limit:
        stmt = stmt.limit(limit)
    result = await session.execute(stmt)
    return result.fetchall()

async def process_match(match_id: int, understat_id: int) -> bool:
    """Scrape and save a single match using a fresh session."""
    async with AsyncSessionLocal() as session:
        try:
            await scrape_and_save_match(session, understat_id, force=True)
            # Update scraping_status to SUCCESS
            match = await session.get(Match, match_id)
            if match:
                match.scraping_status = 'SUCCESS'
                match.error_log = None
                await session.commit()
            print(f"  SUCCESS: match {match_id} (Understat {understat_id})")
            return True
        except Exception as e:
            print(f"  ERROR: match {match_id} (Understat {understat_id}) - {e}")
            # Update scraping_status to ERROR
            match = await session.get(Match, match_id)
            if match:
                match.scraping_status = 'ERROR'
                match.error_log = str(e)[:500]
                await session.commit()
            return False

async def main(limit=None):
    print("Starting batch scrape with force=True...")
    async with AsyncSession(engine) as session:
        rows = await get_real_match_ids(session, limit=limit)
        total = len(rows)
        if total == 0:
            print("No pending matches found.")
            return
        print(f"Found {total} matches to process.")
        
        success = 0
        failed = 0
        for idx, (match_id, understat_id) in enumerate(rows, start=1):
            print(f"[{idx}/{total}] Processing match {match_id} (Understat {understat_id})...")
            if await process_match(match_id, understat_id):
                success += 1
            else:
                failed += 1
            
            # Delay to avoid rate limiting (0.5 seconds)
            if idx < total:
                await asyncio.sleep(0.5)
        
        print(f"\nBatch completed. Success: {success}, Failed: {failed}")
        
        # Final status distribution
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
    # Process all pending matches
    asyncio.run(main())