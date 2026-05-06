"""
Bet Settlement Service — Phase 6
===================================
Closes out open bets after a match finishes by:

1. Fetching all ``OPEN`` bets for the given ``match_id``.
2. Computing exact profit/loss via :func:`settlement_math.calculate_profit`.
3. Updating each bet's ``profit``, ``status`` → ``'SETTLED'``, and ``settled_at``.
4. Updating the corresponding ``features_log.outcome_profit`` (the ML target
   variable ``y``).

All writes are wrapped in a single atomic transaction with rollback on
failure, following the same safety pattern as
:mod:`app.services.tracking_service`.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.settlement_math import calculate_profit

logger = logging.getLogger(__name__)


async def settle_match_bets(
    session: AsyncSession,
    match_id: int,
    home_goals: int,
    away_goals: int,
) -> int:
    """
    Settle all open bets for a finished match.

    Parameters
    ----------
    session : AsyncSession
        Active database session.
    match_id : int
        ``matchcalendar.id`` of the completed match.
    home_goals : int
        Actual goals scored by the home team.
    away_goals : int
        Actual goals scored by the away team.

    Returns
    -------
    int
        Number of bets settled (0 if none were open).

    Raises
    ------
    Exception
        Re-raised after rollback on any DB failure.
    """
    # ── Step 1: Fetch OPEN bets for this match ──────────────────────────
    fetch_query = text("""
        SELECT id, market_key, decimal_odds, stake
        FROM bets
        WHERE match_id = :match_id
          AND status = 'OPEN'
        FOR UPDATE
    """)

    update_bet_query = text("""
        UPDATE bets
        SET profit      = :profit,
            status      = 'SETTLED',
            settled_at  = :settled_at
        WHERE id = :bet_id
    """)

    update_features_query = text("""
        UPDATE features_log
        SET outcome_profit = :outcome_profit
        WHERE match_id = :match_id
          AND market_key = :market_key
    """)

    now = datetime.now(timezone.utc)
    settled_count = 0

    try:
        # ── Fetch open bets with row-level lock ─────────────────────────
        result = await session.execute(fetch_query, {"match_id": match_id})
        rows = result.fetchall()

        if not rows:
            logger.info("settle_match_bets: no OPEN bets for match_id=%s", match_id)
            return 0

        logger.info(
            "settle_match_bets: settling %d bet(s) for match_id=%s (%d–%d)",
            len(rows), match_id, home_goals, away_goals,
        )

        for row in rows:
            bet_id: int = row[0]
            market_key: str = row[1]
            decimal_odds: float = row[2]
            stake: float = row[3] or 0.0

            # ── Step 2: Compute profit ──────────────────────────────────
            try:
                profit = calculate_profit(
                    market_key=market_key,
                    decimal_odds=decimal_odds,
                    stake=stake,
                    home_goals=home_goals,
                    away_goals=away_goals,
                )
            except (ValueError, ZeroDivisionError) as exc:
                logger.warning(
                    "settle_match_bets: calculate_profit failed for bet_id=%s "
                    "(market=%s, odds=%s, stake=%s): %s",
                    bet_id, market_key, decimal_odds, stake, exc,
                )
                # Treat unresolvable bets as void (profit = 0.0)
                profit = 0.0

            # ── Step 3: Update bets table ───────────────────────────────
            await session.execute(
                update_bet_query,
                {
                    "profit": round(profit, 6),
                    "settled_at": now,
                    "bet_id": bet_id,
                },
            )

            # ── Step 4: Update features_log (target variable y) ────────
            await session.execute(
                update_features_query,
                {
                    "outcome_profit": round(profit, 6),
                    "match_id": match_id,
                    "market_key": market_key,
                },
            )

            settled_count += 1

        # ── Step 5: Commit transaction ──────────────────────────────────
        await session.commit()
        logger.info(
            "settle_match_bets: committed %d settlements for match_id=%s",
            settled_count, match_id,
        )

    except Exception:
        await session.rollback()
        logger.exception(
            "settle_match_bets: transaction rolled back for match_id=%s",
            match_id,
        )
        raise

    return settled_count
