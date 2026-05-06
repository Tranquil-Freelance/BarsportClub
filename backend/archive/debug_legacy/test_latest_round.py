import asyncio
import sys
sys.path.append('.')
from app.db.session import AsyncSessionLocal
from app.models.football import MatchCalendar
from sqlalchemy import select, func, extract

async def test_latest_round():
    async with AsyncSessionLocal() as session:
        # Check if there are matches with round populated
        stmt = select(MatchCalendar.league_id, MatchCalendar.round, func.count(MatchCalendar.id)).group_by(MatchCalendar.league_id, MatchCalendar.round).order_by(MatchCalendar.league_id, MatchCalendar.round)
        result = await session.execute(stmt)
        rows = result.all()
        print("Matches per league per round:")
        for league_id, round_num, count in rows[:10]:
            print(f"  league {league_id} round {round_num}: {count}")
        
        # Determine latest round for Serie A (league_id 1)
        stmt2 = select(MatchCalendar.round).where(MatchCalendar.league_id == 1).where(MatchCalendar.round.isnot(None)).order_by(MatchCalendar.round.desc()).limit(1)
        result2 = await session.execute(stmt2)
        latest = result2.scalar_one_or_none()
        print(f"Latest round for Serie A: {latest}")
        
        # Count matches in that round
        if latest:
            stmt3 = select(func.count(MatchCalendar.id)).where(MatchCalendar.league_id == 1, MatchCalendar.round == latest)
            result3 = await session.execute(stmt3)
            count = result3.scalar()
            print(f"Matches in round {latest}: {count}")
        else:
            print("No rounds found")

if __name__ == "__main__":
    asyncio.run(test_latest_round())