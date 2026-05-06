#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from app.db.session import AsyncSessionLocal
from app.models.football import Team, League

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(Team.__table__.select().limit(10))
        teams = result.fetchall()
        print(f"Found {len(teams)} teams")
        for team in teams:
            print(f"ID: {team.id}, Name: {team.name}, League ID: {team.league_id}")

if __name__ == "__main__":
    asyncio.run(main())