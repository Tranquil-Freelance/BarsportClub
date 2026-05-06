#!/usr/bin/env python3
"""
Add missing columns (situation, shotType, assist) to shots table if they don't exist.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import inspect
from app.db.database import engine

async def add_missing_columns():
    # Use the synchronous inspector via sync_engine
    sync_engine = engine.sync_engine
    inspector = inspect(sync_engine)
    columns = [col['name'] for col in inspector.get_columns('shots')]
    print("Existing columns:", columns)
    
    missing = []
    if 'situation' not in columns:
        missing.append('situation VARCHAR')
    if 'shotType' not in columns:
        missing.append('"shotType" VARCHAR')
    if 'assist' not in columns:
        missing.append('assist VARCHAR')
    
    if missing:
        async with engine.connect() as conn:
            for col_def in missing:
                col_name = col_def.split()[0].strip('"')
                print(f"Adding column {col_name}...")
                await conn.execute(f'ALTER TABLE shots ADD COLUMN {col_def}')
                await conn.commit()
            print("Columns added successfully.")
    else:
        print("All columns already present.")

if __name__ == '__main__':
    asyncio.run(add_missing_columns())