import sys
sys.path.append('.')
from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres:postgres@localhost:5432/xpalermostat')
with engine.connect() as conn:
    # columns
    result = conn.execute(text("""
        SELECT column_name, data_type FROM information_schema.columns 
        WHERE table_name = 'player_registry' ORDER BY ordinal_position;
    """))
    print('Columns:')
    for row in result:
        print(f'  {row[0]} ({row[1]})')
    # sample rows
    result = conn.execute(text("SELECT * FROM player_registry LIMIT 5"))
    for row in result:
        print(row)