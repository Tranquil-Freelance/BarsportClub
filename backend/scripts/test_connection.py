#!/usr/bin/env python3
"""
Test database connection with 127.0.0.1.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def test():
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            print("Connection successful:", result.scalar())
            # Count matches
            result = await session.execute(text("SELECT COUNT(*) FROM matches"))
            match_count = result.scalar()
            print(f"Matches in DB: {match_count}")
            # Count shots
            result = await session.execute(text("SELECT COUNT(*) FROM shots"))
            shots_count = result.scalar()
            print(f"Shots in DB: {shots_count}")
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test())