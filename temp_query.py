import sys
sys.path.append('.')
from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres:postgres@localhost:5432/xpalermostat')
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM player'))
    print('player count:', result.fetchone()[0])
    result = conn.execute(text('SELECT COUNT(*) FROM playermatchstat'))
    print('match stats count:', result.fetchone()[0])
    result = conn.execute(text('SELECT player_id, SUM(goals), SUM(xG) FROM playermatchstat GROUP BY player_id LIMIT 5'))
    for row in result:
        print(row)