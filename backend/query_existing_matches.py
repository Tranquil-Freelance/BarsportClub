#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, '.')

from app.db.session import AsyncSessionLocal
from app.models.football import Team, MatchCalendar

async def main():
    async with AsyncSessionLocal() as session:
        # Find Como team
        result = await session.execute(
            Team.__table__.select().where(Team.name.ilike('%como%'))
        )
        como = result.fetchone()
        if not como:
            print("Como team not found in database")
            # maybe team not inserted; we can insert later
            return
        team_id = como[0]  # first column is id
        team_name = como[1]
        print(f"Found team: {team_name} (id={team_id})")
        # Find matches where Como is home or away
        from sqlalchemy import or_
        result = await session.execute(
            MatchCalendar.__table__.select().where(
                or_(
                    MatchCalendar.home_team_id == team_id,
                    MatchCalendar.away_team_id == team_id
                )
            )
        )
        matches = result.fetchall()
        print(f"Found {len(matches)} matches for Como:")
        for match in matches:
            # match columns: id, league_id, home_team_id, away_team_id, match_datetime, is_completed, is_scraped, home_goals, away_goals, home_xG, away_xG
            print(f"  Match ID: {match[0]}, home_team_id: {match[2]}, away_team_id: {match[3]}, datetime: {match[4]}")
        # Also get team names for each match
        # We'll do a join later if needed
        if len(matches) == 0:
            print("No existing matches. Need to scrape.")

if __name__ == '__main__':
    asyncio.run(main())