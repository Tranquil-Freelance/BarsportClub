#!/usr/bin/env python3
"""
xPalermoStat - Core Analytics API.
Implementation of the first 3 priority features: Shot Map, Timeline, xG Standings.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import List, Dict
from app.db.database import get_db
from app.db.models import Match, Shot
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

# --- SCHEMAS ---
class ShotData(BaseModel):
    minute: int
    player: str
    xg: float
    x: float
    y: float
    result: str
    team_type: str

class MatchTimeline(BaseModel):
    minute: int
    h_cum_xg: float
    a_cum_xg: float

# --- ENDPOINTS ---

@router.get("/match/{match_id}/shots", response_model=List[ShotData])
async def get_match_shots(match_id: int, db: AsyncSession = Depends(get_db)):
    """FEATURE 1: Shot Map Interattiva"""
    result = await db.execute(select(Shot).where(Shot.match_id == match_id))
    shots = result.scalars().all()
    if not shots:
        raise HTTPException(status_code=404, detail="Shots not found for this match")
    
    return [
        ShotData(
            minute=s.minute,
            player=s.player,
            xg=s.xG,
            x=s.X,
            y=s.Y,
            result=s.result,
            team_type=s.team_type
        ) for s in shots
    ]

@router.get("/match/{match_id}/timeline", response_model=List[MatchTimeline])
async def get_match_timeline(match_id: int, db: AsyncSession = Depends(get_db)):
    """FEATURE 2: Timeline xG Cumulativa (Window Function)"""
    # Usiamo SQL puro via SQLAlchemy per sfruttare le Window Functions in modo efficiente
    query = text("""
        SELECT 
            minute,
            SUM(CASE WHEN team_type = 'h' THEN "xG" ELSE 0 END) OVER (ORDER BY minute) as h_cum,
            SUM(CASE WHEN team_type = 'a' THEN "xG" ELSE 0 END) OVER (ORDER BY minute) as a_cum
        FROM shots
        WHERE match_id = :match_id
        ORDER BY minute ASC
    """)
    
    result = await db.execute(query, {"match_id": match_id})
    rows = result.fetchall()
    
    return [MatchTimeline(minute=r[0], h_cum_xg=round(r[1], 3), a_cum_xg=round(r[2], 3)) for r in rows]

@router.get("/standings/xg")
async def get_xg_standings(db: AsyncSession = Depends(get_db)):
    """FEATURE 3: Classifica xG Serie A (Aggregata)"""
    # Calcolo xG fatti e concessi per squadra
    # Nota: Questo richiede una logica che colleghi Match e Shot per determinare i nomi dei team
    query = text("""
        WITH team_shots AS (
            SELECT 
                CASE WHEN s.team_type = 'h' THEN m.home_team ELSE m.away_team END as team,
                s."xG" as xg_made,
                0 as xg_conceded
            FROM shots s
            JOIN matches m ON s.match_id = m.id
            UNION ALL
            SELECT 
                CASE WHEN s.team_type = 'h' THEN m.away_team ELSE m.home_team END as team,
                0 as xg_made,
                s."xG" as xg_conceded
            FROM shots s
            JOIN matches m ON s.match_id = m.id
        )
        SELECT 
            team,
            SUM(xg_made) as total_xg,
            SUM(xg_conceded) as total_xga,
            (SUM(xg_made) - SUM(xg_conceded)) as xg_diff
        FROM team_shots
        GROUP BY team
        ORDER BY total_xg DESC
    """)
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    return [
        {
            "team": r[0],
            "xG": round(r[1], 2),
            "xGA": round(r[2], 2),
            "diff": round(r[3], 2)
        } for r in rows
    ]