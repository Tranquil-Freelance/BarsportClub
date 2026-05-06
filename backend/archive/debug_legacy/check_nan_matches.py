import asyncio
import sys
sys.path.insert(0, '.')
from app.db.database import AsyncSessionLocal
from app.db.models import Match
from sqlalchemy import select
import math

async def main():
    async with AsyncSessionLocal() as session:
        stmt = select(Match)
        result = await session.execute(stmt)
        matches = result.scalars().all()
        print(f"Total matches: {len(matches)}")
        nan_matches = []
        for m in matches:
            if (m.home_xg is not None and math.isnan(m.home_xg)) or (m.away_xg is not None and math.isnan(m.away_xg)):
                nan_matches.append(m)
                print(f"Match ID {m.id} understat_id {m.understat_id}: home_xg={m.home_xg}, away_xg={m.away_xg}")
        if not nan_matches:
            print("No NaN values found.")

if __name__ == "__main__":
    asyncio.run(main())