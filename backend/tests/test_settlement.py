"""
Exhaustive unit tests for the Bet Settlement Engine (Phase 6).

Validates ``calculate_profit`` across every supported market type:

- **1X2** — home / draw / away (win, loss)
- **Over / Under** — win, loss, push (total == line)
- **Both Teams to Score** — yes / no
- **Asian Handicap — full / half lines** — no split (integer or .5)
- **Asian Handicap — quarter lines** — split into two components
  (the critical edge case for ML target variable correctness)

Quarter-line Asian Handicap tests explicitly verify:
  - AH -0.75: win by 2+ → full win; win by 1 → half win; draw → full loss
  - AH -0.25: win → full win; draw → half loss; loss → full loss
  - AH +0.25: win → full win; draw → half win; loss → full loss
  - AH +0.75: win → full win; draw → full win; loss by 1 → half loss
"""

import pytest
from app.services.settlement_math import (
    calculate_profit,
    _is_quarter_line,
)


# ===================================================================
# Utility
# ===================================================================


def _assert_profit(
    market_key: str,
    decimal_odds: float,
    stake: float,
    home_goals: int,
    away_goals: int,
    expected: float,
) -> None:
    """Assert that ``calculate_profit`` returns ``expected``."""
    result = calculate_profit(market_key, decimal_odds, stake, home_goals, away_goals)
    assert abs(result - expected) < 1e-9, (
        f"calculate_profit({market_key}, odds={decimal_odds}, stake={stake}, "
        f"{home_goals}-{away_goals}) => {result}, expected {expected}"
    )


# ===================================================================
# Test: 1X2 Markets
# ===================================================================


class Test1X2:
    """Standard 1X2 market resolution."""

    def test_home_win_when_home_wins(self):
        """1x2_home @ 2.10, stake=0.03, score 2-1 → profit = 0.03 × 1.10 = 0.033"""
        _assert_profit("1x2_home", 2.10, 0.03, 2, 1, 0.033)

    def test_home_loss_when_draw(self):
        """1x2_home @ 2.10, stake=0.03, score 1-1 → loss = -0.03"""
        _assert_profit("1x2_home", 2.10, 0.03, 1, 1, -0.03)

    def test_home_loss_when_away_wins(self):
        """1x2_home @ 2.10, stake=0.03, score 0-2 → loss = -0.03"""
        _assert_profit("1x2_home", 2.10, 0.03, 0, 2, -0.03)

    def test_draw_wins_on_tie(self):
        """1x2_draw @ 3.50, stake=0.02, score 1-1 → profit = 0.02 × 2.50 = 0.05"""
        _assert_profit("1x2_draw", 3.50, 0.02, 1, 1, 0.05)

    def test_draw_loses_when_home_wins(self):
        """1x2_draw @ 3.50, stake=0.02, score 2-1 → loss = -0.02"""
        _assert_profit("1x2_draw", 3.50, 0.02, 2, 1, -0.02)

    def test_draw_loses_when_away_wins(self):
        """1x2_draw @ 3.50, stake=0.02, score 0-1 → loss = -0.02"""
        _assert_profit("1x2_draw", 3.50, 0.02, 0, 1, -0.02)

    def test_away_wins_when_away_wins(self):
        """1x2_away @ 2.80, stake=0.04, score 1-3 → profit = 0.04 × 1.80 = 0.072"""
        _assert_profit("1x2_away", 2.80, 0.04, 1, 3, 0.072)

    def test_away_loses_when_draw(self):
        """1x2_away @ 2.80, stake=0.04, score 2-2 → loss = -0.04"""
        _assert_profit("1x2_away", 2.80, 0.04, 2, 2, -0.04)

    def test_away_loses_when_home_wins(self):
        """1x2_away @ 2.80, stake=0.04, score 3-1 → loss = -0.04"""
        _assert_profit("1x2_away", 2.80, 0.04, 3, 1, -0.04)


# ===================================================================
# Test: Over / Under Markets
# ===================================================================


class TestOverUnder:
    """Over / Under market resolution (including push)."""

    # ── Over ───────────────────────────────────────────────────────

    def test_over_wins_above_line(self):
        """over_2.5 @ 1.95, stake=0.05, 3-0 (total=3) → win = 0.05 × 0.95 = 0.0475"""
        _assert_profit("over_2.5", 1.95, 0.05, 3, 0, 0.0475)

    def test_over_loses_below_line(self):
        """over_2.5 @ 1.95, stake=0.05, 1-1 (total=2) → loss = -0.05"""
        _assert_profit("over_2.5", 1.95, 0.05, 1, 1, -0.05)

    def test_over_pushes_exactly_on_line(self):
        """over_2.0 @ 2.00, stake=0.03, 1-1 (total=2) → push = 0.0"""
        _assert_profit("over_2.0", 2.00, 0.03, 1, 1, 0.0)

    # ── Under ──────────────────────────────────────────────────────

    def test_under_wins_below_line(self):
        """under_2.5 @ 1.85, stake=0.04, 0-0 (total=0) → win = 0.04 × 0.85 = 0.034"""
        _assert_profit("under_2.5", 1.85, 0.04, 0, 0, 0.034)

    def test_under_loses_above_line(self):
        """under_2.5 @ 1.85, stake=0.04, 3-2 (total=5) → loss = -0.04"""
        _assert_profit("under_2.5", 1.85, 0.04, 3, 2, -0.04)

    def test_under_pushes_exactly_on_line(self):
        """under_3.0 @ 1.90, stake=0.02, 2-1 (total=3) → push = 0.0"""
        _assert_profit("under_3.0", 1.90, 0.02, 2, 1, 0.0)

    def test_under_wins_on_zero_zero(self):
        """under_0.5 @ 10.00, stake=0.01, 0-0 → win = 0.01 × 9.00 = 0.09"""
        _assert_profit("under_0.5", 10.00, 0.01, 0, 0, 0.09)


# ===================================================================
# Test: Both Teams to Score
# ===================================================================


class TestBTTS:
    """Both Teams to Score resolution."""

    def test_btts_yes_both_score(self):
        """btts_yes @ 2.00, stake=0.03, 2-1 → win = 0.03"""
        _assert_profit("btts_yes", 2.00, 0.03, 2, 1, 0.03)

    def test_btts_yes_one_team_blank(self):
        """btts_yes @ 2.00, stake=0.03, 1-0 → loss = -0.03"""
        _assert_profit("btts_yes", 2.00, 0.03, 1, 0, -0.03)

    def test_btts_no_one_team_blank(self):
        """btts_no @ 1.80, stake=0.02, 3-0 → win = 0.02 × 0.80 = 0.016"""
        _assert_profit("btts_no", 1.80, 0.02, 3, 0, 0.016)

    def test_btts_no_both_score(self):
        """btts_no @ 1.80, stake=0.02, 2-2 → loss = -0.02"""
        _assert_profit("btts_no", 1.80, 0.02, 2, 2, -0.02)


# ===================================================================
# Test: Asian Handicap — Full / Half Lines (no split)
# ===================================================================


class TestAsianHandicapStandard:
    """Non-split AH lines (integer or .5 multiples, e.g. -1.0, -0.5, 0.0, +1.0)."""

    # ── Integer line: push possible ────────────────────────────────

    def test_ah_minus_1_home_win_by_2(self):
        """ah_-1.0_home @ 2.10, stake=0.03, 3-1 (goal_diff=2) → win"""
        _assert_profit("ah_-1.0_home", 2.10, 0.03, 3, 1, 0.033)

    def test_ah_minus_1_home_win_by_1_push(self):
        """ah_-1.0_home @ 2.10, stake=0.03, 2-1 (goal_diff=1) → push = 0.0"""
        _assert_profit("ah_-1.0_home", 2.10, 0.03, 2, 1, 0.0)

    def test_ah_minus_1_home_draw_loss(self):
        """ah_-1.0_home @ 2.10, stake=0.03, 1-1 → loss = -0.03"""
        _assert_profit("ah_-1.0_home", 2.10, 0.03, 1, 1, -0.03)

    # ── Half line: no push possible ────────────────────────────────

    def test_ah_minus_0_5_home_wins(self):
        """ah_-0.5_home @ 1.95, stake=0.04, 2-1 → win = 0.04 × 0.95 = 0.038"""
        _assert_profit("ah_-0.5_home", 1.95, 0.04, 2, 1, 0.038)

    def test_ah_minus_0_5_home_draw_loss(self):
        """ah_-0.5_home @ 1.95, stake=0.04, 1-1 → loss = -0.04"""
        _assert_profit("ah_-0.5_home", 1.95, 0.04, 1, 1, -0.04)

    # ── Positive line, away side ───────────────────────────────────

    def test_ah_plus_0_5_away_draw_wins(self):
        """ah_+0.5_away @ 1.90, stake=0.02, 1-1 (away. eff = -0+0.5=0.5) → win"""
        _assert_profit("ah_+0.5_away", 1.90, 0.02, 1, 1, 0.018)

    def test_ah_plus_0_5_away_loss(self):
        """ah_+0.5_away @ 1.90, stake=0.02, 2-0 → loss = -0.02"""
        _assert_profit("ah_+0.5_away", 1.90, 0.02, 2, 0, -0.02)


# ===================================================================
# Test: Asian Handicap — Quarter Lines (CRITICAL — split math)
# ===================================================================


class TestAsianHandicapQuarterLines:
    """
    Quarter-line Asian Handicap split resolution.

    These are the mathematically critical edge cases for the ML target
    variable. Each quarter line (ending in .25 or .75) splits into
    two components with 50 % stake each.
    """

    # ═══════════════════════════════════════════════════════════════
    # AH -0.75 (Home -0.75) — splits into -0.5 (full) and -1.0 (half)
    # ═══════════════════════════════════════════════════════════════

    def test_ah_minus_0_75_win_by_2_full_win(self):
        """
        AH -0.75 HOME, win by 2 goals (3-1, goal_diff=2):

        eff = 2 + (-0.75) = 1.25
        Component A (-0.5): eff₁ = 1.25 + 0.25 = 1.50 > 0  →  WIN
        Component B (-1.0): eff₂ = 1.25 - 0.25 = 1.00 > 0  →  WIN

        Result: full win → profit = stake × (odds - 1)
        """
        _assert_profit("ah_-0.75_home", 2.00, 0.04, 3, 1, 0.04)

    def test_ah_minus_0_75_win_by_1_half_win(self):
        """
        AH -0.75 HOME, win by exactly 1 goal (2-1, goal_diff=1):

        eff = 1 + (-0.75) = 0.25
        Component A (-0.5): eff₁ = 0.25 + 0.25 = 0.50 > 0  →  WIN
        Component B (-1.0): eff₂ = 0.25 - 0.25 = 0.00     →  PUSH

        Result: half win → profit = 0.5 × stake × (odds - 1)
        """
        profit = 0.5 * 0.04 * (2.00 - 1.0)  # = 0.02
        _assert_profit("ah_-0.75_home", 2.00, 0.04, 2, 1, profit)

    def test_ah_minus_0_75_draw_full_loss(self):
        """
        AH -0.75 HOME, draw (1-1, goal_diff=0):

        eff = 0 + (-0.75) = -0.75
        Component A (-0.5): eff₁ = -0.75 + 0.25 = -0.50 < 0  →  LOSS
        Component B (-1.0): eff₂ = -0.75 - 0.25 = -1.00 < 0  →  LOSS

        Result: full loss → profit = -stake
        """
        _assert_profit("ah_-0.75_home", 2.00, 0.04, 1, 1, -0.04)

    def test_ah_minus_0_75_loss_full_loss(self):
        """
        AH -0.75 HOME, loss (0-2, goal_diff=-2):

        Both components lose → full loss
        """
        _assert_profit("ah_-0.75_home", 2.00, 0.04, 0, 2, -0.04)

    # ═══════════════════════════════════════════════════════════════
    # AH -0.25 (Home -0.25) — splits into 0.0 (full) and -0.5 (half)
    # ═══════════════════════════════════════════════════════════════

    def test_ah_minus_0_25_win_full_win(self):
        """
        AH -0.25 HOME, win by 1 (2-1, goal_diff=1):

        eff = 1 + (-0.25) = 0.75
        Component A (0.0):  eff₁ = 0.75 + 0.25 = 1.00 > 0  →  WIN
        Component B (-0.5): eff₂ = 0.75 - 0.25 = 0.50 > 0  →  WIN

        Result: full win
        """
        _assert_profit("ah_-0.25_home", 2.10, 0.03, 2, 1, 0.033)

    def test_ah_minus_0_25_draw_half_loss(self):
        """
        AH -0.25 HOME, draw (1-1, goal_diff=0):

        eff = 0 + (-0.25) = -0.25
        Component A (0.0):  eff₁ = -0.25 + 0.25 = 0.00     →  PUSH
        Component B (-0.5): eff₂ = -0.25 - 0.25 = -0.50 < 0  →  LOSS

        Result: half loss → profit = -0.5 × stake
        """
        _assert_profit("ah_-0.25_home", 2.10, 0.03, 1, 1, -0.015)

    def test_ah_minus_0_25_loss_full_loss(self):
        """
        AH -0.25 HOME, loss (0-2, goal_diff=-2):

        Both components lose → full loss
        """
        _assert_profit("ah_-0.25_home", 2.10, 0.03, 0, 2, -0.03)

    # ═══════════════════════════════════════════════════════════════
    # AH +0.25 (Home +0.25) — splits into +0.5 (full) and 0.0 (half)
    # ═══════════════════════════════════════════════════════════════

    def test_ah_plus_0_25_win_full_win(self):
        """
        AH +0.25 HOME, win (2-1, goal_diff=1):

        Both components win → full win
        """
        _assert_profit("ah_+0.25_home", 1.95, 0.04, 2, 1, 0.038)

    def test_ah_plus_0_25_draw_half_win(self):
        """
        AH +0.25 HOME, draw (1-1, goal_diff=0):

        eff = 0 + 0.25 = 0.25
        Component A (+0.5): eff₁ = 0.25 + 0.25 = 0.50 > 0  →  WIN
        Component B (0.0):  eff₂ = 0.25 - 0.25 = 0.00     →  PUSH

        Result: half win → profit = 0.5 × stake × (odds - 1)
        """
        profit = 0.5 * 0.04 * (1.95 - 1.0)  # = 0.019
        _assert_profit("ah_+0.25_home", 1.95, 0.04, 1, 1, profit)

    def test_ah_plus_0_25_loss_full_loss(self):
        """
        AH +0.25 HOME, loss (0-1, goal_diff=-1):

        Both components lose → full loss
        """
        _assert_profit("ah_+0.25_home", 1.95, 0.04, 0, 1, -0.04)

    # ═══════════════════════════════════════════════════════════════
    # AH +0.75 (Home +0.75) — splits into +1.0 (full) and +0.5 (half)
    # ═══════════════════════════════════════════════════════════════

    def test_ah_plus_0_75_win_full_win(self):
        """
        AH +0.75 HOME, win (2-1, goal_diff=1):

        Both components win → full win
        """
        _assert_profit("ah_+0.75_home", 2.00, 0.03, 2, 1, 0.03)

    def test_ah_plus_0_75_draw_full_win(self):
        """
        AH +0.75 HOME, draw (1-1, goal_diff=0):

        eff = 0 + 0.75 = 0.75
        Component A (+1.0): eff₁ = 0.75 + 0.25 = 1.00 > 0  →  WIN
        Component B (+0.5): eff₂ = 0.75 - 0.25 = 0.50 > 0  →  WIN

        Result: full win (home +0.75 covers draw)
        """
        _assert_profit("ah_+0.75_home", 2.00, 0.03, 1, 1, 0.03)

    def test_ah_plus_0_75_loss_by_1_half_loss(self):
        """
        AH +0.75 HOME, loss by exactly 1 goal (0-1, goal_diff=-1):

        eff = -1 + 0.75 = -0.25
        Component A (+1.0): eff₁ = -0.25 + 0.25 = 0.00     →  PUSH
        Component B (+0.5): eff₂ = -0.25 - 0.25 = -0.50 < 0  →  LOSS

        Result: half loss → profit = -0.5 × stake
        """
        _assert_profit("ah_+0.75_home", 2.00, 0.03, 0, 1, -0.015)

    def test_ah_plus_0_75_loss_by_2_full_loss(self):
        """
        AH +0.75 HOME, loss by 2 goals (0-2, goal_diff=-2):

        Both components lose → full loss
        """
        _assert_profit("ah_+0.75_home", 2.00, 0.03, 0, 2, -0.03)

    # ═══════════════════════════════════════════════════════════════
    # AWAY side quarter lines
    # ═══════════════════════════════════════════════════════════════

    def test_ah_minus_0_75_away_win_by_2_full_win(self):
        """
        AH -0.75 AWAY, away wins by 2 (0-2, goal_diff=-2):

        eff = -(-2) + (-0.75) = 2 - 0.75 = 1.25
        Both components win → full win
        """
        _assert_profit("ah_-0.75_away", 2.00, 0.03, 0, 2, 0.03)

    def test_ah_minus_0_75_away_win_by_1_half_win(self):
        """
        AH -0.75 AWAY, away wins by 1 (1-2, goal_diff=-1):

        eff = -(-1) + (-0.75) = 1 - 0.75 = 0.25
        Component A (-0.5): eff₁ = 0.50 > 0  → WIN
        Component B (-1.0): eff₂ = 0.00     → PUSH

        Result: half win
        """
        profit = 0.5 * 0.03 * (2.00 - 1.0)  # = 0.015
        _assert_profit("ah_-0.75_away", 2.00, 0.03, 1, 2, profit)

    def test_ah_minus_0_75_away_draw_full_loss(self):
        """AH -0.75 AWAY, draw → full loss"""
        _assert_profit("ah_-0.75_away", 2.00, 0.03, 1, 1, -0.03)

    def test_ah_plus_0_25_away_draw_half_win(self):
        """
        AH +0.25 AWAY, draw (1-1, goal_diff=0):

        eff = -0 + 0.25 = 0.25
        Component A (+0.5): eff₁ = 0.50 > 0  → WIN
        Component B (0.0):  eff₂ = 0.00     → PUSH

        Result: half win
        """
        profit = 0.5 * 0.02 * (2.10 - 1.0)  # = 0.011
        _assert_profit("ah_+0.25_away", 2.10, 0.02, 1, 1, profit)


# ===================================================================
# Test: _is_quarter_line
# ===================================================================


class TestIsQuarterLine:
    """Verify quarter-line detection."""

    def test_minus_1_0_is_not_quarter(self):
        assert not _is_quarter_line(-1.0)

    def test_minus_0_75_is_quarter(self):
        assert _is_quarter_line(-0.75)

    def test_minus_0_5_is_not_quarter(self):
        assert not _is_quarter_line(-0.5)

    def test_minus_0_25_is_quarter(self):
        assert _is_quarter_line(-0.25)

    def test_zero_is_not_quarter(self):
        assert not _is_quarter_line(0.0)

    def test_plus_0_25_is_quarter(self):
        assert _is_quarter_line(0.25)

    def test_plus_0_5_is_not_quarter(self):
        assert not _is_quarter_line(0.5)

    def test_plus_0_75_is_quarter(self):
        assert _is_quarter_line(0.75)

    def test_plus_1_0_is_not_quarter(self):
        assert not _is_quarter_line(1.0)

    def test_plus_1_25_is_quarter(self):
        assert _is_quarter_line(1.25)


# ===================================================================
# Test: Edge Cases
# ===================================================================


class TestEdgeCases:
    """Boundary conditions and error handling."""

    def test_zero_stake_returns_zero(self):
        """Stake of 0.0 → profit = 0.0 regardless of outcome."""
        _assert_profit("1x2_home", 2.00, 0.0, 5, 0, 0.0)

    def test_negative_stake_treated_as_zero(self):
        """Negative stake → 0.0 (guard clamps to 0)."""
        _assert_profit("1x2_home", 2.00, -0.01, 1, 0, 0.0)

    def test_unknown_market_key_raises_value_error(self):
        """Unrecognised market_key → ValueError."""
        with pytest.raises(ValueError, match="Unrecognised market_key"):
            calculate_profit("invalid_key", 2.0, 0.01, 0, 0)

    def test_case_insensitivity(self):
        """Market keys are case-insensitive (lowercased internally)."""
        _assert_profit("1X2_HOME", 2.00, 0.01, 1, 0, 0.01)
        _assert_profit("OVER_2.5", 2.00, 0.01, 3, 0, 0.01)
        _assert_profit("AH_-0.75_HOME", 2.00, 0.01, 2, 1, 0.005)

    def test_odds_at_exactly_1_0(self):
        """decimal_odds = 1.0 → profit = 0.0 on win (since odds-1 = 0)."""
        _assert_profit("1x2_home", 1.0, 0.01, 1, 0, 0.0)
