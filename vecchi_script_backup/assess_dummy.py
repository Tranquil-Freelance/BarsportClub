#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')

from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/xpalermostat_db'
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Count rows where home_team = 'Home' OR understat_id = 29
    result = conn.execute(
        text("""
            SELECT COUNT(*) as count 
            FROM matches 
            WHERE home_team = 'Home' OR understat_id = 29
        """)
    )
    count = result.scalar()
    print(f"Rows to delete (home_team='Home' OR understat_id=29): {count}")
    
    # List them
    result = conn.execute(
        text("""
            SELECT id, home_team, away_team, understat_id, status
            FROM matches 
            WHERE home_team = 'Home' OR understat_id = 29
            ORDER BY id
        """)
    )
    rows = result.fetchall()
    if rows:
        print("\nDetails:")
        for row in rows:
            print(f"  id={row.id}, home='{row.home_team}', away='{row.away_team}', understat_id={row.understat_id}, status='{row.status}'")
    
    # Also check for away_team = 'Away' maybe
    result = conn.execute(
        text("SELECT COUNT(*) FROM matches WHERE away_team = 'Away'")
    )
    away_count = result.scalar()
    print(f"\nRows with away_team='Away': {away_count}")
    
    # Check for any other dummy patterns (home_team='Home' and away_team='Away')
    result = conn.execute(
        text("""
            SELECT COUNT(*) FROM matches 
            WHERE home_team = 'Home' AND away_team = 'Away'
        """)
    )
    both_count = result.scalar()
    print(f"Rows with home='Home' AND away='Away': {both_count}")