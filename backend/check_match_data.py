"""
Check which matches have data in xpalermostat database.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import create_engine, text

engine = create_engine('postgresql+psycopg2://postgres:password@localhost:5432/xpalermostat')
with engine.connect() as conn:
    cnt = conn.execute(text("SELECT COUNT(*) FROM player_stats WHERE match_id = 30133")).scalar()
    print(f"Match 30133 player_stats rows: {cnt}")
    
    rows = conn.execute(text("""
        SELECT DISTINCT match_id FROM player_stats 
        ORDER BY match_id DESC LIMIT 10
    """)).fetchall()
    print("Latest match IDs with player_stats:")
    for r in rows:
        mid = r[0]
        cnt2 = conn.execute(text(f"SELECT COUNT(*) FROM player_stats WHERE match_id = {mid}")).scalar()
        
        # Check for 'Sub' position players
        subs_count = conn.execute(text(f"""
            SELECT COUNT(*) FROM player_stats 
            WHERE match_id = {mid} AND position = 'Sub'
        """)).scalar()
        
        starters = conn.execute(text(f"""
            SELECT COUNT(*) FROM player_stats 
            WHERE match_id = {mid} AND position != 'Sub'
        """)).scalar()
        
        print(f"  match {mid}: total={cnt2}, starters={starters}, subs={subs_count}")
    
    # Check substitutions for these matches
    print("\nSubstitutions for these matches:")
    for r in rows:
        mid = r[0]
        cnt3 = conn.execute(text(f"SELECT COUNT(*) FROM substitutions WHERE match_id = {mid}")).scalar()
        if cnt3 > 0:
            print(f"  match {mid}: {cnt3} substitutions")
