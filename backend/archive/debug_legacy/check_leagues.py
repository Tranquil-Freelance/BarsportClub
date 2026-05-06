#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from app.db.session import AsyncSessionLocal
from app.models.football import League

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(League.__table__.select())
        leagues = result.fetchall()
        for league in leagues:
            print(f"ID: {league.id}, Name: {league.name}, Slug: {league.understat_slug}")

if __name__ == "__main__":
    asyncio.run(main())