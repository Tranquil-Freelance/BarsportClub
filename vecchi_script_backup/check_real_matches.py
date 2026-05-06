#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')

from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/xpalermostat_db'
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Count matches with understat_id > 20000
    result = conn.execute(
        text("""
            SELECT COUNT(*) as count 
            FROM matches 
            WHERE understat_id > 20000
        """)
    )
    count = result.scalar()
    print(f"Matches with understat_id > 20000: {count}")
    
    # Count those with status 'finito'
    result = conn.execute(
        text("""
            SELECT COUNT(*) as count 
            FROM matches 
            WHERE understat_id > 20000 AND status = 'finito'
        """)
    )
    count_finito = result.scalar()
    print(f"  - with status 'finito': {count_finito}")
    
    # Count those with scraping_status = 'PENDING' (or other)
    result = conn.execute(
        text("""
            SELECT scraping_status, COUNT(*) as count 
            FROM matches 
            WHERE understat_id > 20000 AND status = 'finito'
            GROUP BY scraping_status
            ORDER BY scraping_status
        """)
    )
    rows = result.fetchall()
    print("  - scraping_status distribution:")
    for row in rows:
        print(f"    {row.scraping_status}: {row.count}")
    
    # List first 10 matches for inspection
    result = conn.execute(
        text("""
            SELECT id, home_team, away_team, understat_id, status, scraping_status
            FROM matches 
            WHERE understat_id > 20000 AND status = 'finito'
            ORDER BY understat_id
            LIMIT 10
        """)
    )
    rows = result.fetchall()
    print("\nFirst 10 real matches (understat_id > 20000, finito):")
    for row in rows:
        print(f"  id={row.id}, home='{row.home_team}', away='{row.away_team}', understat_id={row.understat_id}, status='{row.status}', scraping='{row.scraping_status}'")