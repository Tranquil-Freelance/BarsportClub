import asyncio
import math
from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.models.football import MatchCalendar

async def clean():
    async with AsyncSessionLocal() as session:
        stmt = select(MatchCalendar)
        result = await session.execute(stmt)
        matches = result.scalars().all()
        updated = 0
        for match in matches:
            changed = False
            if match.home_xG is not None and (math.isnan(match.home_xG) or math.isinf(match.home_xG)):
                match.home_xG = None
                changed = True
            if match.away_xG is not None and (math.isnan(match.away_xG) or math.isinf(match.away_xG)):
                match.away_xG = None
                changed = True
            if changed:
                updated += 1
        await session.commit()
        print(f"Updated {updated} matches with NaN/inf values.")
        print("Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(clean())