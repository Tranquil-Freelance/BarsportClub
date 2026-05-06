import asyncio
import sys
sys.path.append('.')
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import inspect, text

async def check():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/xpalermostat_db')
    async with engine.connect() as conn:
        # Use raw SQL
        result = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='team_season_stat' ORDER BY ordinal_position"))
        cols = [row[0] for row in result]
        print('Columns:', cols)
        if 'xpts' in cols:
            print('xpts column exists')
            # fetch one value
            result2 = await conn.execute(text("SELECT xpts FROM team_season_stat LIMIT 1"))
            row = result2.first()
            print('Sample xpts:', row[0] if row else None)
        else:
            print('xpts column missing')
    await engine.dispose()

asyncio.run(check())