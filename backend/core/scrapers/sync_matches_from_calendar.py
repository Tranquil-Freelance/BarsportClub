import asyncio
import sys
sys.path.insert(0, '.')
from app.db.database import AsyncSessionLocal
from app.models.football import MatchCalendar, Team
from app.db.models import Match
from sqlalchemy import select, update, and_

async def main():
    async with AsyncSessionLocal() as session:
        # Fetch all MatchCalendar entries with team names
        stmt = select(
            MatchCalendar.id,
            MatchCalendar.home_team_id,
            MatchCalendar.away_team_id,
            MatchCalendar.home_goals,
            MatchCalendar.away_goals,
            MatchCalendar.is_completed,
            MatchCalendar.match_datetime
        )
        result = await session.execute(stmt)
        calendars = result.all()
        print(f"Processing {len(calendars)} MatchCalendar entries")
        
        updated = 0
        created = 0
        for cal in calendars:
            # Get team names
            home_team = await session.get(Team, cal.home_team_id)
            away_team = await session.get(Team, cal.away_team_id)
            if not home_team or not away_team:
                continue
            home_name = home_team.name
            away_name = away_team.name
            
            # Determine status
            status = 'FT' if cal.is_completed else 'programmato'
            
            # Check if match already exists in matches table (by id)
            existing = await session.get(Match, cal.id)
            if existing:
                # Update
                existing.home_team = home_name
                existing.away_team = away_name
                existing.home_score = cal.home_goals
                existing.away_score = cal.away_goals
                existing.status = status
                existing.start_time = cal.match_datetime
                existing.understat_id = cal.id
                updated += 1
            else:
                # Insert new match
                match = Match(
                    id=cal.id,
                    home_team=home_name,
                    away_team=away_name,
                    home_score=cal.home_goals,
                    away_score=cal.away_goals,
                    status=status,
                    start_time=cal.match_datetime,
                    understat_id=cal.id,
                    scraping_status='PENDING'
                )
                session.add(match)
                created += 1
        
        await session.commit()
        print(f"Updated {updated} matches, created {created} new matches.")
        
        # Verify
        stmt2 = select(Match).where(Match.home_team.in_(['Home', 'Away'])).limit(5)
        result2 = await session.execute(stmt2)
        placeholder_matches = result2.scalars().all()
        print(f"Remaining placeholder matches (Home/Away): {len(placeholder_matches)}")

if __name__ == "__main__":
    asyncio.run(main())