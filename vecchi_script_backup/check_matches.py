#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')

from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/xpalermostat_db'
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    match_ids = [27362, 27371, 27382]
    for match_id in match_ids:
        result = conn.execute(
            text('SELECT id, home_team, away_team FROM matches WHERE id = :match_id'),
            {'match_id': match_id}
        )
        row = result.fetchone()
        if row:
            print(f"Match ID {match_id}: exists - {row.home_team} vs {row.away_team}")
        else:
            print(f"Match ID {match_id}: not found in matches table")