import asyncio
import math
from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.models.football import MatchCalendar

async def main():
    async with AsyncSessionLocal() as session:
        stmt = select(MatchCalendar).limit(50)
        result = await session.execute(stmt)
        matches = result.scalars().all()
        for match in matches:
            print(f"MatchCalendar {match.id}: home_xG={match.home_xG}, away_xG={match.away_xG}")
            if match.home_xG is not None:
                try:
                    if math.isnan(match.home_xG):
                        print(f"   home_xG is NaN!")
                except TypeError:
                    print(f"   home_xG is not float")
            if match.away_xG is not None:
                try:
                    if math.isnan(match.away_xG):
                        print(f"   away_xG is NaN!")
                except TypeError:
                    print(f"   away_xG is not float")

if __name__ == "__main__":
    asyncio.run(main())