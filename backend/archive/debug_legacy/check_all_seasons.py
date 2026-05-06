import asyncio
import sys
sys.path.append('.')
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/xpalermostat_db')
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT team_id, season, xG_for, xG_against, xpts, points FROM team_season_stat ORDER BY season"))
        rows = result.all()
        for row in rows:
            print(row)
    await engine.dispose()

asyncio.run(check())