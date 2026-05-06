#!/usr/bin/env python3
"""
Check columns of matches table.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from app.db.database import engine

async def main():
    async with engine.connect() as conn:
        # Raw SQL to get column names
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'matches'
            ORDER BY ordinal_position
        """))
        rows = result.fetchall()
        print('Matches table columns:')
        column_names = []
        for row in rows:
            col_name, data_type, is_nullable = row
            print(f'  {col_name} {data_type} ({is_nullable})')
            column_names.append(col_name)
        print('\nColumn names list:', column_names)
        
        # Check which columns from the Match model are missing
        expected_columns = [
            'home_team_id', 'away_team_id', 'league_id', 'match_datetime',
            'round', 'is_completed', 'is_scraped', 'home_goals', 'away_goals',
            'home_xG', 'away_xG', 'home_xg', 'away_xg'
        ]
        missing = [col for col in expected_columns if col not in column_names]
        print('\nMissing columns:', missing)
        if missing:
            print('Need to add these columns via migration.')
        else:
            print('All expected columns exist.')
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(main())