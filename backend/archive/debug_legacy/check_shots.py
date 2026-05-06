#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:postgres@localhost/xpalermostat_db'
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(text('SELECT match_id, COUNT(*) as shot_count FROM shots GROUP BY match_id ORDER BY match_id'))
    rows = result.fetchall()
    if rows:
        print(f"Found {len(rows)} matches with shots:")
        for row in rows:
            print(f"Match ID: {row.match_id}, shots: {row.shot_count}")
    else:
        print("No shots in database.")