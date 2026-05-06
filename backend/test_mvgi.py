import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import sys
sys.path.insert(0, '.')
from app.api.scout_routes import _build_player

async def test_mvgi():
    engine = create_async_engine('postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat')
    async with engine.connect() as conn:
        # Get a sample player row (Keinan Davis)
        _FROM = "'áàâäãåçéèêëíìîïñóòôöõúùûüýÿøšćž'"
        _TO   = "'aaaaaaceeeeiiiinooooouuuuyyoscz'"
        NAME_NORM  = f"translate(lower(player_name), {_FROM}, {_TO})"
        PARAM_NORM = f"translate(lower(:p),           {_FROM}, {_TO})"
        AGG = """
            player_name,
            MAX(team_name)                        AS team_name,
            MAX(position)                         AS position,
            COALESCE(SUM(goals::float),      0)   AS goals,
            COALESCE(SUM(0),                 0)   AS npg,
            COALESCE(SUM(shots::float),      0)   AS shots,
            COALESCE(SUM(assists::float),    0)   AS assists,
            COALESCE(SUM(key_passes::float), 0)   AS key_passes,
            COALESCE(SUM(xg::float),         0)   AS xg,
            COALESCE(SUM(npxg::float),       0)   AS npxg,
            COALESCE(SUM(xa::float),         0)   AS xa,
            COALESCE(SUM(xgchain::float),    0)   AS xgchain,
            COALESCE(SUM(xgbuildup::float),  0)   AS xgbuildup,
            COALESCE(SUM(time::float),       1)   AS minutes,
            COUNT(DISTINCT match_id)          AS games
        """
        query = f"""
            SELECT {AGG}
            FROM master_europe_players
            WHERE {NAME_NORM} ILIKE {PARAM_NORM}
            GROUP BY player_name
            ORDER BY MAX(season::int) DESC
            LIMIT 1
        """
        res = await conn.execute(text(query), {"p": f"%Keinan Davis%"})
        row = res.fetchone()
        if not row:
            print("Player not found")
            return
        print("Row:", row)
        player = _build_player(row)
        print("Player data keys:", player.keys())
        print("Scores:", player.get('scores'))
        print("MVGI present?", 'MVGI' in player.get('scores', {}))
        if 'MVGI' in player.get('scores', {}):
            print("MVGI value:", player['scores']['MVGI'])
        else:
            print("MVGI missing")
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(test_mvgi())