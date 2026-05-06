import asyncio
import sys
sys.path.append('.')
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.football import TeamSeasonStat

async def check():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/xpalermostat_db')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        stmt = select(TeamSeasonStat)
        result = await db.execute(stmt)
        stats = result.scalars().all()
        for stat in stats:
            print(f'Team {stat.team_id} Season {stat.season!r}: xG_for {stat.xG_for}, xG_against {stat.xG_against}, xpts {stat.xpts}, points {stat.points}')
    await engine.dispose()

asyncio.run(check())