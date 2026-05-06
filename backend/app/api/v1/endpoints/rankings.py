from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.database import AsyncSessionLocal
from app.db.models import PlayerStat

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/xgchain-leaders")
async def get_xgchain_leaders(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Restituisce i leader della Serie A per xGChain dal 2020."""
    stmt = (
        select(
            PlayerStat.player_name, 
            func.sum(PlayerStat.xGChain).label('total_xgchain')
        )
        .group_by(PlayerStat.player_name)
        .order_by(func.sum(PlayerStat.xGChain).desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    return [
        {"name": r.player_name, "xgchain": round(r.total_xgchain, 2)} 
        for r in rows
    ]