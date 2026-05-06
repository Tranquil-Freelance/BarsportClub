import asyncio
import math
from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.models.football import MatchCalendar

async def main():
    async with AsyncSessionLocal() as session:
        stmt = select(MatchCalendar)
        result = await session.execute(stmt)
        for match in result.scalars():
            if match.home_xG is not None and (math.isnan(match.home_xG) or math.isinf(match.home_xG)):
                print(f'Match {match.id} home_xG: {match.home_xG}')
            if match.away_xG is not None and (math.isnan(match.away_xG) or math.isinf(match.away_xG)):
                print(f'Match {match.id} away_xG: {match.away_xG}')
        # also check other float columns if any
        print("Scan complete.")

if __name__ == "__main__":
    asyncio.run(main())