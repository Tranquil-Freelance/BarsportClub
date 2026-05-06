import asyncio
import sys
sys.path.insert(0, '.')
from app.db.database import AsyncSessionLocal
from app.models.football import MatchCalendar
from sqlalchemy import select, func

async def main():
    async with AsyncSessionLocal() as session:
        # total matches
        total = await session.execute(select(func.count(MatchCalendar.id)))
        total_count = total.scalar()
        # matches where round is null
        null_round = await session.execute(select(func.count(MatchCalendar.id)).where(MatchCalendar.round.is_(None)))
        null_count = null_round.scalar()
        print(f"Total MatchCalendar rows: {total_count}")
        print(f"Rows with round NULL: {null_count}")
        if null_count > 0:
            # fetch a few examples
            examples = await session.execute(select(MatchCalendar.id, MatchCalendar.match_datetime, MatchCalendar.home_team_id, MatchCalendar.away_team_id).where(MatchCalendar.round.is_(None)).limit(5))
            for ex in examples:
                print(f"  ID {ex.id} date {ex.match_datetime}")
        else:
            print("All rows have round populated.")

if __name__ == "__main__":
    asyncio.run(main())