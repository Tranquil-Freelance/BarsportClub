#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:postgres@localhost/xpalermostat_db'
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(text("SELECT id, home_team, away_team FROM matches WHERE home_team LIKE '%Como%' OR away_team LIKE '%Como%'"))
    rows = result.fetchall()
    if rows:
        print(f"Found {len(rows)} matches with Como:")
        for row in rows:
            print(f"Match ID: {row.id}, {row.home_team} vs {row.away_team}")
    else:
        print("No Como matches in database.")