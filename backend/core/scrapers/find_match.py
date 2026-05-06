import asyncio
import sys
sys.path.append('.')
from app.db.session import AsyncSessionLocal
from app.models.football import Match

async def main():
    async with AsyncSessionLocal() as session:
        # Query for Udinese vs Juventus
        from sqlalchemy import select
        stmt = select(Match).where(
            (Match.home_team.ilike('%Udinese%')) | (Match.away_team.ilike('%Udinese%'))
        )
        result = await session.execute(stmt)
        matches = result.scalars().all()
        for m in matches:
            print(f"Match ID {m.id}: {m.home_team} vs {m.away_team} (understat {m.understat_id})")
        
        # Also search for Juventus vs Udinese
        stmt2 = select(Match).where(
            (Match.home_team.ilike('%Juventus%')) | (Match.away_team.ilike('%Juventus%'))
        )
        result2 = await session.execute(stmt2)
        matches2 = result2.scalars().all()
        for m in matches2:
            print(f"Match ID {m.id}: {m.home_team} vs {m.away_team} (understat {m.understat_id})")
        
        await session.close()

if __name__ == "__main__":
    asyncio.run(main())