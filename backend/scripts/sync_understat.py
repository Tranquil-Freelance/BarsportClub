#!/usr/bin/env python3
"""
Sync Understat Serie A team and season stats into the database.
Fetches the current season (2025) from understat.com, extracts teamsData,
and upserts Team and TeamSeasonStat records.
"""

import asyncio
import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, Any, List

import aiohttp
from aiohttp import ClientTimeout
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

# Add the parent directory to sys.path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import AsyncSessionLocal
from app.models.football import League, Team, TeamSeasonStat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

UNDERSTAT_API_URL = "https://understat.com/getLeagueData/Serie_A/2025"
TEAMS_DATA_VAR = "teamsData"  # kept for compatibility


async def fetch_teams_data(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """
    Fetch teams data from Understat API (JSON).
    Returns the parsed JSON dictionary containing 'teams' key.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "X-Requested-With": "XMLHttpRequest",
    }
    timeout = ClientTimeout(total=30)
    async with session.get(UNDERSTAT_API_URL, headers=headers, timeout=timeout) as response:
        response.raise_for_status()
        # Understat returns JSON with content‑type text/javascript;charset=UTF-8
        # aiohttp's .json() expects application/json, so we read raw text and parse.
        text = await response.text()
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from Understat API: {e}")
            logger.debug(f"First 500 chars of response: {text[:500]}")
            raise
        return data


def compute_season_totals(team_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute aggregate statistics from a team's match history.
    """
    if not team_history:
        return {}
    
    totals = {
        "matches_played": len(team_history),
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "goals_for": 0,
        "goals_against": 0,
        "points": 0,
        "xpts": 0.0,
        "xG_for": 0.0,
        "xG_against": 0.0,
        "npxG_for": 0.0,
        "npxG_against": 0.0,
        "deep_completions": 0,
        "deep_allowed": 0,
        "ppda_passes": 0,   # sum of ppda.att
        "ppda_def": 0,      # sum of ppda.def
        "oppda_passes": 0,  # sum of ppda_allowed.att
        "oppda_def": 0,     # sum of ppda_allowed.def
    }
    
    for match in team_history:
        # Determine result
        scored = match.get("scored", 0)
        missed = match.get("missed", 0)
        if scored > missed:
            totals["wins"] += 1
        elif scored == missed:
            totals["draws"] += 1
        else:
            totals["losses"] += 1
        
        totals["goals_for"] += scored
        totals["goals_against"] += missed
        totals["points"] += match.get("pts", 0)
        totals["xpts"] += match.get("xpts", 0.0)
        totals["xG_for"] += match.get("xG", 0.0)
        totals["xG_against"] += match.get("xGA", 0.0)
        totals["npxG_for"] += match.get("npxG", 0.0)
        totals["npxG_against"] += match.get("npxGA", 0.0)
        totals["deep_completions"] += match.get("deep", 0)
        totals["deep_allowed"] += match.get("deep_allowed", 0)
        
        ppda = match.get("ppda", {})
        totals["ppda_passes"] += ppda.get("att", 0)
        totals["ppda_def"] += ppda.get("def", 0)
        
        ppda_allowed = match.get("ppda_allowed", {})
        totals["oppda_passes"] += ppda_allowed.get("att", 0)
        totals["oppda_def"] += ppda_allowed.get("def", 0)
    
    # Calculate PPDA (passes per defensive action)
    totals["ppda"] = (
        totals["ppda_passes"] / totals["ppda_def"]
        if totals["ppda_def"] > 0 else None
    )
    totals["oppda"] = (
        totals["oppda_passes"] / totals["oppda_def"]
        if totals["oppda_def"] > 0 else None
    )
    
    return totals


async def ensure_league(db: AsyncSession) -> League:
    """
    Ensure a League record for Serie A exists.
    Returns the League instance.
    """
    # Try to find by Understat slug first
    stmt = select(League).where(League.understat_slug == "Serie_A")
    result = await db.execute(stmt)
    league = result.scalar_one_or_none()
    if league:
        logger.info(f"Using existing league (by slug): {league.name} (ID {league.id})")
        return league
    
    # If not found, try by name "Serie A"
    stmt = select(League).where(League.name == "Serie A")
    result = await db.execute(stmt)
    league = result.scalar_one_or_none()
    if league:
        # Update understat_slug for future
        if league.understat_slug != "Serie_A":
            league.understat_slug = "Serie_A"
            logger.info(f"Updated league understat_slug to 'Serie_A'")
        logger.info(f"Using existing league (by name): {league.name} (ID {league.id})")
        return league
    
    # Create new league
    league = League(name="Serie A", understat_slug="Serie_A")
    db.add(league)
    await db.commit()
    await db.refresh(league)
    logger.info(f"Created new league: {league.name} (ID {league.id})")
    return league


async def upsert_team(db: AsyncSession, league_id: int, team_data: Dict[str, Any]) -> Team:
    """
    Upsert a Team record. team_data must contain 'id', 'title', 'short_title'.
    Returns the Team instance.
    """
    team_id = int(team_data["id"])
    team_name = team_data["title"]
    
    stmt = select(Team).where(Team.id == team_id)
    result = await db.execute(stmt)
    team = result.scalar_one_or_none()
    
    if team:
        # Update name if changed (unlikely)
        if team.name != team_name:
            team.name = team_name
            logger.info(f"Updated team name: {team_name}")
        return team
    
    # Insert new team
    team = Team(id=team_id, name=team_name, league_id=league_id)
    db.add(team)
    # Since we have a manual ID, we need to flush to avoid conflict with sequence
    await db.flush()
    logger.info(f"Created new team: {team_name} (ID {team_id})")
    return team


async def upsert_team_season_stat(
    db: AsyncSession,
    team_id: int,
    league_id: int,
    season: str,
    totals: Dict[str, Any],
) -> TeamSeasonStat:
    """
    Upsert a TeamSeasonStat record.
    """
    # Build data dict for upsert
    data = {
        "team_id": team_id,
        "league_id": league_id,
        "season": season,
        "matches_played": totals["matches_played"],
        "wins": totals["wins"],
        "draws": totals["draws"],
        "losses": totals["losses"],
        "goals_for": totals["goals_for"],
        "goals_against": totals["goals_against"],
        "points": totals["points"],
        "xpts": round(totals["xpts"], 2),
        "xG_for": round(totals["xG_for"], 2),
        "xG_against": round(totals["xG_against"], 2),
        "ppda": round(totals["ppda"], 3) if totals["ppda"] is not None else None,
        "deep_completions": totals["deep_completions"],
    }
    
    # Insert or update
    insert_stmt = pg_insert(TeamSeasonStat).values(**data)
    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["team_id", "league_id", "season"],
        set_={k: insert_stmt.excluded[k] for k in data.keys()}
    )
    await db.execute(upsert_stmt)
    await db.commit()
    
    # Retrieve the record
    stmt = select(TeamSeasonStat).where(
        TeamSeasonStat.team_id == team_id,
        TeamSeasonStat.league_id == league_id,
        TeamSeasonStat.season == season,
    )
    result = await db.execute(stmt)
    stat = result.scalar_one()
    logger.info(
        f"Upserted TeamSeasonStat for team {team_id} season {season}: "
        f"{stat.wins}W {stat.draws}D {stat.losses}L, "
        f"{stat.goals_for}GF {stat.goals_against}GA, "
        f"{stat.points} pts, xG {stat.xG_for:.2f}"
    )
    return stat


async def main():
    """Main sync routine."""
    logger.info("Starting Understat sync for Serie A 2025")
    
    # Fetch teams data from Understat API
    async with aiohttp.ClientSession() as http_session:
        try:
            data = await fetch_teams_data(http_session)
        except Exception as e:
            logger.error(f"Failed to fetch teams data: {e}")
            sys.exit(1)
    
    teams_data = data.get("teams", {})
    if not teams_data:
        logger.error("No teams found in teamsData")
        sys.exit(1)
    
    logger.info(f"Found {len(teams_data)} teams")
    
    # Database session
    async with AsyncSessionLocal() as db:
        # Ensure league exists
        league = await ensure_league(db)
        
        # Process each team
        for team_id_str, team_data in teams_data.items():
            try:
                team_id = int(team_id_str)
                team_name = team_data.get("title", "Unknown")
                logger.info(f"Processing team: {team_name} (ID {team_id})")
                
                # Upsert Team
                team = await upsert_team(db, league.id, team_data)
                
                # Compute season totals from history
                history = team_data.get("history", [])
                if not history:
                    logger.warning(f"No history for team {team_name}, skipping season stats")
                    continue
                
                totals = compute_season_totals(history)
                
                # Log xG as requested
                logger.info(f"Team {team_name} has total xG {totals['xG_for']:.2f}")
                
                # Upsert TeamSeasonStat
                await upsert_team_season_stat(
                    db,
                    team.id,
                    league.id,
                    "2025/26",
                    totals,
                )
                
            except Exception as e:
                logger.exception(f"Error processing team {team_id_str}: {e}")
                # Continue with next team
    
    logger.info("Understat sync completed successfully")


if __name__ == "__main__":
    asyncio.run(main())