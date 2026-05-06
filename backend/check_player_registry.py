import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat')
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'player_registry'"))
        cols = result.fetchall()
        print('Columns:', [c[0] for c in cols])
        # also sample a row
        result2 = await conn.execute(text("SELECT * FROM player_registry LIMIT 1"))
        row = result2.fetchone()
        if row:
            print('Sample:', dict(zip([c[0] for c in cols], row)))
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(main())