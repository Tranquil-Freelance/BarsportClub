"""
Statistical aggregations API endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.football import Player, PlayerMatchStat, Team, MatchCalendar
from app.schemas.statistics import PlayerStatAggResponse

router = APIRouter()


@router.get("/players/top", response_model=List[PlayerStatAggResponse])
async def get_top_players(
    league_id: int = Query(..., description="League ID to filter matches"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of players to return"),
    min_minutes: int = Query(90, ge=0, description="Minimum total minutes played"),
    db: AsyncSession = Depends(get_db),
) -> List[PlayerStatAggResponse]:
    """
    Retrieve top players by xG in a given league.
    Aggregates match‑level statistics (goals, xG, xA, minutes) per player.
    """
    stmt = (
        select(
            Player.id.label("player_id"),
            Player.name.label("player_name"),
            Team.name.label("team_name"),
            func.count(PlayerMatchStat.match_id).label("matches_played"),
            func.sum(PlayerMatchStat.minutes_played).label("total_minutes"),
            func.sum(PlayerMatchStat.goals).label("total_goals"),
            func.sum(PlayerMatchStat.assists).label("total_assists"),
            func.sum(PlayerMatchStat.xG).label("total_xG"),
            func.sum(PlayerMatchStat.xA).label("total_xA"),
        )
        .select_from(PlayerMatchStat)
        .join(Player, PlayerMatchStat.player_id == Player.id)
        .join(Team, Player.current_team_id == Team.id, isouter=True)
        .join(MatchCalendar, PlayerMatchStat.match_id == MatchCalendar.id)
        .where(MatchCalendar.league_id == league_id, MatchCalendar.is_completed == True, MatchCalendar.is_scraped == True)
        .group_by(Player.id, Player.name, Team.name)
        .having(func.sum(PlayerMatchStat.minutes_played) >= min_minutes)
        .order_by(func.sum(PlayerMatchStat.xG).desc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.fetchall()

    response = []
    for row in rows:
        total_minutes = row.total_minutes or 0
        total_xG = row.total_xG or 0.0
        xg_per_90 = (total_xG / total_minutes * 90) if total_minutes > 0 else 0.0

        response.append(
            PlayerStatAggResponse(
                player_id=row.player_id,
                player_name=row.player_name,
                team_name=row.team_name,
                matches_played=row.matches_played,
                total_minutes=total_minutes,
                total_goals=row.total_goals or 0,
                total_assists=row.total_assists or 0,
                total_xG=total_xG,
                total_xA=row.total_xA or 0.0,
                xG_per_90=xg_per_90,
            )
        )

    return response