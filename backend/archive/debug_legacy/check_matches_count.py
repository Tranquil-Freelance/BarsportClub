#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.session import AsyncSessionLocal
from app.db.models import Match

async def count_matches():
    async with AsyncSessionLocal() as session:
        result = await session.execute("SELECT COUNT(*) FROM matches")
        count = result.scalar()
        print(f"Matches in database: {count}")
        # also count shots
        result = await session.execute("SELECT COUNT(*) FROM shots")
        shots = result.scalar()
        print(f"Shots in database: {shots}")

if __name__ == "__main__":
    asyncio.run(count_matches())