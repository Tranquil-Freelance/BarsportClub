#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import AsyncSessionLocal
from app.db.models import Match, Shot

async def main():
    async with AsyncSessionLocal() as session:
        match = await session.get(Match, 27362)
        if match:
            print(f"Match found: {match.home_team} vs {match.away_team}")
            shots = await session.execute(Shot.__table__.select().where(Shot.match_id == 27362))
            shots = shots.fetchall()
            print(f"Shots count: {len(shots)}")
            for shot in shots:
                print(shot)
        else:
            print("Match not found")

if __name__ == "__main__":
    asyncio.run(main())