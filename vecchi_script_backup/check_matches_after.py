#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')
from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/xpalermostat_db'
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    # Check by understat_id 29
    result = conn.execute(
        text('SELECT id, understat_id, status, home_team, away_team FROM matches WHERE understat_id = :id'),
        {'id': 29}
    )
    rows = result.fetchall()
    print('Rows with understat_id 29:', rows)
    # Check by primary key id 29
    result2 = conn.execute(
        text('SELECT id, understat_id, status FROM matches WHERE id = 29')
    )
    row2 = result2.fetchone()
    print('Row with id 29:', row2)
    # Check matchcalendar row id 29
    result3 = conn.execute(
        text('SELECT id, is_completed, is_scraped FROM matchcalendar WHERE id = 29')
    )
    row3 = result3.fetchone()
    print('MatchCalendar row id 29:', row3)