"""
Add text columns (player_out, player_in) and team_type to the existing substitutions table.
Then populate them from the player table and player_stats.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import create_engine, text

URL = "postgresql+psycopg2://postgres:password@localhost:5432/xpalermostat"
engine = create_engine(URL)

with engine.connect() as conn:
    # 1. Add player_out VARCHAR column
    for col in ['player_out VARCHAR(255)', 'player_in VARCHAR(255)', 'team_type VARCHAR(5) DEFAULT NULL']:
        col_name = col.split()[0]
        try:
            conn.execute(text(f"ALTER TABLE substitutions ADD COLUMN {col}"))
            print(f"Added column: {col_name}")
        except Exception as e:
            print(f"Column {col_name} note: {e}")
    
    conn.commit()
    
    # 2. Populate player_out and player_in from player table
    result = conn.execute(text("""
        UPDATE substitutions s
        SET player_out = p.name
        FROM player p
        WHERE s.player_out_id = p.id
        AND s.player_out IS NULL
    """))
    print(f"Updated player_out: {result.rowcount} rows")
    
    result = conn.execute(text("""
        UPDATE substitutions s
        SET player_in = p.name
        FROM player p
        WHERE s.player_in_id = p.id
        AND s.player_in IS NULL
    """))
    print(f"Updated player_in: {result.rowcount} rows")
    
    conn.commit()
    
    # 3. Populate team_type via player_stats cross-reference
    # Match player_out_id -> player name -> player_stats entry for the same match
    result = conn.execute(text("""
        UPDATE substitutions s
        SET team_type = ps.team_type
        FROM player_stats ps, player p
        WHERE s.match_id = ps.match_id
          AND s.player_out_id = p.id
          AND p.name = ps.player_name
          AND s.team_type IS NULL
    """))
    print(f"Updated team_type (via player_stats name match): {result.rowcount} rows")
    
    # For remaining rows, use player's current_team_id vs match home/away
    result = conn.execute(text("""
        UPDATE substitutions s
        SET team_type = 'h'
        FROM matchcalendar m, player p
        WHERE s.match_id = m.id
          AND s.player_out_id = p.id
          AND p.current_team_id = m.home_team_id
          AND s.team_type IS NULL
    """))
    print(f"Updated team_type='h' (via current_team_id): {result.rowcount} rows")
    
    result = conn.execute(text("""
        UPDATE substitutions s
        SET team_type = 'a'
        FROM matchcalendar m, player p
        WHERE s.match_id = m.id
          AND s.player_out_id = p.id
          AND p.current_team_id = m.away_team_id
          AND s.team_type IS NULL
    """))
    print(f"Updated team_type='a' (via current_team_id): {result.rowcount} rows")
    
    conn.commit()
    
    # 4. Verify the migration
    cols = conn.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'substitutions'
        ORDER BY ordinal_position
    """)).fetchall()
    print("\nUpdated substitutions table:")
    for c in cols:
        print(f"  {c[0]} ({c[1]}, nullable={c[2]})")
    
    # Sample data
    samples = conn.execute(text("""
        SELECT id, match_id, player_out, player_in, minute, team_type
        FROM substitutions
        WHERE player_out IS NOT NULL
        ORDER BY match_id DESC, team_type
        LIMIT 20
    """)).fetchall()
    print(f"\nSample data:")
    for s in samples:
        print(f"  {s}")
    
    # NULL counts
    null_out = conn.execute(text("SELECT COUNT(*) FROM substitutions WHERE player_out IS NULL")).scalar()
    null_in = conn.execute(text("SELECT COUNT(*) FROM substitutions WHERE player_in IS NULL")).scalar()
    null_tt = conn.execute(text("SELECT COUNT(*) FROM substitutions WHERE team_type IS NULL")).scalar()
    print(f"\nNULL player_out: {null_out}")
    print(f"NULL player_in: {null_in}")
    print(f"NULL team_type: {null_tt}")
    
    # Team type distribution
    tt_dist = conn.execute(text("""
        SELECT team_type, COUNT(*) FROM substitutions GROUP BY team_type
    """)).fetchall()
    print(f"\nTeam type distribution:")
    for r in tt_dist:
        print(f"  {r[0]}: {r[1]}")
