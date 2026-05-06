#!/usr/bin/env python3
"""
Insert a test match for Palermo (Serie B 25/26) into the database.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.football import League, Team, MatchCalendar

async def ensure_league_exists(session: AsyncSession) -> int:
    LEAGUE_NAME = "Serie B"
    stmt = select(League).where(League.name == LEAGUE_NAME)
    result = await session.execute(stmt)
    league = result.scalar_one_or_none()
    if league:
        print(f"League '{LEAGUE_NAME}' already exists with id={league.id}")
        return league.id
    # Create new league record
    new_league = League(
        name=LEAGUE_NAME,
        understat_slug="ITA-Serie B",  # stored in understat_slug column for compatibility
    )
    session.add(new_league)
    await session.commit()
    print(f"Created new league '{LEAGUE_NAME}' with id={new_league.id}")
    return new_league.id

async def main():
    async with AsyncSessionLocal() as session:
        # Ensure Serie B league exists
        league_id = await ensure_league_exists(session)
        print(f"League ID: {league_id}")
        
        # Create Palermo team if not exists
        palermo = await session.execute(select(Team).where(Team.name == "Palermo"))
        palermo = palermo.scalar_one_or_none()
        if not palermo:
            palermo = Team(name="Palermo", league_id=league_id)
            session.add(palermo)
            await session.commit()
            await session.refresh(palermo)
            print(f"Created Palermo team with id={palermo.id}")
        else:
            print(f"Palermo team already exists with id={palermo.id}")
        
        # Create opponent team (e.g., "Como")
        como = await session.execute(select(Team).where(Team.name == "Como"))
        como = como.scalar_one_or_none()
        if not como:
            como = Team(name="Como", league_id=league_id)
            session.add(como)
            await session.commit()
            await session.refresh(como)
            print(f"Created Como team with id={como.id}")
        else:
            print(f"Como team already exists with id={como.id}")
        
        # Create a match (most recent)
        match = MatchCalendar(
            league_id=league_id,
            home_team_id=palermo.id,
            away_team_id=como.id,
            match_datetime=datetime(2026, 1, 22, 20, 45, tzinfo=timezone.utc),
            is_completed=True,
            is_scraped=False,
            home_goals=2,
            away_goals=1,
            home_xG=1.8,
            away_xG=0.9,
        )
        session.add(match)
        await session.commit()
        await session.refresh(match)
        print(f"Created match with id={match.id}, datetime={match.match_datetime}")
        
        # Verify match exists
        stmt = select(MatchCalendar).where(MatchCalendar.home_team_id == palermo.id)
        result = await session.execute(stmt)
        matches = result.scalars().all()
        print(f"Total matches for Palermo: {len(matches)}")

if __name__ == "__main__":
    asyncio.run(main())