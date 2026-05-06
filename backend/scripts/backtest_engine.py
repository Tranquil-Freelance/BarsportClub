#!/usr/bin/env python
"""
Backtesting Engine — Phase 9
==============================
Standalone script for the Risk Manager to evaluate historical ROI of the
Fractional Kelly strategy versus a Flat Stake strategy.

Data source
-----------
``bets`` table where ``status = 'SETTLED'``, ordered by ``placed_at ASC``.

Simulation
----------
Two portfolios are evaluated side-by-side on the exact same bet sequence:

**Portfolio A (Flat Stake)**
    Stakes exactly **$100** per bet regardless of bankroll size.

**Portfolio B (Fractional Kelly)**
    Uses the actual ``stake`` (fraction of bankroll) and ``profit`` stored in
    the database, simulated dynamically starting from an initial bankroll of
    **$10,000**.  The Kelly portfolio's actual P&L at each step is:

        dollar_stake   = current_bankroll × DB_stake_fraction
        dollar_profit  = current_bankroll × DB_profit_fraction   (if win)
        dollar_profit  = −current_bankroll × DB_stake_fraction   (if loss)
        bankroll      += dollar_profit

Metrics reported
----------------
- Total Bets Placed
- Win Rate (Hits / Total)
- ROI % for Flat Stake
- ROI % for Kelly Stake
- Maximum Drawdown % for Kelly Stake

Usage
-----
From the ``backend/`` directory::

    .\\venv312\\Scripts\\python.exe scripts\\backtest_engine.py

Exit codes
----------
0 — success
1 — unexpected error
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass, field
from typing import List, Optional

from sqlalchemy import create_engine, text

# Ensure the backend package is importable
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from app.core.config import settings  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("backtest_engine")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FLAT_STAKE_AMOUNT: float = 100.0
"""Absolute dollar amount staked per bet in the Flat portfolio."""

INITIAL_BANKROLL: float = 10_000.0
"""Starting bankroll for the Kelly portfolio simulation."""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class SettledBetRow:
    """A single row from the ``bets`` table after settlement."""

    match_id: Optional[int]
    market_key: str
    decimal_odds: float
    stake_frac: float  # Fraction of bankroll wagered (e.g. 0.02 = 2 %)
    profit_frac: float  # Net profit / loss as fraction of bankroll
    placed_at: str  # ISO datetime string


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_settled_bets(db_url: str) -> List[SettledBetRow]:
    """
    Load all settled bets ordered chronologically.

    Converts the async driver URI to a sync one (``+asyncpg`` → ``+psycopg2``)
    since this is a standalone script.
    """
    sync_url = db_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)

    query = text("""
        SELECT
            match_id,
            market_key,
            decimal_odds,
            stake,
            profit,
            placed_at::text
        FROM bets
        WHERE status = 'SETTLED'
        ORDER BY placed_at ASC, id ASC
    """)

    rows: List[SettledBetRow] = []

    try:
        with engine.connect() as conn:
            result = conn.execute(query)
            for r in result:
                # Filter out rows with missing data
                profit_val = r[4]
                stake_val = r[3]
                odds_val = r[2]

                if profit_val is None or stake_val is None or odds_val is None:
                    continue
                if stake_val <= 0.0:
                    continue

                rows.append(
                    SettledBetRow(
                        match_id=r[0],
                        market_key=str(r[1]),
                        decimal_odds=float(odds_val),
                        stake_frac=float(stake_val),
                        profit_frac=float(profit_val),
                        placed_at=str(r[5] or ""),
                    )
                )
    except Exception as exc:
        logger.error("Failed to load settled bets: %s", exc)
        raise
    finally:
        engine.dispose()

    return rows


# ---------------------------------------------------------------------------
# Portfolio simulation
# ---------------------------------------------------------------------------


@dataclass
class SimulationResult:
    """Aggregated backtest metrics."""

    total_bets: int = 0
    wins: int = 0
    losses: int = 0
    pushes: int = 0
    flat_final_pnl: float = 0.0
    flat_roi_pct: float = 0.0
    kelly_final_bankroll: float = INITIAL_BANKROLL
    kelly_roi_pct: float = 0.0
    kelly_max_drawdown_pct: float = 0.0
    """
    Maximum drawdown percentage for the Kelly portfolio — the largest peak-to-
    trough decline in bankroll over the simulation period.
    """


def simulate(bets: List[SettledBetRow]) -> SimulationResult:
    """
    Run the dual-portfolio simulation over the full bet sequence.

    Parameters
    ----------
    bets : list of SettledBetRow
        Chronologically ordered settled bets.

    Returns
    -------
    SimulationResult
        Aggregated metrics for both portfolios.
    """
    result = SimulationResult()
    result.total_bets = len(bets)

    # ── Portfolio A: Flat Stake ($100 per bet) ───────────────────────────
    flat_cumulative_pnl = 0.0

    # ── Portfolio B: Fractional Kelly ($10,000 initial bankroll) ─────────
    kelly_bankroll = INITIAL_BANKROLL
    peak_bankroll = INITIAL_BANKROLL
    max_drawdown = 0.0  # Absolute dollar drawdown

    for bet in bets:
        # ── Determine outcome ────────────────────────────────────────────
        if bet.profit_frac > 0.0:
            result.wins += 1
        elif bet.profit_frac < 0.0:
            result.losses += 1
        else:
            result.pushes += 1

        # ── Flat stake P&L ──────────────────────────────────────────────
        if bet.profit_frac > 0.0:
            # Win: profit = stake × (odds - 1)
            flat_pnl = FLAT_STAKE_AMOUNT * (bet.decimal_odds - 1.0)
        elif bet.profit_frac < 0.0:
            # Loss: lose the stake
            flat_pnl = -FLAT_STAKE_AMOUNT
        else:
            # Push / void: stake returned
            flat_pnl = 0.0

        flat_cumulative_pnl += flat_pnl

        # ── Kelly P&L ───────────────────────────────────────────────────
        # The stored profit_frac is computed as:
        #   profit_frac = stake_frac × (odds - 1)   for wins
        #   profit_frac = -stake_frac                for losses
        # To convert to absolute dollars, multiply by current bankroll.
        # BUT: profit_frac is already relative to the bankroll at placement
        # time. The actual dollar P&L = profit_frac × bankroll_before.
        # Since we're simulating dynamically, we use the current bankroll.
        kelly_dollar_profit = bet.profit_frac * kelly_bankroll
        kelly_bankroll += kelly_dollar_profit

        # ── Track peak and drawdown ─────────────────────────────────────
        if kelly_bankroll > peak_bankroll:
            peak_bankroll = kelly_bankroll

        current_drawdown = peak_bankroll - kelly_bankroll
        if current_drawdown > max_drawdown:
            max_drawdown = current_drawdown

    # ── Compute final metrics ────────────────────────────────────────────
    total_invested_flat = FLAT_STAKE_AMOUNT * result.total_bets

    result.flat_final_pnl = round(flat_cumulative_pnl, 2)
    if total_invested_flat > 0:
        result.flat_roi_pct = round(
            (flat_cumulative_pnl / total_invested_flat) * 100, 2
        )
    else:
        result.flat_roi_pct = 0.0

    result.kelly_final_bankroll = round(kelly_bankroll, 2)
    total_kelly_invested = INITIAL_BANKROLL  # Not truly "invested" but this
    # is the reference for ROI calculation.
    result.kelly_roi_pct = round(
        ((kelly_bankroll - INITIAL_BANKROLL) / INITIAL_BANKROLL) * 100, 2
    )

    if peak_bankroll > 0:
        result.kelly_max_drawdown_pct = round(
            (max_drawdown / peak_bankroll) * 100, 2
        )
    else:
        result.kelly_max_drawdown_pct = 0.0

    return result


# ---------------------------------------------------------------------------
# Terminal report
# ---------------------------------------------------------------------------


def print_report(result: SimulationResult) -> None:
    """
    Print a clean, formatted terminal report of backtest metrics.
    """
    win_rate = (
        round((result.wins / result.total_bets) * 100, 2)
        if result.total_bets > 0
        else 0.0
    )

    sep = "=" * 60
    dash = "-" * 60

    print()
    print(sep)
    print("   🧪  BACKTESTING REPORT — STRATEGY PERFORMANCE  🧪")
    print(sep)
    print(f"   Generated:    {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(dash)
    print()
    print("   📊  GENERAL STATISTICS")
    print(dash)
    print(f"      Total Bets Placed:         {result.total_bets}")
    print(f"      Wins (Hits):               {result.wins}")
    print(f"      Losses:                    {result.losses}")
    print(f"      Pushes / Voids:            {result.pushes}")
    print(f"      Win Rate:                  {win_rate} %")
    print()
    print(dash)
    print("   💰  PORTFOLIO A — FLAT STAKE ($100/BET)")
    print(dash)
    print(f"      Total Wagered:             ${FLAT_STAKE_AMOUNT * result.total_bets:,.2f}")
    print(f"      Net Profit / Loss:         ${result.flat_final_pnl:+,.2f}")
    print(f"      ROI:                       {result.flat_roi_pct:+.2f} %")
    print()
    print(dash)
    print("   📈  PORTFOLIO B — FRACTIONAL KELLY ($10,000 INITIAL)")
    print(dash)
    print(f"      Final Bankroll:            ${result.kelly_final_bankroll:,.2f}")
    print(f"      Net Profit / Loss:         ${result.kelly_final_bankroll - INITIAL_BANKROLL:+,.2f}")
    print(f"      ROI:                       {result.kelly_roi_pct:+.2f} %")
    print(f"      Maximum Drawdown:          {result.kelly_max_drawdown_pct:.2f} %")
    print()
    print(sep)
    print("   📋  VERDICT")
    print(sep)
    if result.kelly_roi_pct > result.flat_roi_pct:
        print(f"      ✅ Fractional Kelly outperforms Flat Stake by "
              f"{result.kelly_roi_pct - result.flat_roi_pct:+.2f} % ROI.")
    elif result.kelly_roi_pct < result.flat_roi_pct:
        print(f"      ❌ Flat Stake outperforms Fractional Kelly by "
              f"{result.flat_roi_pct - result.kelly_roi_pct:+.2f} % ROI.")
    else:
        print("      ⚖️  Both strategies performed identically.")
    print(
        f"      Maximum Kelly Drawdown:    {result.kelly_max_drawdown_pct:.2f} % "
        f"(Risk of ruin indicator)."
    )
    print(sep)
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Orchestrate the backtest: load → simulate → report."""
    db_url: str = settings.SQLALCHEMY_DATABASE_URI
    logger.info("Loading settled bets from database...")

    bets = load_settled_bets(db_url)
    logger.info("Loaded %d settled bet(s).", len(bets))

    if not bets:
        logger.warning("No settled bets found — cannot run backtest.")
        print("\n⚠️  No settled bets in the database. Backtest skipped.\n")
        return

    logger.info("Running dual-portfolio simulation...")
    result = simulate(bets)

    print_report(result)

    logger.info("Backtest complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Fatal error in backtest engine")
        sys.exit(1)
