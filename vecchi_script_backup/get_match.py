#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('backend')
from app.db.session import AsyncSessionLocal
from app.models.football import Match

async def main():
    async with AsyncSessionLocal() as session:
        match = await session.get(Match, 29)
        if match:
            print(f"Match ID: {match.id}")
            print(f"Home: {match.home_team} vs Away: {match.away_team}")
            print(f"Understat ID: {match.understat_id}")
            print(f"Date: {match.start_time}")
        else:
            print("Match not found")
        await session.close()

if __name__ == "__main__":
    asyncio.run(main())