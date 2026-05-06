import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine('postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat')
    async with engine.connect() as conn:
        # get columns
        res = await conn.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'master_europe_players'
            ORDER BY ordinal_position
        """))
        for row in res.fetchall():
            print(row[0], row[1])

if __name__ == '__main__':
    asyncio.run(check())