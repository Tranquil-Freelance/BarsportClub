"""
SQLAlchemy ORM models for player and match statistics.
"""
from datetime import date
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Float, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Player(Base):
    """
    Player entity with unique understat identifier.
    """
    __tablename__ = "player"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    understat_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    team: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    match_stats: Mapped[list["MatchStat"]] = relationship(
        "MatchStat", back_populates="player", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Player(id={self.id}, name='{self.name}', team='{self.team}')>"


class MatchStat(Base):
    """
    Match‑level statistics for a player.
    """
    __tablename__ = "match_stat"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    player_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("player.id", ondelete="CASCADE"), nullable=False
    )
    match_date: Mapped[date] = mapped_column(Date, nullable=False)
    goals: Mapped[int] = mapped_column(Integer, default=0)
    assists: Mapped[int] = mapped_column(Integer, default=0)
    xG: Mapped[float] = mapped_column(Float, default=0.0)
    xA: Mapped[float] = mapped_column(Float, default=0.0)
    shots: Mapped[int] = mapped_column(Integer, default=0)
    key_passes: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    player: Mapped["Player"] = relationship("Player", back_populates="match_stats")

    def __repr__(self) -> str:
        return (
            f"<MatchStat(id={self.id}, player_id={self.player_id}, "
            f"date={self.match_date}, goals={self.goals}, assists={self.assists})>"
        )