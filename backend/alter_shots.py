#!/usr/bin/env python3
"""
Add missing columns to shots table, ignoring errors if they already exist.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from app.db.database import engine

async def alter_shots():
    async with engine.connect() as conn:
        # Add situation column
        try:
            await conn.execute(text('ALTER TABLE shots ADD COLUMN situation VARCHAR'))
            print("Added situation column")
        except Exception as e:
            print(f"Column situation may already exist: {e}")
        
        # Add shotType column (note case-sensitive column name)
        try:
            await conn.execute(text('ALTER TABLE shots ADD COLUMN "shotType" VARCHAR'))
            print('Added "shotType" column')
        except Exception as e:
            print(f'Column shotType may already exist: {e}')
        
        # Add assist column
        try:
            await conn.execute(text('ALTER TABLE shots ADD COLUMN assist VARCHAR'))
            print("Added assist column")
        except Exception as e:
            print(f"Column assist may already exist: {e}")
        
        await conn.commit()
        print("Alterations completed.")

if __name__ == '__main__':
    asyncio.run(alter_shots())