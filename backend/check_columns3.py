import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect('postgresql://postgres:password@localhost:5432/xpalermostat')
    try:
        # Get column names
        rows = await conn.fetch('SELECT * FROM master_europe_players LIMIT 1')
        if rows:
            print('Columns:', rows[0].keys())
        # Check existence of npg
        try:
            await conn.fetch('SELECT npg FROM master_europe_players LIMIT 1')
            print('npg column exists')
        except asyncpg.exceptions.UndefinedColumnError:
            print('npg column does NOT exist')
        # Check npxg
        try:
            await conn.fetch('SELECT npxg FROM master_europe_players LIMIT 1')
            print('npxg column exists')
        except asyncpg.exceptions.UndefinedColumnError:
            print('npxg column does NOT exist')
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(check())