import asyncio
import traceback
from app.db.database import AsyncSessionLocal
from app.api.crud import get_matches

async def main():
    async with AsyncSessionLocal() as session:
        try:
            print("Calling get_matches...")
            matches = await get_matches(session)
            print(f"Success! Retrieved {len(matches)} matches")
            if matches:
                print("First match:", matches[0])
        except Exception as e:
            print("Error:", e)
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())