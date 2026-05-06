import sys
sys.path.append('.')
from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres:postgres@localhost:5432/xpalermostat')
with engine.connect() as conn:
    # list tables
    result = conn.execute(text("""
        SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;
    """))
    print('Tables:')
    for row in result:
        print(row[0])
    # count rows in each table
    result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
    tables = [r[0] for r in result]
    for table in tables:
        try:
            count = conn.execute(text(f'SELECT COUNT(*) FROM \"{table}\"')).scalar()
            print(f'{table}: {count}')
        except Exception as e:
            print(f'{table}: error {e}')