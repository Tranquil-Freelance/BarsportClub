import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat')
    async with engine.connect() as conn:
        # get max season
        season_res = await conn.execute(text('SELECT MAX(season::int) FROM master_europe_players'))
        season = season_res.scalar()
        print('Max season:', season)
        # count Sub players with >=600 minutes in that season
        res = await conn.execute(text('''
            SELECT player_name, SUM(time::float) as minutes
            FROM master_europe_players
            WHERE season::int = :s AND position = 'Sub'
            GROUP BY player_name
            HAVING SUM(time::float) >= 600
        '''), {'s': season})
        rows = res.fetchall()
        print(f'Number of Sub players in season {season} with >=600 minutes: {len(rows)}')
        for r in rows[:5]:
            print(f'  {r[0]}: {r[1]}')
        # also check total players in that season regardless of position
        res2 = await conn.execute(text('SELECT COUNT(DISTINCT player_name) FROM master_europe_players WHERE season::int = :s'), {'s': season})
        total = res2.scalar()
        print(f'Total distinct players in season {season}: {total}')
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(main())