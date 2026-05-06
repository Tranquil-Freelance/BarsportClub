import asyncio
import sys
sys.path.insert(0, '.')
import math
from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.db.models import Shot

async def main():
    async with AsyncSessionLocal() as session:
        stmt = select(Shot).limit(100)
        result = await session.execute(stmt)
        shots = result.scalars().all()
        nan_shots = []
        for shot in shots:
            if (shot.xG is not None and math.isnan(shot.xG)) or (shot.X is not None and math.isnan(shot.X)) or (shot.Y is not None and math.isnan(shot.Y)):
                nan_shots.append(shot)
        print(f"Found {len(nan_shots)} shots with NaN values out of {len(shots)} total")
        for shot in nan_shots[:5]:
            print(f"  Shot id={shot.id}, match_id={shot.match_id}, xG={shot.xG}, X={shot.X}, Y={shot.Y}")

if __name__ == "__main__":
    asyncio.run(main())