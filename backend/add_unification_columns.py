#!/usr/bin/env python3
"""
Migration script to add columns needed for unification of Match and MatchCalendar.
Also renames home_xg/away_xg to home_xG/away_xG and copies date/matchday data.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from app.db.database import engine

async def migrate():
    async with engine.connect() as conn:
        # 1. Skip renaming columns (home_xg/away_xg already mapped to home_xG/away_xG in model)
        
        # 2. Add missing columns (if not exist)
        columns_to_add = [
            ('home_team_id', 'INTEGER'),
            ('away_team_id', 'INTEGER'),
            ('league_id', 'INTEGER'),
            ('match_datetime', 'TIMESTAMP'),
            ('round', 'INTEGER'),
            ('is_completed', 'BOOLEAN DEFAULT FALSE'),
            ('is_scraped', 'BOOLEAN DEFAULT FALSE'),
            ('home_goals', 'INTEGER'),
            ('away_goals', 'INTEGER'),
        ]
        
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
        
        # 3. Copy data from date to match_datetime where match_datetime is NULL
        print('\nCopying data from date to match_datetime...')
        copy_sql = """
            UPDATE matches 
            SET match_datetime = date 
            WHERE match_datetime IS NULL AND date IS NOT NULL
        """
        try:
            result = await conn.execute(text(copy_sql))
            await conn.commit()
            print(f'  -> Updated {result.rowcount} rows.')
        except Exception as e:
            print(f'  -> Error copying date: {e}')
        
        # 4. Copy data from matchday to round where round is NULL
        print('\nCopying data from matchday to round...')
        copy_sql = """
            UPDATE matches 
            SET round = matchday 
            WHERE round IS NULL AND matchday IS NOT NULL
        """
        try:
            result = await conn.execute(text(copy_sql))
            await conn.commit()
            print(f'  -> Updated {result.rowcount} rows.')
        except Exception as e:
            print(f'  -> Error copying matchday: {e}')
        
        # 5. Optionally add foreign key constraints (skip for now as tables may not exist)
        # We'll leave them as nullable columns.
        
        print('\nMigration completed.')
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(migrate())