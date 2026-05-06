import sys
sys.path.append('.')
from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres:postgres@localhost:5432/xpalermostat')
with engine.connect() as conn:
    # Get column info
    result = conn.execute(text("""
        SELECT column_name, data_type FROM information_schema.columns 
        WHERE table_name = 'seriea_match_players' ORDER BY ordinal_position;
    """))
    print('Columns:')
    for row in result:
        print(f'  {row[0]} ({row[1]})')
    # Sample row
    result = conn.execute(text("SELECT * FROM seriea_match_players LIMIT 1"))
    row = result.fetchone()
    if row:
        print('\nSample row:')
        for i, col in enumerate(result.keys()):
            print(f'  {col}: {row[i]}')