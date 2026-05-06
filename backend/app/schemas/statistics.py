"""
Pydantic schemas for statistical aggregations.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict


class PlayerStatAggResponse(BaseModel):
    """Response schema for aggregated player statistics."""

    player_id: int
    player_name: str
    team_name: Optional[str] = None
    matches_played: int
    total_minutes: int
    total_goals: int
    total_assists: int
    total_xG: float
    total_xA: float
    xG_per_90: float

    model_config = ConfigDict(from_attributes=True)