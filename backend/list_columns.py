import asyncio
import asyncpg

async def list_cols():
    conn = await asyncpg.connect('postgresql://postgres:password@localhost:5432/xpalermostat')
    try:
        # Get column names
        rows = await conn.fetch('SELECT * FROM master_europe_players LIMIT 1')
        if rows:
            print('Columns:', rows[0].keys())
            # also check for specific columns
            for col in rows[0].keys():
                print(col)
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(list_cols())