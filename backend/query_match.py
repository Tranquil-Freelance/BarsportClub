import asyncio
from app.db.session import AsyncSessionLocal
from app.models.football import MatchCalendar, Team
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        # Find Palermo team
        stmt = select(Team).where(Team.name == "Palermo")
        result = await session.execute(stmt)
        palermo = result.scalar_one_or_none()
        if palermo:
            print(f"Palermo id: {palermo.id}")
            # Find matches involving Palermo that are completed
            stmt = select(MatchCalendar).where(
                (MatchCalendar.home_team_id == palermo.id) | (MatchCalendar.away_team_id == palermo.id)
            ).where(MatchCalendar.is_completed == True).order_by(MatchCalendar.match_datetime.desc())
            result = await session.execute(stmt)
            matches = result.scalars().all()
            for m in matches:
                print(f"Match id: {m.id}, date: {m.match_datetime}, home: {m.home_team_id}, away: {m.away_team_id}, is_scraped: {m.is_scraped}")
        else:
            print("Palermo not found")

if __name__ == "__main__":
    asyncio.run(main())