import asyncio
import sys
sys.path.append('.')
try:
    from app.db.session import AsyncSessionLocal
    from app.api.crud import get_standings
    print('Imports successful')
except Exception as e:
    print('Import error:', e)
    import traceback
    traceback.print_exc()
    sys.exit(1)

async def test():
    try:
        async with AsyncSessionLocal() as db:
            print('Fetching standings...')
            standings = await get_standings(db)
            print('Standings count:', len(standings))
            if standings:
                first = standings[0]
                print('Keys:', list(first.keys()))
                for key, val in first.items():
                    print(f'{key}: {val}')
            else:
                print('No standings')
    except Exception as e:
        print('Error during test:', e)
        import traceback
        traceback.print_exc()

asyncio.run(test())