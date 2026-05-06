#!/usr/bin/env python3
"""
Insert a test match with sample shot data using direct ORM.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.db.models import Match, Shot

async def main():
    async with AsyncSessionLocal() as session:
        match_id = 99999
        home_team = "Palermo"
        away_team = "Como"
        
        # Check if match already exists
        existing = await session.get(Match, match_id)
        if existing:
            print(f"Match {match_id} already exists, deleting old shots...")
            await session.execute(Shot.__table__.delete().where(Shot.match_id == match_id))
            await session.commit()
            # Update match details
            existing.home_team = home_team
            existing.away_team = away_team
        else:
            match = Match(id=match_id, home_team=home_team, away_team=away_team)
            session.add(match)
            await session.commit()
            print(f"Match {match_id} created.")
        
        # Define shots
        shots_data = [
            (match_id, 12, "Matteo Brunori", 0.45, "Goal", "h", 85.2, 45.8),
            (match_id, 34, "Roberto Floriano", 0.12, "Saved", "h", 78.9, 60.3),
            (match_id, 67, "Jacopo Segre", 0.08, "Blocked", "h", 72.1, 30.5),
            (match_id, 23, "Patrick Cutrone", 0.32, "Saved", "a", 15.7, 55.0),
            (match_id, 55, "Luis Malagon", 0.05, "Missed", "a", 22.4, 40.2),
            (match_id, 89, "Gabriele Gori", 0.78, "Goal", "a", 10.5, 48.9),
        ]
        
        shot_objects = []
        for (match_id, minute, player, xG, result, team_type, X, Y) in shots_data:
            shot = Shot(
                match_id=match_id,
                minute=minute,
                player=player,
                xG=xG,
                result=result,
                team_type=team_type,
                X=X,
                Y=Y
            )
            shot_objects.append(shot)
        
        session.add_all(shot_objects)
        await session.commit()
        print(f"Inserted {len(shot_objects)} shots for match {match_id}.")
        
        # Verify counts
        from sqlalchemy import select, func
        stmt = select(func.count(Shot.id)).where(Shot.match_id == match_id)
        result = await session.execute(stmt)
        total = result.scalar()
        print(f"Total shots in DB: {total}")

if __name__ == "__main__":
    asyncio.run(main())