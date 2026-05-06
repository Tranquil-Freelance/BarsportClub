"""
Pure-Math Bet Settlement Engine
================================
Phase 6 — Resolves bets by computing exact profit/loss from a finished
match's actual score.

All functions are pure — zero database or I/O dependencies.

Supported markets
-----------------
- **1X2** — ``1x2_home``, ``1x2_draw``, ``1x2_away``
- **Over / Under** — ``over_X.X``, ``under_X.X``  (push if total == line)
- **Both Teams to Score** — ``btts_yes``, ``btts_no``
- **Asian Handicap** — ``ah_{line}_home`` / ``ah_{line}_away``

  Full / half lines (multiples of 0.5) resolve directly.

  **Quarter lines** (e.g. AH -0.25, -0.75, +0.25, +1.25) split into
  two component lines (line ± 0.25), each with 50 % of the stake.
"""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EPS: float = 1e-9
"""Numerical tolerance for floating-point comparisons."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def calculate_profit(
    market_key: str,
    decimal_odds: float,
    stake: float,
    home_goals: int,
    away_goals: int,
) -> float:
    """
    Compute the net profit (or loss) for a single settled bet.

    Parameters
    ----------
    market_key : str
        Machine-readable market identifier, e.g. ``"1x2_home"``,
        ``"over_2.5"``, ``"ah_-0.75_home"``, ``"btts_yes"``.
    decimal_odds : float
        Decimal odds at placement (must be >= 1.0).
    stake : float
        Fraction of bankroll wagered (positive).
    home_goals : int
        Actual goals scored by the home team.
    away_goals : int
        Actual goals scored by the away team.

    Returns
    -------
    float
        Net profit:
        - **Positive** → winning bet (e.g. ``stake * (odds - 1)``).
        - **Negative** → losing bet (``-stake``).
        - **0.0** → push / void (full stake returned).

    Raises
    ------
    ValueError
        If ``market_key`` cannot be parsed.
    """
    # ── Guard: non-positive stake ──────────────────────────────────────
    if stake <= 0.0:
        return 0.0

    goal_diff: int = home_goals - away_goals
    total_goals: int = home_goals + away_goals

    # ── Normalise market key ───────────────────────────────────────────
    mk = market_key.strip().lower()

    # ── 1X2 markets ────────────────────────────────────────────────────
    if mk.startswith("1x2_"):
        outcome = mk.replace("1x2_", "")
        return _resolve_1x2(outcome, decimal_odds, stake, goal_diff)

    # ── Over / Under ───────────────────────────────────────────────────
    if mk.startswith("over_") or mk.startswith("under_"):
        return _resolve_over_under(mk, decimal_odds, stake, total_goals)

    # ── Both Teams to Score ────────────────────────────────────────────
    if mk == "btts_yes":
        if home_goals > 0 and away_goals > 0:
            return stake * (decimal_odds - 1.0)
        return -stake

    if mk == "btts_no":
        if home_goals == 0 or away_goals == 0:
            return stake * (decimal_odds - 1.0)
        return -stake

    # ── Asian Handicap ─────────────────────────────────────────────────
    if mk.startswith("ah_"):
        return _resolve_asian_handicap(mk, decimal_odds, stake, goal_diff)

    # ── Unknown market key ─────────────────────────────────────────────
    raise ValueError(f"Unrecognised market_key: '{market_key}'")


# ---------------------------------------------------------------------------
# Internal — 1X2 resolver
# ---------------------------------------------------------------------------


def _resolve_1x2(
    outcome: str,
    decimal_odds: float,
    stake: float,
    goal_diff: int,
) -> float:
    """Resolve a standard 1X2 bet (home / draw / away)."""
    if outcome == "home":
        if goal_diff > 0:
            return stake * (decimal_odds - 1.0)
        return -stake

    if outcome == "draw":
        if goal_diff == 0:
            return stake * (decimal_odds - 1.0)
        return -stake

    if outcome == "away":
        if goal_diff < 0:
            return stake * (decimal_odds - 1.0)
        return -stake

    raise ValueError(f"Invalid 1X2 outcome: '{outcome}'")


# ---------------------------------------------------------------------------
# Internal — Over / Under resolver
# ---------------------------------------------------------------------------


def _resolve_over_under(
    market_key: str,
    decimal_odds: float,
    stake: float,
    total_goals: int,
) -> float:
    """Resolve an Over / Under bet with push support."""
    direction, line_str = market_key.split("_", 1)
    line = float(line_str)

    if direction == "over":
        if total_goals > line:
            return stake * (decimal_odds - 1.0)
        if abs(total_goals - line) <= EPS:
            return 0.0  # push
        return -stake

    # direction == "under"
    if total_goals < line:
        return stake * (decimal_odds - 1.0)
    if abs(total_goals - line) <= EPS:
        return 0.0  # push
    return -stake


# ---------------------------------------------------------------------------
# Internal — Asian Handicap resolver
# ---------------------------------------------------------------------------


def _resolve_asian_handicap(
    market_key: str,
    decimal_odds: float,
    stake: float,
    goal_diff: int,
) -> float:
    """
    Resolve an Asian Handicap bet.

    Parses the market key format ``ah_{line}_{side}`` where:
        - ``line``  is a float handicap value (e.g. ``-0.75``, ``+0.25``)
        - ``side``  is ``home`` or ``away``

    Quarter lines are split into two components with 50 % stake each.
    """
    # Strip "ah_" prefix, then split on last underscore for side
    inner = market_key[3:]  # remove "ah_"
    *line_parts, side = inner.rsplit("_", 1)
    line_str = "_".join(line_parts)
    line = float(line_str)

    # Compute effective goal difference from the bet side's perspective
    if side == "home":
        effective = goal_diff + line
    elif side == "away":
        effective = -goal_diff + line  # flip perspective
    else:
        raise ValueError(f"Invalid AH side: '{side}' in '{market_key}'")

    # ── Detect quarter line ────────────────────────────────────────────
    if _is_quarter_line(line):
        return _resolve_quarter_line(effective, line, decimal_odds, stake)

    # ── Integer / half line — resolve directly ─────────────────────────
    return _resolve_single_line(effective, stake, decimal_odds)


def _is_quarter_line(line: float) -> bool:
    """Return ``True`` if ``line`` is a quarter line (.25 or .75)."""
    remainder = abs(line) % 0.5
    return remainder > EPS and abs(remainder - 0.5) > EPS


def _resolve_quarter_line(
    effective: float,
    original_line: float,
    decimal_odds: float,
    total_stake: float,
) -> float:
    """
    Split a quarter-line AH bet into two components (line₁, line₂).

    Each component gets half the stake.

    **IMPORTANT**: This function adjusts the split by using the
    *component's own effective difference*, not the original effective.

    The split:
        line₁ = original_line + 0.25   (easier to win)
        line₂ = original_line - 0.25   (harder to win)

    For the component result we must recompute effective from scratch,
    but since ``effective = goal_diff + line`` for home side and
    ``effective = -goal_diff + line`` for away side, the per-component
    effective is just ``eff + 0.25`` or ``eff - 0.25`` where ``eff``
    is the effective computed with the *original* line.

    More concretely:

        eff₁ = goal_diff + (line + 0.25) = (goal_diff + line) + 0.25 = eff + 0.25
        eff₂ = goal_diff + (line - 0.25) = (goal_diff + line) - 0.25 = eff - 0.25

    This holds for both ``home`` and ``away`` sides because the
    ``±0.25`` adjustment is symmetric.
    """
    half_stake = total_stake / 2.0

    eff1 = effective + 0.25   # line + 0.25 component
    eff2 = effective - 0.25   # line - 0.25 component

    profit1 = _resolve_single_line(eff1, half_stake, decimal_odds)
    profit2 = _resolve_single_line(eff2, half_stake, decimal_odds)

    return profit1 + profit2


def _resolve_single_line(
    effective: float,
    component_stake: float,
    decimal_odds: float,
) -> float:
    """
    Resolve a single non-split Asian Handicap / Over-Under line.

    Rules
    -----
    - ``effective > EPS``   → win   → profit = component_stake × (odds - 1)
    - ``|effective| ≤ EPS`` → push  → profit = 0.0
    - ``effective < -EPS``  → loss  → profit = -component_stake
    """
    if effective > EPS:
        return component_stake * (decimal_odds - 1.0)
    if abs(effective) <= EPS:
        return 0.0
    return -component_stake
