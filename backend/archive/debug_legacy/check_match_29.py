import asyncio
import sys
sys.path.insert(0, '.')
from app.db.database import AsyncSessionLocal
from app.db.models import Match
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        # Check understat_id 29
        stmt = select(Match).where(Match.understat_id == 29)
        result = await session.execute(stmt)
        match = result.scalar_one_or_none()
        if match:
            print(f"Match found: id={match.id}, home={match.home_team}, away={match.away_team}, home_xg={match.home_xg}, away_xg={match.away_xg}")
        else:
            print("Match with understat_id 29 not found")
        # Also check id 29 (primary key)
        stmt2 = select(Match).where(Match.id == 29)
        result2 = await session.execute(stmt2)
        match2 = result2.scalar_one_or_none()
        if match2:
            print(f"Match with primary key 29: understat_id={match2.understat_id}")
        else:
            print("No match with primary key 29")

if __name__ == "__main__":
    asyncio.run(main())