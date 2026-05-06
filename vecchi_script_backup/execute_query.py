#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')

from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/xpalermostat_db'
engine = create_engine(DATABASE_URL)

query = """
SELECT id, home_team, away_team, understat_id 
FROM matches 
WHERE status = 'FT' 
LIMIT 5;
"""

with engine.connect() as conn:
    result = conn.execute(text(query))
    rows = result.fetchall()
    if not rows:
        print("No matches found with status 'FT'.")
    else:
        print("Matches with status 'FT':")
        for row in rows:
            print(f"id: {row.id}, home_team: {row.home_team}, away_team: {row.away_team}, understat_id: {row.understat_id}")