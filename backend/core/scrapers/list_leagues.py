import asyncio
from app.db.session import AsyncSessionLocal
from app.models.football import League
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(League))
        for league in result.scalars():
            print(f"{league.id}: {league.name} -> {league.understat_slug}")

if __name__ == "__main__":
    asyncio.run(main())