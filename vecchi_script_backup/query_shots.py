#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')

from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/xpalermostat_db'
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    # Query shots for each match ID
    match_ids = [27362, 27371, 27382]
    for match_id in match_ids:
        result = conn.execute(
            text('SELECT COUNT(*) as shot_count FROM shots WHERE match_id = :match_id'),
            {'match_id': match_id}
        )
        row = result.fetchone()
        count = row[0] if row else 0
        print(f"Match ID {match_id}: {count} shots")
    # Also total shots across all matches
    result = conn.execute(text('SELECT COUNT(*) FROM shots'))
    total = result.fetchone()[0]
    print(f"\nTotal shots in database: {total}")