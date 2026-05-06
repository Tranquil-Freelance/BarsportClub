import asyncio
import sys
sys.path.insert(0, '.')
from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.db.models import Match, Shot

async def main():
    async with AsyncSessionLocal() as session:
        # Find a match with shots
        stmt = select(Match).where(Match.scraping_status == 'DONE').limit(5)
        result = await session.execute(stmt)
        matches = result.scalars().all()
        print(f"Found {len(matches)} matches with DONE status")
        for match in matches:
            shot_count = await session.execute(select(Shot).where(Shot.match_id == match.id))
            shots = shot_count.scalars().all()
            print(f"Match {match.id} ({match.home_team} vs {match.away_team}) has {len(shots)} shots")
            if shots:
                print(f"  Sample shot xG: {shots[0].xG}, X: {shots[0].X}, Y: {shots[0].Y}")
                break

if __name__ == "__main__":
    asyncio.run(main())