#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')
from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/xpalermostat_db'
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # 1. Update matchcalendar row id 29
    conn.execute(
        text('UPDATE matchcalendar SET is_completed = TRUE, is_scraped = TRUE WHERE id = :id'),
        {'id': 29}
    )
    print('Updated matchcalendar row 29: is_completed=True, is_scraped=True')
    
    # 2. Check if matches row with understat_id 29 exists; if not, insert
    result = conn.execute(
        text('SELECT id FROM matches WHERE understat_id = :id'),
        {'id': 29}
    )
    existing = result.fetchone()
    if existing:
        print(f'Matches row already exists with id {existing.id}')
        # Update status and scraping_status
        conn.execute(
            text('''
                UPDATE matches 
                SET status = 'finito', 
                    scraping_status = 'SUCCESS',
                    home_team = COALESCE(home_team, 'Home'),
                    away_team = COALESCE(away_team, 'Away')
                WHERE understat_id = :id
            '''),
            {'id': 29}
        )
        print('Updated matches row with understat_id 29')
    else:
        # Insert new match row (minimal columns)
        conn.execute(
            text('''
                INSERT INTO matches (understat_id, status, scraping_status, home_team, away_team)
                VALUES (:id, 'finito', 'SUCCESS', 'Home', 'Away')
            '''),
            {'id': 29}
        )
        print('Inserted new matches row with understat_id 29')
    
    # 3. Update existing row with id 29 (different understat_id) if needed
    conn.execute(
        text('UPDATE matches SET scraping_status = \'SUCCESS\' WHERE id = 29')
    )
    print('Updated matches row id 29 scraping_status to SUCCESS')
    
    conn.commit()
    print('All updates committed.')