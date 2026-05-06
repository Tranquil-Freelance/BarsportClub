"""Test the lineup query after the team_name::int fix."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:your_secure_password@localhost:5432/xpalermostat"

async def test():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        # Test match 30466 - home team (id=131)
        rows_h = (await conn.execute(text("""
            SELECT player_name, position 
            FROM player_stats 
            WHERE match_id = 30466 AND team_name::int = 131
            ORDER BY position
        """))).fetchall()
        print(f"HOME (131): {len(rows_h)} players")
        for r in rows_h:
            print(f"  {r[0]:30s} {r[1]}")
        
        print()
        
        # Test match 30466 - away team (id=123)
        rows_a = (await conn.execute(text("""
            SELECT player_name, position 
            FROM player_stats 
            WHERE match_id = 30466 AND team_name::int = 123
            ORDER BY position
        """))).fetchall()
        print(f"AWAY (123): {len(rows_a)} players")
        for r in rows_a:
            print(f"  {r[0]:30s} {r[1]}")
        
        print()
        print("--- Substitutions for match 30466 ---")
        subs = (await conn.execute(text("""
            SELECT player_out, player_in, minute, team_type
            FROM substitutions
            WHERE match_id = 30466
            ORDER BY minute
        """))).fetchall()
        print(f"{len(subs)} substitutions")
        for s in subs:
            print(f"  {s[2]}': {s[0]} -> {s[1]} ({s[3]})")
    
    await engine.dispose()

asyncio.run(test())
