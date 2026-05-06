#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')

from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/xpalermostat_db'
engine = create_engine(DATABASE_URL)

# Original query with 'FT' (no matches)
query_ft = """
SELECT id, home_team, away_team, understat_id 
FROM matches 
WHERE status = 'FT' 
LIMIT 5;
"""

# Corrected query with 'finito' (Italian for finished)
query_finito = """
SELECT id, home_team, away_team, understat_id 
FROM matches 
WHERE status = 'finito' 
LIMIT 5;
"""

with engine.connect() as conn:
    # Execute corrected query
    result = conn.execute(text(query_finito))
    rows = result.fetchall()
    
    print("=== Query Results ===")
    print("NOTE: Status 'FT' returned 0 matches. Using 'finito' (Italian) which matches 285 finished matches.")
    print("")
    if not rows:
        print("No matches found with status 'finito'.")
    else:
        print("First 5 matches with status = 'finito':")
        print("")
        print(f"{'id':<8} {'home_team':<25} {'away_team':<25} {'understat_id':<12}")
        print("-" * 70)
        for row in rows:
            print(f"{row.id:<8} {row.home_team:<25} {row.away_team:<25} {row.understat_id if row.understat_id else 'NULL':<12}")
    
    # Also show count of finito matches
    count_result = conn.execute(text("SELECT COUNT(*) FROM matches WHERE status = 'finito'"))
    total = count_result.scalar()
    print(f"\nTotal matches with status 'finito': {total}")