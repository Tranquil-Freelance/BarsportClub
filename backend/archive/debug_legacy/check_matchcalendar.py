import asyncio
import sys
sys.path.insert(0, '.')
from app.db.database import AsyncSessionLocal
from app.models.football import MatchCalendar, Team
from sqlalchemy import select, join

async def main():
    async with AsyncSessionLocal() as session:
        # Query MatchCalendar with joined team names
        stmt = select(
            MatchCalendar.id,
            MatchCalendar.home_team_id,
            MatchCalendar.away_team_id,
            MatchCalendar.home_goals,
            MatchCalendar.away_goals,
            MatchCalendar.is_completed,
            MatchCalendar.match_datetime
        ).where(MatchCalendar.is_completed == True).order_by(MatchCalendar.match_datetime).limit(3)
        result = await session.execute(stmt)
        rows = result.all()
        print(f"Found {len(rows)} completed matches in MatchCalendar:")
        for row in rows:
            # Fetch team names
            home_team = await session.get(Team, row.home_team_id)
            away_team = await session.get(Team, row.away_team_id)
            home_name = home_team.name if home_team else 'Unknown'
            away_name = away_team.name if away_team else 'Unknown'
            print(f"MatchCalendar ID {row.id}: {home_name} {row.home_goals} - {row.away_goals} {away_name} (completed: {row.is_completed})")
        # Count total matches
        stmt2 = select(MatchCalendar).where(MatchCalendar.is_completed == True)
        result2 = await session.execute(stmt2)
        total_completed = len(result2.scalars().all())
        print(f"Total completed matches in MatchCalendar: {total_completed}")

if __name__ == "__main__":
    asyncio.run(main())