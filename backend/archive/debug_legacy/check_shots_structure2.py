import asyncio
import sys
sys.path.insert(0, '.')
from sqlalchemy import text
from app.db.database import AsyncSessionLocal
from app.scraper.understat_parser import get_match_shots
from app.scraper.understat_engine import get_understat_match_shots

async def check_db():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text('SELECT id FROM matches LIMIT 1'))
        row = result.fetchone()
        if row:
            match_id = row[0]
            print(f"Found match ID: {match_id}")
            # Fetch shots via parser
            try:
                shots = get_match_shots(match_id)
                print(f"Type of shots: {type(shots)}")
                if isinstance(shots, dict):
                    print(f"Keys: {shots.keys()}")
                    if 'h' in shots and 'a' in shots:
                        print(f"Home shots count: {len(shots['h'])}")
                        print(f"Away shots count: {len(shots['a'])}")
                        if shots['h']:
                            print(f"Sample shot keys: {shots['h'][0].keys()}")
                elif isinstance(shots, list):
                    print(f"List length: {len(shots)}")
                    if shots:
                        print(f"Sample shot keys: {shots[0].keys()}")
            except Exception as e:
                print(f"Error fetching shots: {e}")
        else:
            print("No matches in database")

if __name__ == '__main__':
    asyncio.run(check_db())