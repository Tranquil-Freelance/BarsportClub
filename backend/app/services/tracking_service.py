"""
Data Tracking & Feature Logging Service
=========================================
Phase 5 — The Data Tracking Loop.

Persists every evaluated bet's feature vector into the ``features_log``
table for future ML training, and records actual executable bets into
the ``bets`` table with their calculated Fractional Kelly stakes.

All database writes are isolated in try/except/rollback blocks so that
logging failures never propagate up to break the API response.
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Bet, FeaturesLog
from app.services.staking_engine import calculate_kelly_fraction

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HYPOTHETICAL_BANKROLL: float = 10_000.0
"""Temporary fixed bankroll used until dynamic bankroll tracking is live."""

DEFAULT_BET_STATUS: str = "OPEN"
"""Status assigned to newly logged bets before settlement."""


# ---------------------------------------------------------------------------
# Function A — log_features
# ---------------------------------------------------------------------------


async def log_features(
    session: AsyncSession,
    match_id: int,
    market_key: str,
    features: Dict[str, Any],
) -> None:
    """
    Insert a feature-vector record into the ``features_log`` table.

    Parameters
    ----------
    session : AsyncSession
        Active DB session.
    match_id : int
        ``matchcalendar.id`` of the evaluated match.
    market_key : str
        Machine-readable market key, e.g. ``"over_2.5"``, ``"1x2_home"``.
    features : dict
        Feature dictionary with the following optional keys:

        - ``lambda_home``        — Poisson λ for home team
        - ``lambda_away``        — Poisson λ for away team
        - ``p_model``            — Model-estimated probability
        - ``p_book``             — Margin-free bookmaker probability
        - ``ev_base``            — Raw expected value before AI correction
        - ``team_strength_home`` — Home team xG_diff from rolling stats
        - ``team_strength_away`` — Away team xG_diff from rolling stats
        - ``stability_home``     — Home team stability score
        - ``stability_away``     — Away team stability score
        - ``odds``               — Bookmaker decimal odds

    Raises
    ------
    Exception
        Re-raised after rollback so callers can handle gracefully.
    """
    record = FeaturesLog(
        match_id=match_id,
        market_key=market_key,
        lambda_home=features.get("lambda_home"),
        lambda_away=features.get("lambda_away"),
        p_model=features.get("p_model"),
        p_book=features.get("p_book"),
        ev_base=features.get("ev_base"),
        team_strength_home=features.get("team_strength_home"),
        team_strength_away=features.get("team_strength_away"),
        stability_home=features.get("stability_home"),
        stability_away=features.get("stability_away"),
        odds=features.get("odds"),
    )

    try:
        session.add(record)
        await session.commit()
        logger.debug(
            "log_features: committed match_id=%s market=%s",
            match_id, market_key,
        )
    except Exception:
        await session.rollback()
        logger.exception(
            "log_features: failed for match_id=%s market=%s",
            match_id, market_key,
        )
        raise


# ---------------------------------------------------------------------------
# Function B — log_bet
# ---------------------------------------------------------------------------


async def log_bet(
    session: AsyncSession,
    match_id: int,
    market_key: str,
    odds: float,
    p_model: float,
    ev_final: float,
    recommended_stake_fraction: float,
    bankroll: Optional[float] = None,
) -> None:
    """
    Insert a bet record into the ``bets`` table.

    Calculates the absolute stake from the Fractional Kelly fraction and
    the current bankroll, then records bankroll state before and after.

    Parameters
    ----------
    session : AsyncSession
        Active DB session.
    match_id : int
        ``matchcalendar.id`` of the evaluated match.
    market_key : str
        Machine-readable market key.
    odds : float
        Bookmaker decimal odds at placement.
    p_model : float
        Model-estimated probability of the outcome.
    ev_final : float
        AI-corrected expected value.
    recommended_stake_fraction : float
        Fraction of bankroll to stake (output of Fractional Kelly engine).
        0.0 means "no bet".
    bankroll : float, optional
        Current bankroll amount.  Defaults to ``HYPOTHETICAL_BANKROLL``
        (10,000) until dynamic bankroll tracking is implemented.

    Raises
    ------
    Exception
        Re-raised after rollback so callers can handle gracefully.
    """
    if bankroll is None:
        bankroll = HYPOTHETICAL_BANKROLL

    # Calculate absolute stake amount in dollars
    stake_amount = round(bankroll * recommended_stake_fraction, 2)
    bankroll_after = round(bankroll - stake_amount, 2)

    record = Bet(
        match_id=match_id,
        market_key=market_key,
        decimal_odds=odds,
        p_model=p_model,
        ev=ev_final,
        stake=recommended_stake_fraction,
        bankroll_before=bankroll,
        bankroll_after=bankroll_after,
        status=DEFAULT_BET_STATUS,
    )

    try:
        session.add(record)
        await session.commit()
        logger.debug(
            "log_bet: committed match_id=%s market=%s stake_frac=%.4f stake_abs=$%.2f",
            match_id, market_key, recommended_stake_fraction, stake_amount,
        )
    except Exception:
        await session.rollback()
        logger.exception(
            "log_bet: failed for match_id=%s market=%s",
            match_id, market_key,
        )
        raise
