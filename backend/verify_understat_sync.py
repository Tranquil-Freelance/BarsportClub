#!/usr/bin/env python3
"""
Verify that Understat sync script correctly inserted/updated Team and TeamSeasonStat records.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import AsyncSessionLocal
from app.models.football import Team, TeamSeasonStat, League
from sqlalchemy import select, func

async def verify():
    async with AsyncSessionLocal() as session:
        # Count teams
        team_count = await session.scalar(select(func.count(Team.id)))
        print(f"Total teams in database: {team_count}")
        
        # Count TeamSeasonStat for season 2025
        stat_count = await session.scalar(
            select(func.count(TeamSeasonStat.id)).where(TeamSeasonStat.season == "2025")
        )
        print(f"TeamSeasonStat records for season 2025: {stat_count}")
        
        # Show a few sample records
        stats = await session.execute(
            select(TeamSeasonStat, Team.name)
            .join(Team, TeamSeasonStat.team_id == Team.id)
            .where(TeamSeasonStat.season == "2025")
            .order_by(TeamSeasonStat.points.desc())
            .limit(5)
        )
        print("\nTop 5 teams by points:")
        for stat, team_name in stats:
            print(f"  {team_name}: {stat.wins}W {stat.draws}D {stat.losses}L, "
                  f"{stat.goals_for}GF {stat.goals_against}GA, "
                  f"{stat.points} pts, xG {stat.xG_for:.2f}")
        
        # Verify that each team has a record
        missing = await session.execute(
            select(Team.id, Team.name)
            .outerjoin(
                TeamSeasonStat,
                (TeamSeasonStat.team_id == Team.id) & (TeamSeasonStat.season == "2025")
            )
            .where(TeamSeasonStat.id.is_(None))
        )
        missing_rows = missing.fetchall()
        if missing_rows:
            print(f"\nWARNING: {len(missing_rows)} teams missing season 2025 stats:")
            for tid, name in missing_rows:
                print(f"  {name} (ID {tid})")
        else:
            print("\nAll teams have season 2025 stats.")
        
        # Check league understat_slug
        league = await session.scalar(
            select(League).where(League.name == "Serie A")
        )
        if league:
            print(f"\nLeague 'Serie A' understat_slug: {league.understat_slug}")
        else:
            print("\nLeague 'Serie A' not found.")

if __name__ == "__main__":
    asyncio.run(verify())