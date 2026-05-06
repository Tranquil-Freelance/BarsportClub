from sqlalchemy import create_engine, text
DATABASE_URL = 'postgresql+psycopg2://postgres:your_secure_password@127.0.0.1:5432/xpalermostat_db'
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    rows = conn.execute(text('SELECT DISTINCT position FROM rosters ORDER BY position')).fetchall()
    print('Positions:', [r[0] for r in rows])
    
    rows = conn.execute(text('SELECT match_id, COUNT(*) as cnt FROM rosters GROUP BY match_id ORDER BY match_id DESC LIMIT 5')).fetchall()
    print('Sample matches:', rows)
    
    rows = conn.execute(text('SELECT r.match_id, r.player, r.position, r.team_id, r.time FROM rosters r WHERE r.match_id = 30181 ORDER BY r.id')).fetchall()
    print('Match 30181 rosters:')
    for r in rows[:30]:
        print(f'  {r}')
    
    rows = conn.execute(text('SELECT id, home_team_id, away_team_id, home_goals, away_goals FROM matchcalendar WHERE id = 30181')).fetchall()
    print('Match details:', rows)
    
    rows = conn.execute(text('SELECT id, name FROM team WHERE id IN (SELECT home_team_id FROM matchcalendar WHERE id = 30181) OR id IN (SELECT away_team_id FROM matchcalendar WHERE id = 30181)')).fetchall()
    print('Teams:', rows)
