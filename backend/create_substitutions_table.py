"""
Create the substitutions table in the database.
Schema: match_id, player_out (player_name), player_in (player_name), minute, team_id, team_type
"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = 'postgresql+psycopg2://postgres:your_secure_password@127.0.0.1:5432/xpalermostat_db'

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    # Create substitutions table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS substitutions (
            id SERIAL PRIMARY KEY,
            match_id BIGINT NOT NULL REFERENCES matchcalendar(id) ON DELETE CASCADE,
            player_out VARCHAR(255) NOT NULL,
            player_in VARCHAR(255) NOT NULL,
            minute INTEGER NOT NULL,
            team_id INTEGER REFERENCES team(id),
            team_type VARCHAR(5) DEFAULT 'h',
            UNIQUE(match_id, player_out, player_in, minute)
        )
    """))
    
    # Create index for faster lookups
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_substitutions_match 
        ON substitutions(match_id)
    """))
    
    conn.commit()
    print("OK - substitutions table created")

    # Now populate it by inferring from player_stats
    matches = conn.execute(text("""
        SELECT DISTINCT ps.match_id 
        FROM player_stats ps 
        JOIN matchcalendar m ON m.id = ps.match_id
        WHERE m.is_completed = true
        AND ps.match_id NOT IN (SELECT DISTINCT match_id FROM substitutions)
        ORDER BY ps.match_id
    """)).fetchall()
    
    print(f"Found {len(matches)} matches to process")
    
    total_inserted = 0
    for (match_id,) in matches:
        for team_type in ['h', 'a']:
            # Get starters (not Sub) ordered by time ASC (least minutes first = subbed out earliest)
            starters = conn.execute(text("""
                SELECT player_name, position, time 
                FROM player_stats 
                WHERE match_id = :mid AND team_type = :tt AND position != 'Sub'
                ORDER BY time ASC
            """), {"mid": match_id, "tt": team_type}).fetchall()
            
            # Get subs ordered by time DESC (most minutes first = came on earliest)
            subs = conn.execute(text("""
                SELECT player_name, position, time 
                FROM player_stats 
                WHERE match_id = :mid AND team_type = :tt AND position = 'Sub'
                ORDER BY time DESC
            """), {"mid": match_id, "tt": team_type}).fetchall()
            
            if not starters or not subs:
                continue
            
            # Get team_id for this team in this match
            team_row = conn.execute(text("""
                SELECT DISTINCT t.id FROM team t
                JOIN matchcalendar m ON (m.home_team_id = t.id AND :tt = 'h') OR (m.away_team_id = t.id AND :tt = 'a')
                WHERE m.id = :mid
            """), {"mid": match_id, "tt": team_type}).fetchone()
            
            team_id = team_row[0] if team_row else None
            
            # Pair: each starter with time < 90 gets matched with a sub
            starters_below_90 = [s for s in starters if s[2] < 90]
            
            for i, starter in enumerate(starters_below_90):
                if i >= len(subs):
                    break
                sub = subs[i]
                
                # Substitution minute = starter's minutes (when they left the pitch)
                sub_minute = starter[2]
                
                try:
                    conn.execute(text("""
                        INSERT INTO substitutions (match_id, player_out, player_in, minute, team_id, team_type)
                        VALUES (:mid, :pout, :pin, :min, :tid, :tt)
                        ON CONFLICT (match_id, player_out, player_in, minute) DO NOTHING
                    """), {
                        "mid": match_id,
                        "pout": starter[0],
                        "pin": sub[0],
                        "min": sub_minute,
                        "tid": team_id,
                        "tt": team_type
                    })
                    total_inserted += 1
                except Exception as e:
                    print(f"  Error inserting sub for match {match_id}: {e}")
    
    conn.commit()
    print(f"OK - Inserted {total_inserted} substitution events")
    
    # Verify
    count = conn.execute(text("SELECT COUNT(*) FROM substitutions")).scalar()
    print(f"Total substitutions in DB: {count}")
    
    # Show sample
    rows = conn.execute(text("""
        SELECT s.match_id, s.player_out, s.player_in, s.minute, s.team_type
        FROM substitutions s
        ORDER BY s.match_id DESC, s.team_type
        LIMIT 20
    """)).fetchall()
    print("\nSample substitutions:")
    for r in rows:
        print(f"  Match {r[0]}: {r[1]} -> {r[2]} @ {r[3]}' ({r[4]})")
