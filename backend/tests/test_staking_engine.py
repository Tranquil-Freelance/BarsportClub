"""
Unit tests for the Fractional Kelly Criterion Staking Engine.

Validates:
  1. Standard +EV bet → correct fractional stake.
  2. Negative EV bet  → exactly 0.0.
  3. Extremely high EV → strictly capped at 0.05 (5 %).
  4. Extremely low EV below 0.5 % threshold → 0.0.
"""

import pytest
from app.services.staking_engine import (
    calculate_kelly_fraction,
    MAX_STAKE_FRACTION,
    MIN_STAKE_FRACTION,
    DEFAULT_KELLY_FRACTION,
)


class TestCalculateKellyFraction:
    """
    Suite: ``calculate_kelly_fraction(p_model, decimal_odds, fraction)``
    """

    # ──────────────────────────────────────────────────────────────
    # Test 1 — Standard +EV bet
    # ──────────────────────────────────────────────────────────────

    def test_standard_positive_ev_returns_correct_fractional_stake(self):
        """
        A typical +EV scenario:
          p_model = 0.55  (55 % chance)
          decimal_odds = 2.10  (implied probability ~47.6 %)
          fraction = 0.25  (25 % Kelly)

        Full Kelly = (b * p - q) / b
          b = 2.10 - 1.0 = 1.10
          q = 1.0 - 0.55 = 0.45
          full_kelly = (1.10 * 0.55 - 0.45) / 1.10
                     = (0.605 - 0.45) / 1.10
                     = 0.155 / 1.10
                     = 0.140909...
          target = 0.140909 * 0.25 = 0.035227...
          min cap: 0.035227 >= 0.005  ✓
          max cap: min(0.035227, 0.05) = 0.035227
        """
        result = calculate_kelly_fraction(
            p_model=0.55,
            decimal_odds=2.10,
            fraction=0.25,
        )

        # Expected: 0.035227...  (above min, below max)
        assert 0.03 < result < 0.04, (
            f"Expected stake ~0.0352, got {result}"
        )
        assert result <= MAX_STAKE_FRACTION, (
            f"Stake {result} exceeds max cap {MAX_STAKE_FRACTION}"
        )

    # ──────────────────────────────────────────────────────────────
    # Test 2 — Negative EV bet
    # ──────────────────────────────────────────────────────────────

    def test_negative_ev_returns_zero(self):
        """
        A -EV scenario:
          p_model = 0.40  (40 % chance)
          decimal_odds = 2.10  (fair value would be ~2.50)

        b = 2.10 - 1.0 = 1.10
        q = 1.0 - 0.40 = 0.60
        full_kelly = (1.10 * 0.40 - 0.60) / 1.10
                   = (0.44 - 0.60) / 1.10
                   = -0.16 / 1.10
                   = -0.145454...  (negative)
        """
        result = calculate_kelly_fraction(
            p_model=0.40,
            decimal_odds=2.10,
        )
        assert result == 0.0, (
            f"Expected 0.0 for -EV bet, got {result}"
        )

    # ──────────────────────────────────────────────────────────────
    # Test 3 — Extremely high EV → capped at MAX_STAKE_FRACTION
    # ──────────────────────────────────────────────────────────────

    def test_extreme_high_ev_capped_at_max(self):
        """
        An extremely high EV scenario that would exceed the 5 % max cap:
          p_model = 0.80  (80 % chance — huge edge)
          decimal_odds = 3.00  (implied probability ~33.3 %)

        b = 3.00 - 1.0 = 2.00
        q = 1.0 - 0.80 = 0.20
        full_kelly = (2.00 * 0.80 - 0.20) / 2.00
                   = (1.60 - 0.20) / 2.00
                   = 1.40 / 2.00
                   = 0.70
        target = 0.70 * 0.25 = 0.175
        max cap: min(0.175, 0.05) = 0.05
        """
        result = calculate_kelly_fraction(
            p_model=0.80,
            decimal_odds=3.00,
        )
        assert result == MAX_STAKE_FRACTION, (
            f"Expected {MAX_STAKE_FRACTION} (max cap), got {result}"
        )

    # ──────────────────────────────────────────────────────────────
    # Test 4 — Extremely low EV below min threshold
    # ──────────────────────────────────────────────────────────────

    def test_extreme_low_ev_below_min_threshold_returns_zero(self):
        """
        An EV so low that the fractional target sits below 0.5 %:
          p_model = 0.52
          decimal_odds = 1.95  (fair implied prob ~51.3%)
          fraction = 0.25

        b = 1.95 - 1.0 = 0.95
        q = 1.0 - 0.52 = 0.48
        full_kelly = (0.95 * 0.52 - 0.48) / 0.95
                   = (0.494 - 0.48) / 0.95
                   = 0.014 / 0.95
                   = 0.014736...
        target = 0.014736 * 0.25 = 0.003684...
        min cap: 0.003684 < 0.005  →  return 0.0
        """
        result = calculate_kelly_fraction(
            p_model=0.52,
            decimal_odds=1.95,
        )
        assert result == 0.0, (
            f"Expected 0.0 for sub-threshold stake, got {result}"
        )

    # ──────────────────────────────────────────────────────────────
    # Edge Cases
    # ──────────────────────────────────────────────────────────────

    def test_odds_equal_to_one_returns_zero(self):
        """decimal_odds == 1.0 means no possible profit → 0.0."""
        result = calculate_kelly_fraction(p_model=0.99, decimal_odds=1.0)
        assert result == 0.0

    def test_odds_below_one_returns_zero(self):
        """decimal_odds < 1.0 is impossible → 0.0."""
        result = calculate_kelly_fraction(p_model=0.50, decimal_odds=0.5)
        assert result == 0.0

    def test_full_kelly_fraction_returns_higher_stake(self):
        """
        Using fraction=1.0 (full Kelly) on a moderate +EV bet
        should return higher than the 0.25 fractional version,
        but still respect the max cap.
        """
        full_result = calculate_kelly_fraction(
            p_model=0.55,
            decimal_odds=2.10,
            fraction=1.0,  # full Kelly
        )
        quarter_result = calculate_kelly_fraction(
            p_model=0.55,
            decimal_odds=2.10,
            fraction=0.25,
        )
        assert full_result > quarter_result, (
            f"Full Kelly ({full_result}) should exceed quarter Kelly ({quarter_result})"
        )
        assert full_result <= MAX_STAKE_FRACTION

    def test_p_model_of_one_with_fair_odds(self):
        """
        p_model = 1.0 (certainty), decimal_odds = 1.01 (slight edge).
        b = 0.01, q = 0.0
        full_kelly = (0.01 * 1.0 - 0.0) / 0.01 = 1.0
        target = 1.0 * 0.25 = 0.25
        max cap: min(0.25, 0.05) = 0.05
        """
        result = calculate_kelly_fraction(p_model=1.0, decimal_odds=1.01)
        assert result == MAX_STAKE_FRACTION

    def test_p_model_of_zero_returns_zero(self):
        """p_model = 0.0 means no chance → 0.0."""
        result = calculate_kelly_fraction(p_model=0.0, decimal_odds=2.0)
        assert result == 0.0

    def test_custom_fraction_applied_correctly(self):
        """
        With fraction=0.5 (50% Kelly) and a moderate edge,
        the result should be double the 0.25 Kelly result
        (provided it stays within caps).
        """
        p, odds = 0.58, 2.00
        r_half = calculate_kelly_fraction(p, odds, fraction=0.5)
        r_quarter = calculate_kelly_fraction(p, odds, fraction=0.25)
        # Should be roughly double
        assert abs(r_half - 2 * r_quarter) < 1e-10 or r_half == MAX_STAKE_FRACTION, (
            f"Half Kelly ({r_half}) should be ~2x quarter Kelly ({r_quarter})"
        )
