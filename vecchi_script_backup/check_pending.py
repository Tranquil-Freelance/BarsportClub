#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')

from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/xpalermostat_db'
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Count matches with understat_id > 20000, status = 'finito', scraping_status = 'PENDING'
    result = conn.execute(text("""
        SELECT COUNT(*) as count
        FROM matches
        WHERE understat_id > 20000
          AND status = 'finito'
          AND scraping_status = 'PENDING'
    """))
    row = result.fetchone()
    print(f"Pending matches: {row.count}")
    
    # Show details
    result = conn.execute(text("""
        SELECT id, understat_id, home_team, away_team, scraping_status, status
        FROM matches
        WHERE understat_id > 20000
          AND status = 'finito'
          AND scraping_status = 'PENDING'
        LIMIT 10
    """))
    for r in result:
        print(f"  id={r.id}, understat_id={r.understat_id}, {r.home_team} vs {r.away_team}, scraping_status={r.scraping_status}, status={r.status}")