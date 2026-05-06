#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from sqlalchemy import create_engine, inspect

DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/xpalermostat_db'
engine = create_engine(DATABASE_URL)
inspector = inspect(engine)
try:
    columns = inspector.get_columns('shots')
    print('Columns in shots table:')
    for col in columns:
        print(f"  - {col['name']} ({col['type']})")
except Exception as e:
    print(f"Error inspecting shots table: {e}")
    tables = inspector.get_table_names()
    print(f"Available tables: {tables}")

engine.dispose()