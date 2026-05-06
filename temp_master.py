import sys
sys.path.append('.')
from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres:postgres@localhost:5432/xpalermostat')
with engine.connect() as conn:
    # columns
    result = conn.execute(text("""
        SELECT column_name, data_type FROM information_schema.columns 
        WHERE table_name = 'master_europe_players' ORDER BY ordinal_position;
    """))
    print('Columns:')
    for row in result:
        print(f'  {row[0]} ({row[1]})')
    # distinct season
    result = conn.execute(text("SELECT DISTINCT season FROM master_europe_players ORDER BY season DESC LIMIT 10"))
    print('\nSeasons:')
    for row in result:
        print(row[0])
    # count rows
    result = conn.execute(text("SELECT COUNT(*) FROM master_europe_players"))
    print('Total rows:', result.fetchone()[0])