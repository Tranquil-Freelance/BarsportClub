"""
Fractional Kelly Criterion — Staking Engine
=============================================
Phase 1 of the Capital Allocation layer.

Calculates optimal bet sizing using the Fractional Kelly Criterion
with strict safety caps.

All functions are pure — no database or I/O dependencies.
"""

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — Safety Caps
# ---------------------------------------------------------------------------

MAX_STAKE_FRACTION: float = 0.05
"""Absolute maximum fraction of bankroll that can be wagered on any single bet."""

MIN_STAKE_FRACTION: float = 0.005
"""Minimum fraction threshold — bets below this are rejected (0.5 % of bankroll)."""

DEFAULT_KELLY_FRACTION: float = 0.25
"""Default fraction of the full Kelly to use (conservative 25 %)."""


# ---------------------------------------------------------------------------
# Core — Fractional Kelly Calculator
# ---------------------------------------------------------------------------


def calculate_kelly_fraction(
    p_model: float,
    decimal_odds: float,
    fraction: float = DEFAULT_KELLY_FRACTION,
) -> float:
    """
    Compute the optimal fraction of bankroll to stake using Fractional Kelly.

    Parameters
    ----------
    p_model : float
        The model's estimated probability of the outcome (0.0 – 1.0).
    decimal_odds : float
        The bookmaker's decimal odds (e.g. 2.10).
    fraction : float, optional
        Fraction of full Kelly to apply (default 0.25 = 25 %).

    Returns
    -------
    float
        Recommended stake as a fraction of bankroll.
        0.0 means no bet should be placed.

    Logic
    -----
    1. Compute net odds:  ``b = decimal_odds - 1.0``
    2. Compute loss probability:  ``q = 1.0 - p_model``
    3. Full Kelly:  ``full_kelly = (b * p_model - q) / b``   (if b > 0)
       If b <= 0,  full_kelly = 0.0
    4. Target stake:  ``target_stake = full_kelly * fraction``

    Safety Caps (Strict)
    --------------------
    - If full_kelly <= 0  →  return 0.0  (no value, no bet).
    - Max cap:  ``min(target_stake, MAX_STAKE_FRACTION)``
    - Min threshold:  if target_stake < MIN_STAKE_FRACTION  →  return 0.0
    """
    # ── Guard: invalid or non-positive odds ─────────────────────────────
    if decimal_odds <= 1.0:
        logger.debug(
            "Kelly: decimal_odds=%.4f <= 1.0, no edge possible → 0.0",
            decimal_odds,
        )
        return 0.0

    # ── Step 1: Net odds ────────────────────────────────────────────────
    b = decimal_odds - 1.0

    # ── Step 2: Loss probability ────────────────────────────────────────
    q = 1.0 - p_model

    # ── Step 3: Full Kelly ──────────────────────────────────────────────
    full_kelly = (b * p_model - q) / b

    # ── Safety: negative or zero EV → no bet ────────────────────────────
    if full_kelly <= 0.0:
        logger.debug(
            "Kelly: full_kelly=%.6f <= 0 (p_model=%.4f, odds=%.4f) → 0.0",
            full_kelly,
            p_model,
            decimal_odds,
        )
        return 0.0

    # ── Step 4: Fractional Kelly target ─────────────────────────────────
    target_stake = full_kelly * fraction

    # ── Min stake cap: below 0.5 % of bankroll → no bet ─────────────────
    if target_stake < MIN_STAKE_FRACTION:
        logger.debug(
            "Kelly: target_stake=%.6f < MIN_STAKE_FRACTION=%.4f → 0.0",
            target_stake,
            MIN_STAKE_FRACTION,
        )
        return 0.0

    # ── Max stake cap: never exceed 5 % of bankroll ─────────────────────
    final_stake = min(target_stake, MAX_STAKE_FRACTION)

    logger.debug(
        "Kelly: p_model=%.4f odds=%.4f fraction=%.2f → full=%.6f target=%.6f final=%.6f",
        p_model,
        decimal_odds,
        fraction,
        full_kelly,
        target_stake,
        final_stake,
    )

    return round(final_stake, 6)
