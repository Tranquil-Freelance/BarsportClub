"""
Check the actual schema of the substitutions table via information_schema.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import create_engine, text

engine = create_engine('postgresql+psycopg2://postgres:your_secure_password@127.0.0.1:5432/xpalermostat_db')
with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'substitutions'
        ORDER BY ordinal_position
    """)).fetchall()
    print('Columns in substitutions table:')
    for r in rows:
        print(f'  {r[0]} ({r[1]}, nullable={r[2]})')
    
    rows2 = conn.execute(text("""
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_name LIKE '%substit%'
    """)).fetchall()
    print(f'\nTables matching %substit%:')
    for r in rows2:
        print(f'  {r[0]}.{r[1]}')

    count = conn.execute(text("SELECT COUNT(*) FROM substitutions")).scalar()
    print(f'\nTotal rows: {count}')
