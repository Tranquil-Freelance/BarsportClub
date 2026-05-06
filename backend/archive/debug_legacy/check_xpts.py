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
        stmt = select(TeamSeasonStat).where(TeamSeasonStat.team_id == 106)  # Inter
        result = await db.execute(stmt)
        stat = result.scalar_one()
        print(f'Team: {stat.team_id}, xG_for: {stat.xG_for}, xG_against: {stat.xG_against}, xpts: {stat.xpts}')
        # also check if xpts is not zero
        if stat.xpts == 0.0:
            print('WARNING: xpts is zero!')
        else:
            print(f'xpts value: {stat.xpts}')
    await engine.dispose()

asyncio.run(check())