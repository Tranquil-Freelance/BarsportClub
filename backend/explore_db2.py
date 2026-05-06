from sqlalchemy import create_engine, text
DATABASE_URL = 'postgresql+psycopg2://postgres:your_secure_password@127.0.0.1:5432/xpalermostat_db'
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    # Find matches that have rosters data
    rows = conn.execute(text("""
        SELECT r.match_id, COUNT(*) as cnt 
        FROM rosters r 
        JOIN matchcalendar m ON m.id = r.match_id
        WHERE m.is_completed = true
        GROUP BY r.match_id 
        ORDER BY r.match_id DESC 
        LIMIT 10
    """)).fetchall()
    print('Matches with rosters:', rows)
    
    if rows:
        mid = rows[0][0]
        print(f'\n--- Rosters for match {mid} ---')
        rows = conn.execute(text("""
            SELECT r.player, r.position, r.team_id, r.time, r.goals, r.assists, r.xG, r.xA 
            FROM rosters r WHERE r.match_id = :mid ORDER BY r.team_id, r.id
        """), {"mid": mid}).fetchall()
        for r in rows[:40]:
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
    
    # Check player_stats table
    print('\n--- player_stats sample ---')
    rows = conn.execute(text("""
        SELECT player_name, position, team_type, time, team_name 
        FROM player_stats LIMIT 10
    """)).fetchall()
    for r in rows:
        print(f'  {r}')
    
    # Check positions in player_stats
    print('\n--- positions in player_stats ---')
    rows = conn.execute(text("""
        SELECT DISTINCT position FROM player_stats ORDER BY position
    """)).fetchall()
    print('Positions:', [r[0] for r in rows])
