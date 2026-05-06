from sqlalchemy import create_engine, inspect, text
DATABASE_URL = 'postgresql+psycopg2://postgres:your_secure_password@127.0.0.1:5432/xpalermostat_db'
engine = create_engine(DATABASE_URL)
insp = inspect(engine)
cols = [c['name'] for c in insp.get_columns('substitutions')]
print('Subs table columns:', cols)
with engine.connect() as conn:
    rows = conn.execute(text('SELECT * FROM substitutions LIMIT 3')).fetchall()
    for r in rows:
        print(r)
