#!/usr/bin/env python3
"""
Add missing columns to matches table using raw SQL.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from app.db.database import engine

async def add_missing_columns():
    # List of columns to add with SQL definitions
    columns_to_add = [
        ('home_score', 'INTEGER'),
        ('away_score', 'INTEGER'),
        ('status', 'VARCHAR DEFAULT \'scheduled\''),
        ('date', 'TIMESTAMP'),
        ('matchday', 'INTEGER'),
        ('understat_id', 'INTEGER'),
        ('start_time', 'TIMESTAMP'),
        ('last_scraped_at', 'TIMESTAMP'),
        ('scraping_status', 'VARCHAR DEFAULT \'PENDING\''),
        ('error_log', 'TEXT'),
        ('home_xg', 'FLOAT'),
        ('away_xg', 'FLOAT'),
        ('home_shots', 'INTEGER'),
        ('away_shots', 'INTEGER'),
        ('home_shots_on_target', 'INTEGER'),
        ('away_shots_on_target', 'INTEGER'),
    ]
    
    async with engine.connect() as conn:
        for col_name, col_def in columns_to_add:
            # Use IF NOT EXISTS to avoid errors if column already exists
            sql = f'ALTER TABLE matches ADD COLUMN IF NOT EXISTS {col_name} {col_def}'
            print(f'Executing: {sql}')
            try:
                await conn.execute(text(sql))
                await conn.commit()
                print(f'  -> Column {col_name} added or already exists.')
            except Exception as e:
                print(f'  -> Error: {e}')
        print('All columns processed.')

if __name__ == '__main__':
    asyncio.run(add_missing_columns())