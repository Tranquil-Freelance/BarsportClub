import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv('../.env')

async def main():
    conn = await asyncpg.connect(
        host=os.getenv('POSTGRES_SERVER', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'your_secure_password'),
        database='xpalermostat_db'
    )
    # First, check if match 27362 exists in matches table
    match = await conn.fetchrow('SELECT * FROM matches WHERE id = $1', 27362)
    if match:
        print(f"Match 27362 found: home_team={match['home_team']}, away_team={match['away_team']}")
        # check columns
        columns = list(match.keys())
        print(f"Columns in matches: {columns}")
        # if title column exists, use it; else use home_team vs away_team
        if 'title' in columns:
            title = match['title']
        else:
            title = f"{match['home_team']} vs {match['away_team']}"
        print(f"Match title: {title}")
    else:
        print("Match 27362 not found in matches table.")
        title = None
    
    # Count shots for match 27362
    shots_count = await conn.fetchval('SELECT COUNT(*) FROM shots WHERE match_id = $1', 27362)
    print(f"Shots count for match 27362: {shots_count}")
    
    # Also run the user's exact query (might fail if title column missing)
    try:
        rows = await conn.fetch('''
            SELECT m.title, COUNT(s.id) 
            FROM matches m 
            JOIN shots s ON m.id = s.match_id 
            WHERE m.id = 27362 
            GROUP BY m.title
        ''')
        for row in rows:
            print(f"Query result: title={row['title']}, shot_count={row['count']}")
    except Exception as e:
        print(f"User query failed (likely missing title column): {e}")
        # alternative query using home_team and away_team
        rows = await conn.fetch('''
            SELECT m.home_team, m.away_team, COUNT(s.id) as shot_count
            FROM matches m 
            JOIN shots s ON m.id = s.match_id 
            WHERE m.id = 27362 
            GROUP BY m.home_team, m.away_team
        ''')
        for row in rows:
            print(f"Alternative result: {row['home_team']} vs {row['away_team']}, shots={row['shot_count']}")
    
    await conn.close()

asyncio.run(main())