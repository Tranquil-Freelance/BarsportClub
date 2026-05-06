"""
Check why player_in_id values don't match player table.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import create_engine, text

engine = create_engine('postgresql+psycopg2://postgres:password@localhost:5432/xpalermostat')
with engine.connect() as conn:
    # Check non-matching player_in_ids
    rows = conn.execute(text("""
        SELECT DISTINCT s.player_in_id
        FROM substitutions s
        WHERE s.player_in_id NOT IN (SELECT id FROM player)
        LIMIT 10
    """)).fetchall()
    print("player_in_ids NOT in player table:")
    for r in rows:
        print(f"  {r[0]}")
    
    cnt = conn.execute(text("""
        SELECT COUNT(*) FROM substitutions
        WHERE player_in_id NOT IN (SELECT id FROM player)
    """)).scalar()
    print(f"Total non-matching player_in_ids: {cnt}")
    
    cnt2 = conn.execute(text("""
        SELECT COUNT(*) FROM substitutions
        WHERE player_in_id IN (SELECT id FROM player)
    """)).scalar()
    print(f"Matching player_in_ids: {cnt2}")
    
    r = conn.execute(text("SELECT MIN(player_in_id), MAX(player_in_id) FROM substitutions")).fetchone()
    print(f"player_in_id range: {r[0]} to {r[1]}")
    
    r = conn.execute(text("SELECT MIN(id), MAX(id) FROM player")).fetchone()
    print(f"player id range: {r[0]} to {r[1]}")
    
    # Try to find some matching player_in_id
    rows = conn.execute(text("""
        SELECT s.player_in_id, p.name
        FROM substitutions s
        JOIN player p ON p.id = s.player_in_id
        LIMIT 10
    """)).fetchall()
    if rows:
        print("\nMatching player_in entries:")
        for r in rows:
            print(f"  ID {r[0]}: {r[1]}")
    else:
        print("\nNo matching player_in entries found")
    
    # Check the player_registry table if it exists
    try:
        rows = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'player_registry'
            ORDER BY ordinal_position
        """)).fetchall()
        print(f"\nplayer_registry columns: {[r[0] for r in rows]}")
        
        # Sample
        rows = conn.execute(text("""
            SELECT * FROM player_registry LIMIT 5
        """)).fetchall()
        print("player_registry sample:")
        for r in rows:
            print(f"  {r}")
    except:
        print("\nNo player_registry table")
