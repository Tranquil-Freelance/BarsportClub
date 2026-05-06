"""
Populate player_in column from player_stats using player_in_id.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import create_engine, text

engine = create_engine('postgresql+psycopg2://postgres:password@localhost:5432/xpalermostat')
with engine.connect() as conn:
    # Check if player_stats.player_id matches subs.player_in_id
    cnt = conn.execute(text("""
        SELECT COUNT(*) FROM substitutions s
        WHERE s.player_in_id IN (SELECT player_id FROM player_stats)
    """)).scalar()
    print(f"Matching player_in_id in player_stats.player_id: {cnt}")
    
    # Populate player_in from player_stats
    result = conn.execute(text("""
        UPDATE substitutions s
        SET player_in = ps.player_name
        FROM player_stats ps
        WHERE s.match_id = ps.match_id
          AND s.player_in_id = ps.player_id
          AND s.player_in IS NULL
    """))
    print(f"Updated player_in: {result.rowcount} rows")
    conn.commit()
    
    # Check remaining NULLs
    null_in = conn.execute(text("SELECT COUNT(*) FROM substitutions WHERE player_in IS NULL")).scalar()
    print(f"Remaining NULL player_in: {null_in}")
    
    # Also try using *_match_players tables
    for tbl in ['premier_match_players', 'seriea_match_players', 'bundesliga_match_players', 
                'laliga_match_players', 'ligue1_match_players']:
        try:
            result = conn.execute(text(f"""
                UPDATE substitutions s
                SET player_in = mp.player_name
                FROM {tbl} mp
                WHERE s.match_id = mp.match_id::integer
                  AND s.player_in_id = mp.player_id::integer
                  AND s.player_in IS NULL
            """))
            if result.rowcount > 0:
                print(f"Updated player_in from {tbl}: {result.rowcount} rows")
                conn.commit()
        except Exception as e:
            print(f"Error with {tbl}: {e}")
    
    # Final check
    null_in = conn.execute(text("SELECT COUNT(*) FROM substitutions WHERE player_in IS NULL")).scalar()
    print(f"\nFinal NULL player_in: {null_in}")
    
    # Show sample
    samples = conn.execute(text("""
        SELECT id, match_id, player_out, player_in, minute, team_type
        FROM substitutions
        WHERE player_in IS NOT NULL
        ORDER BY match_id DESC
        LIMIT 15
    """)).fetchall()
    print(f"\nSample data with player_in populated:")
    for s in samples:
        print(f"  {s}")
    
    # Show some still NULL
    if null_in > 0:
        samples = conn.execute(text("""
            SELECT id, match_id, player_out_id, player_in_id, player_out, player_in, minute
            FROM substitutions
            WHERE player_in IS NULL
            LIMIT 5
        """)).fetchall()
        print(f"\nSample rows still NULL:")
        for s in samples:
            print(f"  {s}")
