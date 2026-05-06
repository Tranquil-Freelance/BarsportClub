#!/usr/bin/env python3
"""
Add round column to matchcalendar table if not exists.
"""
import asyncio
import sys
sys.path.append('.')
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def add_column():
    engine = create_async_engine('postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat')
    async with engine.connect() as conn:
        # Check if column exists
        result = await conn.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name='matchcalendar' AND column_name='round'")
        )
        if result.fetchone():
            print("Column 'round' already exists")
        else:
            print("Adding column 'round' to matchcalendar table")
            await conn.execute(text("ALTER TABLE matchcalendar ADD COLUMN round INTEGER NULL"))
            await conn.commit()
            print("Column added successfully")
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(add_column())