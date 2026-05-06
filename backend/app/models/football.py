"""
SQLAlchemy 2.0 models for football analytics.
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.db.base_class import Base


class League(Base):
    """
    League entity (e.g., Serie A, Premier League).
    """

    __tablename__ = "league"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    understat_slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Relationships
    teams: Mapped[list["Team"]] = relationship("Team", back_populates="league")
    matches: Mapped[list["MatchCalendar"]] = relationship(
        "MatchCalendar", back_populates="league"
    )

    def __repr__(self) -> str:
        return f"<League(id={self.id}, name='{self.name}')>"


class Team(Base):
    """
    Team entity (e.g., Palermo, Juventus).
    """

    __tablename__ = "team"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    league_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("league.id"), nullable=False
    )

    # Relationships
    league: Mapped["League"] = relationship("League", back_populates="teams")
    players: Mapped[list["Player"]] = relationship("Player", back_populates="team")
    home_matches: Mapped[list["MatchCalendar"]] = relationship(
        "MatchCalendar",
        foreign_keys="MatchCalendar.home_team_id",
        back_populates="home_team",
    )
    away_matches: Mapped[list["MatchCalendar"]] = relationship(
        "MatchCalendar",
        foreign_keys="MatchCalendar.away_team_id",
        back_populates="away_team",
    )

    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name='{self.name}')>"


class Player(Base):
    """
    Player entity.
    """

    __tablename__ = "player"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    current_team_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("team.id"), nullable=True
    )

    # Relationships
    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="players")
    match_stats: Mapped[list["PlayerMatchStat"]] = relationship(
        "PlayerMatchStat", back_populates="player"
    )

    def __repr__(self) -> str:
        return f"<Player(id={self.id}, name='{self.name}')>"


class MatchCalendar(Base):
    """
    Match calendar with completion and scraping flags.
    """

    __tablename__ = "matchcalendar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    league_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("league.id"), nullable=False
    )
    home_team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("team.id"), nullable=False
    )
    away_team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("team.id"), nullable=False
    )
    match_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    round: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_scraped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    home_goals: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    away_goals: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    home_xG: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    away_xG: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    league: Mapped["League"] = relationship("League", back_populates="matches")
    home_team: Mapped["Team"] = relationship(
        "Team", foreign_keys=[home_team_id], back_populates="home_matches"
    )
    away_team: Mapped["Team"] = relationship(
        "Team", foreign_keys=[away_team_id], back_populates="away_matches"
    )
    player_stats: Mapped[list["PlayerMatchStat"]] = relationship(
        "PlayerMatchStat", back_populates="match"
    )

    def __repr__(self) -> str:
        return f"<MatchCalendar(id={self.id}, {self.home_team_id} vs {self.away_team_id})>"


class PlayerMatchStat(Base):
    """
    Advanced statistics for a player in a single match.
    """

    __tablename__ = "playermatchstat"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    player_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("player.id"), nullable=False
    )
    match_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("matchcalendar.id"), nullable=False
    )
    minutes_played: Mapped[int] = mapped_column(Integer, nullable=False)
    goals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assists: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shots: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    key_passes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    xG: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    xA: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    xGChain: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    xGBuildup: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    position: Mapped[str] = mapped_column(String(10), nullable=False)
    progressive_passes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    passes_completed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    passes_attempted: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pass_completion_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    progressive_carries: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    dribbles_succeeded: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    dribbles_attempted: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tackles: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    interceptions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    blocks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    clearances: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    aerials_won: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    aerials_lost: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shot_creating_actions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    goal_creating_actions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    touches: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pressures: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    successful_pressures: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recoveries: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    player: Mapped["Player"] = relationship("Player", back_populates="match_stats")
    match: Mapped["MatchCalendar"] = relationship(
        "MatchCalendar", back_populates="player_stats"
    )

    __table_args__ = (
        UniqueConstraint("player_id", "match_id", name="uq_player_match"),
    )

    def __repr__(self) -> str:
        return f"<PlayerMatchStat(player={self.player_id}, match={self.match_id})>"


class TeamSeasonStat(Base):
    """
    Team‑level seasonal aggregates (advanced metrics).
    """

    __tablename__ = "team_season_stat"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("team.id"), nullable=False
    )
    league_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("league.id"), nullable=False
    )
    season: Mapped[str] = mapped_column(String(9), nullable=False)  # e.g., "2025/26"
    matches_played: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    draws: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    losses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    goals_for: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    goals_against: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    xG_for: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    xG_against: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    xpts: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_possession: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    passes_completed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    passes_attempted: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pass_completion_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    progressive_passes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    progressive_carries: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tackles: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    interceptions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pressures: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shots_for: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shots_on_target_for: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shots_against: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shots_on_target_against: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ppda: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # passes allowed per defensive action
    deep_completions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sca: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # shot‑creating actions
    gca: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # goal‑creating actions

    # Relationships
    team: Mapped["Team"] = relationship("Team", backref="season_stats")
    league: Mapped["League"] = relationship("League", backref="team_season_stats")

    __table_args__ = (
        UniqueConstraint("team_id", "league_id", "season", name="uq_team_league_season"),
    )

    def __repr__(self) -> str:
        return f"<TeamSeasonStat(team={self.team_id}, season={self.season})>"