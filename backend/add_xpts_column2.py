#!/usr/bin/env python3
"""
Add missing column xpts to team_season_stat table if it doesn't exist.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from app.db.database import engine

async def add_xpts_column():
    async with engine.connect() as conn:
        # Check if column exists
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'team_season_stat' AND column_name = 'xpts'
        """))
        exists = result.first() is not None
        if not exists:
            print("Adding column xpts...")
            await conn.execute(text("""
                ALTER TABLE team_season_stat 
                ADD COLUMN xpts FLOAT DEFAULT 0.0 NOT NULL
            """))
            await conn.commit()
            print("Column xpts added successfully.")
        else:
            print("Column xpts already present.")
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(add_xpts_column())