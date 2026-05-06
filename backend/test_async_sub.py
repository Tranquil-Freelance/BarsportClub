import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = 'postgresql+asyncpg://postgres:your_secure_password@127.0.0.1:5432/xpalermostat_db'

async def test():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        try:
            rows = (await conn.execute(text("""
                SELECT player_out, player_in, minute
                FROM substitutions
                WHERE match_id = :mid AND team_type = :tt
                ORDER BY minute ASC
            """), {"mid": 30133, "tt": "h"})).fetchall()
            for r in rows:
                print(r)
        except Exception as e:
            print(f"Error: {e}")
    await engine.dispose()

asyncio.run(test())
