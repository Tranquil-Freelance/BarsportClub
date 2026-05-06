"""
Check what database the app actually connects to (the DEFAULT from database.py).
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import create_engine, text

# This is what database.py uses as default (no DATABASE_URL in .env)
DEFAULT_URL = "postgresql+psycopg2://postgres:password@localhost:5432/xpalermostat"
print(f"Connecting with default URL: {DEFAULT_URL}")

try:
    engine = create_engine(DEFAULT_URL)
    with engine.connect() as conn:
        # Check current database
        db_name = conn.execute(text("SELECT current_database()")).scalar()
        print(f"Current database: {db_name}")
        
        # Check if substitutions table exists
        rows = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name = 'substitutions'
        """)).fetchall()
        print(f"Substitutions table exists: {len(rows) > 0}")
        
        if rows:
            cols = conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'substitutions'
                ORDER BY ordinal_position
            """)).fetchall()
            print("Columns:")
            for c in cols:
                print(f"  {c[0]} ({c[1]})")
            
            count = conn.execute(text("SELECT COUNT(*) FROM substitutions")).scalar()
            print(f"Row count: {count}")
        else:
            print("Substitutions table does NOT exist in this database!")
except Exception as e:
    print(f"Error connecting with default: {e}")
    print("Trying with explicit password...")

# Also try with the actual password
REAL_URL = "postgresql+psycopg2://postgres:your_secure_password@127.0.0.1:5432/xpalermostat"
print(f"\nTrying with real password: {REAL_URL}")
try:
    engine = create_engine(REAL_URL)
    with engine.connect() as conn:
        db_name = conn.execute(text("SELECT current_database()")).scalar()
        print(f"Current database: {db_name}")
        
        rows = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name = 'substitutions'
        """)).fetchall()
        print(f"Substitutions table exists: {len(rows) > 0}")
        
        if rows:
            cols = conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'substitutions'
                ORDER BY ordinal_position
            """)).fetchall()
            print("Columns:")
            for c in cols:
                print(f"  {c[0]} ({c[1]})")
            
            count = conn.execute(text("SELECT COUNT(*) FROM substitutions")).scalar()
            print(f"Row count: {count}")
except Exception as e:
    print(f"Error: {e}")
