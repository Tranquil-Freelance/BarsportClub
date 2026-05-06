#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')

from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/xpalermostat_db'
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Update matches with understat_id > 20000, status = 'finito', scraping_status = 'ERROR' to 'PENDING'
    update_stmt = text("""
        UPDATE matches 
        SET scraping_status = 'PENDING', error_log = NULL 
        WHERE understat_id > 20000 
          AND status = 'finito' 
          AND scraping_status = 'ERROR'
    """)
    result = conn.execute(update_stmt)
    updated = result.rowcount
    print(f"Updated {updated} matches from ERROR to PENDING.")
    
    # Verify
    result = conn.execute(
        text("""
            SELECT scraping_status, COUNT(*) as count 
            FROM matches 
            WHERE understat_id > 20000 AND status = 'finito'
            GROUP BY scraping_status
        """)
    )
    rows = result.fetchall()
    print("Current scraping_status distribution:")
    for row in rows:
        print(f"  {row.scraping_status}: {row.count}")
    
    conn.commit()