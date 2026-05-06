#!/usr/bin/env python3
"""
Count shots for match_id 30116.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def count():
    async with AsyncSessionLocal() as session:
        # Count shots for match_id 30116
        result = await session.execute(
            text("SELECT COUNT(*) FROM shots WHERE match_id = 30116")
        )
        count = result.scalar()
        print(f"Shots count for match_id 30116: {count}")
        # Also show match info
        result = await session.execute(
            text("SELECT home_team, away_team FROM matches WHERE id = 30116")
        )
        match = result.first()
        if match:
            print(f"Match: {match.home_team} vs {match.away_team}")
        else:
            print("Match not found.")

if __name__ == "__main__":
    asyncio.run(count())