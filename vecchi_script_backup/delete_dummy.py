#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')

from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/xpalermostat_db'
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # First, list rows that will be deleted
    result = conn.execute(
        text("""
            SELECT id, home_team, away_team, understat_id, status
            FROM matches 
            WHERE home_team = 'Home' OR understat_id = 29
            ORDER BY id
        """)
    )
    rows = result.fetchall()
    print(f"Rows to delete: {len(rows)}")
    for row in rows:
        print(f"  id={row.id}, home='{row.home_team}', away='{row.away_team}', understat_id={row.understat_id}, status='{row.status}'")
    
    # Delete them
    delete_stmt = text("""
        DELETE FROM matches 
        WHERE home_team = 'Home' OR understat_id = 29
    """)
    result = conn.execute(delete_stmt)
    deleted_count = result.rowcount
    print(f"\nDeleted {deleted_count} rows.")
    
    # Commit
    conn.commit()
    
    # Verify deletion
    result = conn.execute(
        text("SELECT COUNT(*) FROM matches WHERE home_team = 'Home' OR understat_id = 29")
    )
    remaining = result.scalar()
    print(f"Remaining rows matching condition: {remaining}")
    
    # Also check total matches count
    result = conn.execute(text("SELECT COUNT(*) FROM matches"))
    total = result.scalar()
    print(f"Total matches after deletion: {total}")