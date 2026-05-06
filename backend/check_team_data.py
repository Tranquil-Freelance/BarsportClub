"""
Check team_name and team_type data quality.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import create_engine, text

engine = create_engine('postgresql+psycopg2://postgres:password@localhost:5432/xpalermostat')
with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT DISTINCT team_name, LEFT(team_type, 20) as tt_prefix
        FROM player_stats WHERE match_id = 30466
        LIMIT 10
    """)).fetchall()
    print("Match 30466 team data:")
    for r in rows:
        print(f"  team_name={repr(r[0])}, team_type_prefix={repr(r[1])}")
    
    # Check if team_type values always start with 'team_type'
    sample = conn.execute(text("""
        SELECT team_type FROM player_stats WHERE match_id = 30466 LIMIT 3
    """)).fetchall()
    print(f"\nRaw team_type samples: {[repr(r[0]) for r in sample]}")
    
    # Check if team_name contains the actual team name
    rows = conn.execute(text("""
        SELECT DISTINCT team_name FROM player_stats WHERE match_id = 30466
    """)).fetchall()
    print(f"\nDistinct team_names for match 30466:")
    for r in rows:
        print(f"  {repr(r[0])}")
    
    # Check match info
    match = conn.execute(text("""
        SELECT th.name as home, ta.name as away
        FROM matchcalendar m
        JOIN team th ON th.id = m.home_team_id
        JOIN team ta ON ta.id = m.away_team_id
        WHERE m.id = 30466
    """)).fetchone()
    print(f"\nMatch 30466 teams: home={match[0]}, away={match[1]}")
