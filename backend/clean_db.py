#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')

from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/xpalermostat_db'
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # 1. DELETE FROM matchcalendar WHERE is_completed = False AND id = 29;
    delete_matchcalendar = text("""
        DELETE FROM matchcalendar 
        WHERE is_completed = False AND id = 29
    """)
    result1 = conn.execute(delete_matchcalendar)
    print(f"Deleted {result1.rowcount} row(s) from matchcalendar (id=29).")
    
    # 2. DELETE FROM matches WHERE home_team = 'Home' OR understat_id < 20000;
    delete_matches = text("""
        DELETE FROM matches 
        WHERE home_team = 'Home' OR understat_id < 20000
    """)
    result2 = conn.execute(delete_matches)
    print(f"Deleted {result2.rowcount} row(s) from matches (home_team='Home' or understat_id < 20000).")
    
    # 3. UPDATE matches SET scraping_status = 'PENDING' WHERE status = 'finito' AND scraping_status != 'SUCCESS';
    update_matches = text("""
        UPDATE matches 
        SET scraping_status = 'PENDING' 
        WHERE status = 'finito' AND scraping_status != 'SUCCESS'
    """)
    result3 = conn.execute(update_matches)
    print(f"Updated {result3.rowcount} row(s) to PENDING where status='finito' and scraping_status != 'SUCCESS'.")
    
    conn.commit()
    print("All three SQL statements executed successfully.")