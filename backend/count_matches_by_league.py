import asyncio
from app.db.session import AsyncSessionLocal
from app.models.football import MatchCalendar
from sqlalchemy import select, func

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(MatchCalendar.league_id, func.count(MatchCalendar.id)).group_by(MatchCalendar.league_id)
        )
        for league_id, count in result:
            print(f"league_id {league_id}: {count} matches")

if __name__ == "__main__":
    asyncio.run(main())