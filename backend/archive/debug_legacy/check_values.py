import asyncio
import sys
sys.path.insert(0, 'backend')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.db.database import DATABASE_URL
from app.models.football import TeamSeasonStat

async def check():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        stmt = select(TeamSeasonStat).where(TeamSeasonStat.season == "2025/26")
        result = await db.execute(stmt)
        rows = result.scalars().all()
        for stat in rows:
            print(f"{stat.team_id}: xG_for={stat.xG_for}, xG_against={stat.xG_against}, ppda={stat.ppda}")

if __name__ == "__main__":
    asyncio.run(check())