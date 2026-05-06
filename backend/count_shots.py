import asyncio
import sys
sys.path.insert(0, '.')
from app.db.database import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as session:
        # Count all shots
        result = await session.execute(text("SELECT COUNT(*) FROM shots"))
        total = result.scalar()
        print(f"Total shots: {total}")
        # Count shots for match 30116
        result = await session.execute(text("SELECT COUNT(*) FROM shots WHERE match_id = 30116"))
        match_shots = result.scalar()
        print(f"Shots for match 30116: {match_shots}")

if __name__ == "__main__":
    asyncio.run(main())