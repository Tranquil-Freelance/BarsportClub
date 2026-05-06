import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test():
    engine = create_async_engine('postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat')
    try:
        async with engine.connect() as conn:
            print('Connected')
            result = await conn.execute(text('SELECT COUNT(*) FROM master_europe_players'))
            row = result.fetchone()
            print('Count:', row[0] if row else 'none')
            result2 = await conn.execute(text('SELECT player_name, team_name FROM master_europe_players LIMIT 5'))
            for r in result2.fetchall():
                print(r)
    except Exception as e:
        print('Error:', e)
    finally:
        await engine.dispose()

if __name__ == '__main__':
    asyncio.run(test())