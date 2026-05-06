import asyncio
import sys
sys.path.insert(0, '.')

from app.db.session import AsyncSessionLocal
from app.api.crud import get_matches

async def validate():
    async with AsyncSessionLocal() as session:
        matches = await get_matches(session)
        print(f'Total matches: {len(matches)}')
        # Check first few
        for i, m in enumerate(matches[:5]):
            print(f'Match {i}: {m}')
            required_keys = ['id', 'date', 'home_team', 'away_team', 'home_score', 'away_score', 'home_xg', 'away_xg', 'round']
            for key in required_keys:
                if key not in m:
                    print(f'  Missing key: {key}')
                else:
                    val = m[key]
                    if val is None:
                        print(f'  {key} is None')
                    elif isinstance(val, float) and (val != val):  # NaN
                        print(f'  {key} is NaN')
        # Check JSON serializable
        import json
        try:
            json.dumps(matches)
            print('JSON serializable: OK')
        except Exception as e:
            print(f'JSON serialization error: {e}')
            raise

if __name__ == '__main__':
    asyncio.run(validate())