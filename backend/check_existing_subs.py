"""
Check the existing substitutions table in xpalermostat and available player data.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import create_engine, text

URL = "postgresql+psycopg2://postgres:password@localhost:5432/xpalermostat"
engine = create_engine(URL)

with engine.connect() as conn:
    # Check table structure
    cols = conn.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'substitutions'
        ORDER BY ordinal_position
    """)).fetchall()
    print("Existing substitutions table:")
    for c in cols:
        print(f"  {c[0]} ({c[1]}, nullable={c[2]})")
    
    # Check FK references
    fks = conn.execute(text("""
        SELECT
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = 'substitutions'
    """)).fetchall()
    print("\nForeign keys:")
    for fk in fks:
        print(f"  {fk}")
    
    # Check what tables exist for player info
    tables = conn.execute(text("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)).fetchall()
    print(f"\nAll tables ({len(tables)}):")
    for t in tables:
        print(f"  {t[0]}")
    
    # Check player table
    try:
        pcols = conn.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'player'
            ORDER BY ordinal_position
        """)).fetchall()
        print("\nPlayer table columns:")
        for c in pcols:
            print(f"  {c[0]} ({c[1]})")
    except:
        print("\nNo player table found")
    
    # Sample the substitutions data
    samples = conn.execute(text("""
        SELECT * FROM substitutions LIMIT 10
    """)).fetchall()
    print(f"\nSample data ({len(samples)} rows):")
    for s in samples:
        print(f"  {s}")
    
    # Count total
    count = conn.execute(text("SELECT COUNT(*) FROM substitutions")).scalar()
    print(f"\nTotal rows: {count}")
