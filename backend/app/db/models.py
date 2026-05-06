from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, UniqueConstraint, Text, BigInteger
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()

class League(Base):
    __tablename__ = "league"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    understat_slug = Column(String, nullable=False)

class Team(Base):
    __tablename__ = "team"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    league_id = Column(Integer, ForeignKey("league.id"), nullable=True)

class Match(Base):
    __tablename__ = "matchcalendar"
    id = Column(BigInteger, primary_key=True, index=True)
    league_id = Column(Integer, nullable=True) 
    home_team_id = Column(Integer, index=True)
    away_team_id = Column(Integer, index=True)
    match_datetime = Column(DateTime(timezone=True), nullable=True)
    round = Column(Integer, nullable=True)
    is_completed = Column(Boolean, default=False)
    is_scraped = Column(Boolean, default=False)
    home_goals = Column(Integer, default=0)
    away_goals = Column(Integer, default=0)
    home_xG = Column(Float, default=0.0)
    away_xG = Column(Float, default=0.0)
    
    # === LA NUOVA SCATOLA PER IL VERDETTO AI DEL MERITOMETRO ===
    ai_verdict = Column(Text, nullable=True) 
    
    shots = relationship("Shot", back_populates="match", cascade="all, delete-orphan")
    player_stats = relationship("PlayerStat", back_populates="match", cascade="all, delete-orphan")

class Shot(Base):
    __tablename__ = "shots"
    id = Column(BigInteger, primary_key=True, index=True)
    match_id = Column(BigInteger, ForeignKey("matchcalendar.id", ondelete="CASCADE"), nullable=False)
    minute = Column(Integer, nullable=False)
    player = Column(String, nullable=False)
    player_id = Column(BigInteger, nullable=True)
    team_type = Column(String) 
    result = Column(String)
    xG = Column(Float, default=0.0)
    X = Column(Float, default=0.0)
    Y = Column(Float, default=0.0)
    situation = Column(String)
    shotType = Column(String)
    lastAction = Column(String, nullable=True)
    assist = Column(String, nullable=True) 

    match = relationship("Match", back_populates="shots")

    __table_args__ = (
        UniqueConstraint('match_id', 'minute', 'player', 'team_type', 'X', 'Y', name='uq_shot_atomic'),
    )

class PlayerStat(Base):
    __tablename__ = "player_stats"
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    match_id = Column(BigInteger, ForeignKey("matchcalendar.id", ondelete="CASCADE"), nullable=False)
    player_id = Column(BigInteger, nullable=False, index=True)
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

    __table_args__ = (
        UniqueConstraint('match_id', 'player_id', name='uq_player_match_stat'),
    )

class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    slug = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_published = Column(Boolean, default=True)


class Bet(Base):
    """
    Capital Allocation — Stakes & Bankroll Tracking
    =================================================
    Phase 1 of the Fractional Kelly Criterion layer.

    Records each placed bet with its stake, the bankroll state at
    placement time, and the resulting bankroll after settlement.
    """

    __tablename__ = "bets"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    match_id = Column(BigInteger, ForeignKey("matchcalendar.id", ondelete="SET NULL"), nullable=True, index=True)
    market_key = Column(String, nullable=False, comment="e.g. 'over_2.5', '1x2_home'")
    decimal_odds = Column(Float, nullable=False)
    p_model = Column(Float, nullable=False, comment="Model-estimated probability")
    ev = Column(Float, nullable=True, comment="Expected value at placement")

    # === CAPITAL ALLOCATION COLUMNS (Phase 1) ===
    stake = Column(Float, nullable=True, comment="Fraction of bankroll wagered (e.g. 0.02 = 2 %)")
    bankroll_before = Column(Float, nullable=True, comment="Bankroll balance immediately before placement")
    bankroll_after = Column(Float, nullable=True, comment="Bankroll balance immediately after placement")

    # === SETTLEMENT COLUMNS (Phase 6) ===
    profit = Column(Float, nullable=True, comment="Net profit after settlement (positive=win, negative=loss, 0.0=push)")

    status = Column(String, default="pending", comment="pending | won | lost | void | OPEN | SETTLED")
    placed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    settled_at = Column(DateTime(timezone=True), nullable=True)


class FeaturesLog(Base):
    """
    Feature Vector Repository — ML Training Data (Phase 5)
    =======================================================
    Logs every evaluated bet's feature vector for future ML model
    training and backtesting.  Each row captures the complete set
    of numerical features used by the AI risk model, plus team
    strength context.
    """

    __tablename__ = "features_log"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    match_id = Column(BigInteger, ForeignKey("matchcalendar.id", ondelete="SET NULL"), nullable=True, index=True)
    market_key = Column(String, nullable=False, comment="e.g. 'over_2.5', '1x2_home'")

    # === FEATURE VECTOR COLUMNS ===
    lambda_home = Column(Float, nullable=True, comment="Poisson λ for home team expected goals")
    lambda_away = Column(Float, nullable=True, comment="Poisson λ for away team expected goals")
    p_model = Column(Float, nullable=True, comment="Model-estimated probability of outcome")
    p_book = Column(Float, nullable=True, comment="Margin-free bookmaker probability")
    ev_base = Column(Float, nullable=True, comment="Raw expected value before AI correction")
    team_strength_home = Column(Float, nullable=True, comment="Home team xG_diff from rolling stats")
    team_strength_away = Column(Float, nullable=True, comment="Away team xG_diff from rolling stats")
    stability_home = Column(Float, nullable=True, comment="Home team xG_diff stability (lower = more consistent)")
    stability_away = Column(Float, nullable=True, comment="Away team xG_diff stability (lower = more consistent)")
    odds = Column(Float, nullable=True, comment="Bookmaker decimal odds")

    # === TARGET VARIABLE (Phase 6) ===
    outcome_profit = Column(Float, nullable=True, comment="Target variable y — actual profit/loss after settlement")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))