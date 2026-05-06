from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    understat_id = Column(Integer, unique=True, index=True)
    league_id = Column(Integer, nullable=True) 
    home_team = Column(String, index=True)
    away_team = Column(String, index=True)
    home_score = Column(Integer, default=0)
    away_score = Column(Integer, default=0)
    home_goals = Column(Integer, default=0)
    away_goals = Column(Integer, default=0)
    home_xG = Column('home_xg', Float, default=0.0)
    away_xG = Column('away_xg', Float, default=0.0)
    match_datetime = Column(DateTime, nullable=True)
    status = Column(String, default="programmato")
    is_completed = Column(Boolean, default=False)
    is_scraped = Column(Boolean, default=False)
    
    shots = relationship("Shot", back_populates="match", cascade="all, delete-orphan")
    player_stats = relationship("PlayerStat", back_populates="match", cascade="all, delete-orphan")

class Shot(Base):
    __tablename__ = "shots"
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    minute = Column(Integer, nullable=False)
    player = Column(String, nullable=False)
    xG = Column(Float, default=0.0)
    result = Column(String)
    team_type = Column(String) 
    X = Column(Float, default=0.0)
    Y = Column(Float, default=0.0)
    situation = Column(String)
    shotType = Column(String)
    assist = Column(String, nullable=True)
    match = relationship("Match", back_populates="shots")
    __table_args__ = (UniqueConstraint('match_id', 'minute', 'player', 'team_type', name='uq_shot_unique'),)

class PlayerStat(Base):
    __tablename__ = "player_stats"
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    player_id = Column(Integer, nullable=False, index=True)
    player_name = Column(String, nullable=False)
    team_name = Column(String, nullable=False)
    team_type = Column(String)
    time = Column(Integer, default=0)
    position = Column(String)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    shots = Column(Integer, default=0)
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    xG = Column(Float, default=0.0)
    npxG = Column(Float, default=0.0)
    xA = Column(Float, default=0.0)
    xGChain = Column(Float, default=0.0)
    xGBuildup = Column(Float, default=0.0)
    key_passes = Column(Integer, default=0)
    match = relationship("Match", back_populates="player_stats")
    __table_args__ = (UniqueConstraint('match_id', 'player_id', name='uq_player_stat_unique'),)