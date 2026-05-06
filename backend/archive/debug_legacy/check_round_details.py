import asyncio
import sys
sys.path.insert(0, '.')
from app.db.database import AsyncSessionLocal
from app.models.football import MatchCalendar
from sqlalchemy import select, func

async def main():
    async with AsyncSessionLocal() as session:
        # matches where round is null
        stmt = select(MatchCalendar.id, MatchCalendar.match_datetime, MatchCalendar.league_id, MatchCalendar.home_team_id, MatchCalendar.away_team_id).where(MatchCalendar.round.is_(None)).limit(10)
        result = await session.execute(stmt)
        rows = result.all()
        print(f"Found {len(rows)} null round matches:")
        for r in rows:
            print(f"  ID {r.id} league_id {r.league_id} date {r.match_datetime}")
        # also count per league
        stmt2 = select(MatchCalendar.league_id, func.count(MatchCalendar.id)).where(MatchCalendar.round.is_(None)).group_by(MatchCalendar.league_id)
        result2 = await session.execute(stmt2)
        for league_id, cnt in result2:
            print(f"League {league_id}: {cnt} null rounds")

if __name__ == "__main__":
    asyncio.run(main())