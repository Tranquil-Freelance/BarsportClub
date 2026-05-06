import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat')
    async with engine.connect() as conn:
        result = await conn.execute(text('SELECT * FROM master_europe_players LIMIT 1'))
        cols = result.keys()
        print('Columns:', list(cols))
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(main())