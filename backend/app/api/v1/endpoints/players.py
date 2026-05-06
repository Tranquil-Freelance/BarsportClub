"""
Players API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.football import Player
from app.schemas.football import PlayerResponse

router = APIRouter()


@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(
    player_id: int,
    db: AsyncSession = Depends(get_db),
) -> PlayerResponse:
    """
    Retrieve a single player by ID.
    """
    stmt = select(Player).where(Player.id == player_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return player