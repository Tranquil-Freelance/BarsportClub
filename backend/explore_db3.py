from sqlalchemy import create_engine, inspect, text
DATABASE_URL = 'postgresql+psycopg2://postgres:your_secure_password@127.0.0.1:5432/xpalermostat_db'
engine = create_engine(DATABASE_URL)
insp = inspect(engine)
print('All tables:', insp.get_table_names())

with engine.connect() as conn:
    # Check player_stats for a specific match
    rows = conn.execute(text("""
        SELECT ps.match_id, COUNT(*) as cnt 
        FROM player_stats ps 
        JOIN matchcalendar m ON m.id = ps.match_id
        WHERE m.is_completed = true
        GROUP BY ps.match_id 
        ORDER BY ps.match_id DESC 
        LIMIT 5
    """)).fetchall()
    print('Matches with player_stats:', rows)
    
    if rows:
        mid = rows[0][0]
        print(f'\n--- player_stats for match {mid} ---')
        rows = conn.execute(text("""
            SELECT ps.player_name, ps.position, ps.team_type, ps.time, ps.team_name 
            FROM player_stats ps WHERE ps.match_id = :mid 
            ORDER BY ps.team_type, ps.time DESC
        """), {"mid": mid}).fetchall()
        for r in rows:
            print(f'  {r}')
        
        rows = conn.execute(text("""
            SELECT id, home_team_id, away_team_id, home_goals, away_goals 
            FROM matchcalendar WHERE id = :mid
        """), {"mid": mid}).fetchall()
        print(f'\nMatch details:', rows)
        if rows:
            htid, atid = rows[0][1], rows[0][2]
            rows = conn.execute(text("""
                SELECT id, name FROM team WHERE id IN (:ht, :at)
            """), {"ht": htid, "at": atid}).fetchall()
            print('Teams:', rows)
    
    # Check what recent match IDs are in matchcalendar
    print('\n--- Recent completed matches ---')
    rows = conn.execute(text("""
        SELECT id, home_team_id, away_team_id, match_datetime, is_completed 
        FROM matchcalendar 
        WHERE is_completed = true 
        ORDER BY id DESC LIMIT 5
    """)).fetchall()
    for r in rows:
        print(f'  {r}')
