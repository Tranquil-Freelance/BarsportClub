import asyncio
import sys
sys.path.insert(0, '.')

from app.db.session import AsyncSessionLocal
from app.api.crud import get_matches

async def test():
    async with AsyncSessionLocal() as session:
        try:
            matches = await get_matches(session, round_number=29)
            print(f'Total matches round 29: {len(matches)}')
            for m in matches[:5]:
                print(m)
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test())