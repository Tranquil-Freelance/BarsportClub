#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine, inspect, text

DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/xpalermostat_db'
engine = create_engine(DATABASE_URL)

inspector = inspect(engine)
# Get columns of matches table
try:
    columns = inspector.get_columns('matches')
    print('Columns in matches table:')
    for col in columns:
        print(f"  - {col['name']} ({col['type']})")
except Exception as e:
    print(f"Error inspecting matches table: {e}")
    # maybe table doesn't exist
    tables = inspector.get_table_names()
    print(f"Available tables: {tables}")

# Get row count
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM matches'))
    count = result.scalar()
    print(f'Row count in matches: {count}')
    if count == 0:
        print('Table is empty.')
    else:
        # Fetch a sample row
        sample = conn.execute(text('SELECT * FROM matches LIMIT 1')).fetchone()
        print('Sample row:', sample)

engine.dispose()