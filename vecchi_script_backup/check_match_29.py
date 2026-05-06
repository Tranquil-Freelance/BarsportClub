#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')

from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/xpalermostat_db'
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    # Check Match table by id (primary key)
    result = conn.execute(
        text('SELECT id, understat_id, status, scraping_status FROM matches WHERE id = :id'),
        {'id': 29}
    )
    row = result.fetchone()
    if row:
        print(f'Match row (id=29): {row}')
    else:
        print('Match not found by id 29')
    
    # Check by understat_id
    result2 = conn.execute(
        text('SELECT id, understat_id, status, scraping_status FROM matches WHERE understat_id = :id'),
        {'id': 29}
    )
    row2 = result2.fetchone()
    if row2:
        print(f'Match by understat_id=29: {row2}')
    else:
        print('Match not found by understat_id 29')
    
    # Check match_calendar table (match_id refers to understat_id?)
    result3 = conn.execute(
        text('SELECT id, match_id, is_completed, is_scraped FROM match_calendar WHERE match_id = :id'),
        {'id': 29}
    )
    row3 = result3.fetchone()
    if row3:
        print(f'MatchCalendar: {row3}')
    else:
        print('MatchCalendar not found for match_id 29')
    
    # Also check if there are any matches with understat_id 29 but different id
    result4 = conn.execute(
        text('SELECT id, understat_id, status, scraping_status FROM matches WHERE understat_id = 29')
    )
    rows = result4.fetchall()
    if rows:
        print(f'All matches with understat_id 29: {rows}')
    else:
        print('No matches with understat_id 29')