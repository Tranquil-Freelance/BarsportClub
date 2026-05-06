import asyncio
import math
from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.db.models import Match

async def main():
    async with AsyncSessionLocal() as session:
        stmt = select(Match).order_by(Match.id.desc()).limit(20)
        result = await session.execute(stmt)
        matches = result.scalars().all()
        for match in matches:
            print(f"Match {match.id}: home_xg={match.home_xg}, away_xg={match.away_xg}")
            if match.home_xg is not None:
                print(f"  home_xg is not None, isnan={math.isnan(match.home_xg)}")
            if match.away_xg is not None:
                print(f"  away_xg is not None, isnan={math.isnan(match.away_xg)}")

if __name__ == "__main__":
    asyncio.run(main())