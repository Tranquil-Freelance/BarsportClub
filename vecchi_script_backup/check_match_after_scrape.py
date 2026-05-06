#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')
import time
from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/xpalermostat_db'
engine = create_engine(DATABASE_URL)

print("Checking matches table for understat_id 29...")
with engine.connect() as conn:
    result = conn.execute(
        text('SELECT id, understat_id, status, scraping_status, home_team, away_team FROM matches WHERE understat_id = :id'),
        {'id': 29}
    )
    row = result.fetchone()
    if row:
        print(f'Match found: {row}')
    else:
        print('No match with understat_id 29')
        
    # Also check matchcalendar for any match with id 29 (primary key) or maybe home/away teams
    result2 = conn.execute(
        text('SELECT id, home_team_id, away_team_id, is_completed, is_scraped FROM matchcalendar WHERE id = :id'),
        {'id': 29}
    )
    row2 = result2.fetchone()
    if row2:
        print(f'MatchCalendar row id 29: {row2}')
    else:
        print('No MatchCalendar row with id 29')
        
    # List all matches with understat_id like 29 (maybe there are multiple)
    result3 = conn.execute(
        text('SELECT id, understat_id, status FROM matches WHERE understat_id = 29')
    )
    rows = result3.fetchall()
    print(f'Total matches with understat_id 29: {len(rows)}')
    for r in rows:
        print(f'  {r}')