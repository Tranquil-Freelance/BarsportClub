#!/usr/bin/env python3
"""
Add missing column xpts to team_season_stat table if it doesn't exist.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import inspect
from app.db.database import engine

async def add_xpts_column():
    # Use the synchronous inspector via sync_engine
    sync_engine = engine.sync_engine
    inspector = inspect(sync_engine)
    columns = [col['name'] for col in inspector.get_columns('team_season_stat')]
    print("Existing columns:", columns)
    
    if 'xpts' not in columns:
        async with engine.connect() as conn:
            print("Adding column xpts...")
            await conn.execute('ALTER TABLE team_season_stat ADD COLUMN xpts FLOAT DEFAULT 0.0 NOT NULL')
            await conn.commit()
            print("Column xpts added successfully.")
    else:
        print("Column xpts already present.")

if __name__ == '__main__':
    asyncio.run(add_xpts_column())