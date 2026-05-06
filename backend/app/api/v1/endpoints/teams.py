"""
Teams API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.football import Team, Player, League
from app.schemas.football import TeamResponse, PlayerResponse, LeagueResponse

router = APIRouter()


@router.get("/", response_model=List[TeamResponse])
async def list_teams(
    league_id: Optional[int] = Query(None, description="Filter by league ID"),
    db: AsyncSession = Depends(get_db),
) -> List[TeamResponse]:
    """
    Retrieve a list of teams, optionally filtered by league_id.
    """
    stmt = select(Team)
    if league_id is not None:
        stmt = stmt.where(Team.league_id == league_id)
    result = await db.execute(stmt)
    teams = result.scalars().all()
    return teams


@router.get("/leagues/", response_model=List[LeagueResponse])
async def list_leagues(
    db: AsyncSession = Depends(get_db),
) -> List[LeagueResponse]:
    """
    Retrieve a list of all leagues.
    """
    stmt = select(League)
    result = await db.execute(stmt)
    leagues = result.scalars().all()
    return leagues


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: int,
    db: AsyncSession = Depends(get_db),
) -> TeamResponse:
    """
    Retrieve a single team by ID.
    """
    stmt = select(Team).where(Team.id == team_id)
    result = await db.execute(stmt)
    team = result.scalar_one_or_none()
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.get("/{team_id}/players", response_model=List[PlayerResponse])
async def get_team_players(
    team_id: int,
    db: AsyncSession = Depends(get_db),
) -> List[PlayerResponse]:
    """
    Retrieve all players belonging to a specific team.
    """
    stmt = select(Player).where(Player.current_team_id == team_id)
    result = await db.execute(stmt)
    players = result.scalars().all()
    return players