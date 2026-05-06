"""
Find which table maps understat player IDs to names.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import create_engine, text

engine = create_engine('postgresql+psycopg2://postgres:password@localhost:5432/xpalermostat')
with engine.connect() as conn:
    # Check player_stats for player_id column
    rows = conn.execute(text("""
        SELECT column_name, data_type FROM information_schema.columns 
        WHERE table_name = 'player_stats'
        ORDER BY ordinal_position
    """)).fetchall()
    print("player_stats columns:")
    for r in rows:
        print(f"  {r[0]} ({r[1]})")
    
    # Check master_europe_players
    rows = conn.execute(text("""
        SELECT column_name, data_type FROM information_schema.columns 
        WHERE table_name = 'master_europe_players'
        ORDER BY ordinal_position
    """)).fetchall()
    print("\nmaster_europe_players columns:")
    for r in rows:
        print(f"  {r[0]} ({r[1]})")
    
    # Find all *_players tables
    rows = conn.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE '%player%'
        ORDER BY table_name
    """)).fetchall()
    print("\nAll player-related tables:")
    for r in rows:
        print(f"  {r[0]}")
        try:
            cols = conn.execute(text(f"""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = '{r[0]}'
                ORDER BY ordinal_position
            """)).fetchall()
            print(f"    -> {[c[0] for c in cols]}")
        except:
            pass
    
    # Try to find a match between understat player IDs and names
    # Check if there's a column with understat_id in any table
    rows = conn.execute(text("""
        SELECT table_name, column_name FROM information_schema.columns 
        WHERE column_name IN ('understat_id', 'player_id', 'understatid', 'uid')
    """)).fetchall()
    print("\nTables with understat/player ID columns:")
    for r in rows:
        print(f"  {r[0]}.{r[1]}")
    
    # Check player_stats for player name match with substitutions
    print("\nSample: match 30165 substitutions -> player_stats players")
    subs = conn.execute(text("""
        SELECT s.player_out, s.player_in, s.minute, s.team_type
        FROM substitutions s
        WHERE s.match_id = 30165 AND s.team_type = 'h'
        ORDER BY s.minute
    """)).fetchall()
    print("Home substitutions for match 30165:")
    for s in subs:
        print(f"  {s}")
    
    # Check player_stats for match 30165 home team
    stats = conn.execute(text("""
        SELECT player_name, position, time
        FROM player_stats
        WHERE match_id = 30165 AND team_type = 'h'
        ORDER BY time DESC
    """)).fetchall()
    print("\nHome player_stats for match 30165:")
    for s in stats:
        print(f"  {s[0]} ({s[1]}, {s[2]}min)")
