import asyncio
import sys
sys.path.insert(0, '.')
from app.db.database import AsyncSessionLocal
from app.db.models import Match
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        stmt = select(Match).where(Match.status == 'FT').order_by(Match.id).limit(3)
        result = await session.execute(stmt)
        matches = result.scalars().all()
        print(f"Found {len(matches)} matches with status 'FT':")
        for match in matches:
            print(f"ID {match.id}: {match.home_team} {match.home_score} - {match.away_score} {match.away_team} (understat_id={match.understat_id})")
        # Also check for any matches with home_team = 'Home' or 'Away'
        stmt2 = select(Match).where(Match.home_team.in_(['Home', 'Away'])).limit(5)
        result2 = await session.execute(stmt2)
        placeholder_matches = result2.scalars().all()
        print(f"\nPlaceholder matches (Home/Away): {len(placeholder_matches)}")
        for m in placeholder_matches:
            print(f"ID {m.id}: {m.home_team} vs {m.away_team}")

if __name__ == "__main__":
    asyncio.run(main())