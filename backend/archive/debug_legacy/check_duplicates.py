import asyncio
import sys
sys.path.insert(0, '.')
from sqlalchemy import select, func
from app.db.database import AsyncSessionLocal
from app.db.models import Match

async def main():
    async with AsyncSessionLocal() as session:
        # Count duplicates
        stmt = (
            select(Match.understat_id, func.count(Match.understat_id))
            .group_by(Match.understat_id)
            .having(func.count(Match.understat_id) > 1)
        )
        result = await session.execute(stmt)
        duplicates = result.all()
        print(f"Found {len(duplicates)} duplicate understat_ids")
        for understat_id, count in duplicates:
            print(f"  understat_id {understat_id}: {count} rows")
            # Fetch the rows
            rows = await session.execute(select(Match).where(Match.understat_id == understat_id))
            for row in rows.scalars():
                print(f"    id={row.id}, home_team={row.home_team}, away_team={row.away_team}")

if __name__ == "__main__":
    asyncio.run(main())