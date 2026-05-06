"""
Debug why lineup endpoint returns empty starters for match 30466.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import create_engine, text

engine = create_engine('postgresql+psycopg2://postgres:password@localhost:5432/xpalermostat')
with engine.connect() as conn:
    mid = 30466
    
    # Check match calendar
    match = conn.execute(text("""
        SELECT id, home_team_id, away_team_id, home_goals, away_goals
        FROM matchcalendar WHERE id = :mid
    """), {"mid": mid}).fetchone()
    print(f"Match: {match}")
    
    # Check player_stats for this match
    rows = conn.execute(text("""
        SELECT player_name, position, team_type, time
        FROM player_stats 
        WHERE match_id = :mid
        ORDER BY team_type, position
    """), {"mid": mid}).fetchall()
    print(f"\nplayer_stats for match {mid}: {len(rows)} rows")
    for r in rows[:5]:
        print(f"  {r}")
    
    # Check distinct team_types
    tts = conn.execute(text("""
        SELECT DISTINCT team_type FROM player_stats WHERE match_id = :mid
    """), {"mid": mid}).fetchall()
    print(f"\nDistinct team_types: {[r[0] for r in tts]}")
    
    # Try raw query with unquoted column
    rows = conn.execute(text("""
        SELECT player_name, position, "xG", "xA", goals, assists
        FROM player_stats
        WHERE match_id = :mid AND team_type = :tt
        LIMIT 5
    """), {"mid": mid, "tt": "h"}).fetchall()
    print(f"\nHome players (with xG/xA quoted): {len(rows)}")
    for r in rows:
        print(f"  {r}")
    
    # Check the actual column names in player_stats
    cols = conn.execute(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'player_stats'
        ORDER BY ordinal_position
    """)).fetchall()
    print(f"\nplayer_stats columns:")
    for c in cols:
        print(f"  {c[0]}")
