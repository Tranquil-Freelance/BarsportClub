#!/usr/bin/env python3
"""
Test batch scrape shot data for first 2 real matches.
"""
import asyncio
import sys

sys.path.insert(0, 'backend')

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.db.models import Match
from app.services.understat_service import scrape_and_save_match

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/xpalermostat_db"
engine = create_async_engine(DATABASE_URL, echo=False)

async def get_real_matches(session: AsyncSession, limit: int = 2):
    stmt = (
        select(Match)
        .where(Match.understat_id > 20000)
        .where(Match.status == 'finito')
        .order_by(Match.understat_id)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()

async def main():
    async with AsyncSession(engine) as session:
        matches = await get_real_matches(session, limit=2)
        print(f"Testing with {len(matches)} matches.")
        for match in matches:
            print(f"Processing match ID {match.id} (Understat ID {match.understat_id})...")
            try:
                await scrape_and_save_match(session, match.understat_id, force=True)
                print(f"  Success")
            except Exception as e:
                print(f"  Error: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())