import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv('../.env')  # load from parent directory

async def main():
    conn = await asyncpg.connect(
        host=os.getenv('POSTGRES_SERVER', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'your_secure_password'),
        database=os.getenv('POSTGRES_DB', 'xpalermostat')
    )
    # query shots count per match
    rows = await conn.fetch('SELECT match_id, COUNT(*) as shot_count FROM shots GROUP BY match_id ORDER BY match_id')
    print(f"Found {len(rows)} matches with shots:")
    for row in rows:
        print(f"Match ID: {row['match_id']}, shots: {row['shot_count']}")
    # also check if match 27362 exists in matches table
    match = await conn.fetchrow('SELECT * FROM matches WHERE id = $1', 27362)
    if match:
        print(f"Match 27362 exists: {match['home_team']} vs {match['away_team']}")
    else:
        print("Match 27362 not in matches table.")
    await conn.close()

asyncio.run(main())