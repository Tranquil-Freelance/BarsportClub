"""
Pydantic schemas for football entities.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict


class TeamBase(BaseModel):
    """Base schema for Team."""

    id: int
    name: str
    league_id: int


class TeamResponse(TeamBase):
    """Response schema for Team (ORM compatible)."""

    model_config = ConfigDict(from_attributes=True)


class LeagueBase(BaseModel):
    """Base schema for League."""

    id: int
    name: str
    understat_slug: str


class LeagueResponse(LeagueBase):
    """Response schema for League (ORM compatible)."""

    model_config = ConfigDict(from_attributes=True)


class PlayerBase(BaseModel):
    """Base schema for Player."""

    id: int
    name: str
    current_team_id: Optional[int] = None


class PlayerResponse(PlayerBase):
    """Response schema for Player (ORM compatible)."""

    model_config = ConfigDict(from_attributes=True)