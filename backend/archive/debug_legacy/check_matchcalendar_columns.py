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
        result = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='matchcalendar' ORDER BY ordinal_position"))
        cols = [row[0] for row in result]
        print('MatchCalendar columns:', cols)
        # also check if round column exists
        if 'round' in cols:
            print('Round column exists')
        else:
            print('Round column missing')
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(check())