#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')

from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/xpalermostat_db'
engine = create_engine(DATABASE_URL)

query = """
SELECT status, COUNT(*) as count 
FROM matches 
GROUP BY status 
ORDER BY count DESC;
"""

with engine.connect() as conn:
    result = conn.execute(text(query))
    rows = result.fetchall()
    if not rows:
        print("No matches found.")
    else:
        print("Status distribution in matches table:")
        for row in rows:
            print(f"  status: '{row.status}', count: {row.count}")