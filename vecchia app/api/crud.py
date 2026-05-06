from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, and_
from app.db.models import Match

async def get_standings(db: AsyncSession):
    """
    Compute Serie A standings from matches.
    Returns list of teams with aggregated stats.
    """
    # For now, return empty list because matches lack scores.
    # TODO: implement proper standings calculation when scores are available.
    return []

async def get_matches(db: AsyncSession, round_number: int = None):
    # Simple implementation returning all matches
    stmt = select(Match)
    if round_number is not None:
        stmt = stmt.where(Match.matchday == round_number)
    result = await db.execute(stmt)
    return result.scalars().all()