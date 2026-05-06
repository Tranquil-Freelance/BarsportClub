"""
Unit tests for the Data Tracking & Feature Logging Service (Phase 5).

Validates:
  1. ``log_features`` inserts a ``FeaturesLog`` record with correct field mapping.
  2. ``log_bet`` inserts a ``Bet`` record with correct stake calculation.
  3. Error handling rolls back and re-raises on DB write failure.
  4. Edge cases: zero stake, missing optional features, None values.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Bet, FeaturesLog
from app.services.tracking_service import (
    HYPOTHETICAL_BANKROLL,
    log_bet,
    log_features,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a fully mocked AsyncSession with add, commit, rollback attrs."""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def sample_features() -> Dict[str, Any]:
    """A realistic feature vector as produced by the pipeline."""
    return {
        "lambda_home": 1.45,
        "lambda_away": 1.12,
        "p_model": 0.58,
        "p_book": 0.4762,
        "ev_base": 0.1245,
        "team_strength_home": 0.32,
        "team_strength_away": -0.15,
        "stability_home": 1.2,
        "stability_away": 0.9,
        "odds": 2.10,
    }


@pytest.fixture
def sample_bet_params() -> Dict[str, Any]:
    """Typical bet parameters sourced from a ValueBetResponse."""
    return {
        "match_id": 27362,
        "market_key": "over_2.5",
        "odds": 2.10,
        "p_model": 0.58,
        "ev_final": 0.12,
        "recommended_stake_fraction": 0.035,  # 3.5 % of bankroll
    }


# ---------------------------------------------------------------------------
# Test: log_features
# ---------------------------------------------------------------------------


class TestLogFeatures:
    """Suite: ``log_features(session, match_id, market_key, features)``"""

    # ──────────────────────────────────────────────────────────────────────
    # Happy path — full feature vector
    # ──────────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_inserts_features_log_record_with_correct_mapping(
        self,
        mock_session: AsyncMock,
        sample_features: Dict[str, Any],
    ):
        """
        Given a full feature dict, ``log_features`` must:
          - call ``session.add()`` with a ``FeaturesLog`` instance
          - call ``session.commit()`` once
          - set every column on the ORM object from the matching feature key
        """
        match_id = 27362
        market_key = "over_2.5"

        # Execute
        await log_features(
            session=mock_session,
            match_id=match_id,
            market_key=market_key,
            features=sample_features,
        )

        # Assert session.add was called once
        mock_session.add.assert_called_once()
        record: FeaturesLog = mock_session.add.call_args[0][0]

        # Assert it's a FeaturesLog instance
        assert isinstance(record, FeaturesLog), (
            f"Expected FeaturesLog instance, got {type(record)}"
        )

        # Assert field-level mapping
        assert record.match_id == match_id
        assert record.market_key == market_key
        assert record.lambda_home == sample_features["lambda_home"]
        assert record.lambda_away == sample_features["lambda_away"]
        assert record.p_model == sample_features["p_model"]
        assert record.p_book == sample_features["p_book"]
        assert record.ev_base == sample_features["ev_base"]
        assert record.team_strength_home == sample_features["team_strength_home"]
        assert record.team_strength_away == sample_features["team_strength_away"]
        assert record.stability_home == sample_features["stability_home"]
        assert record.stability_away == sample_features["stability_away"]
        assert record.odds == sample_features["odds"]

        # Assert commit was called
        mock_session.commit.assert_awaited_once()

    # ──────────────────────────────────────────────────────────────────────
    # Partial feature vector (None for optional fields)
    # ──────────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_partial_features_handles_missing_keys_gracefully(
        self,
        mock_session: AsyncMock,
    ):
        """
        A sparse feature dict with only ``p_model`` and ``odds`` set
        should not raise — missing keys default to ``None``.
        """
        sparse = {
            "p_model": 0.55,
            "odds": 1.95,
        }

        await log_features(
            session=mock_session,
            match_id=100,
            market_key="1x2_home",
            features=sparse,
        )

        record: FeaturesLog = mock_session.add.call_args[0][0]
        assert record.match_id == 100
        assert record.market_key == "1x2_home"
        assert record.p_model == 0.55
        assert record.odds == 1.95
        # Missing keys should be None
        assert record.lambda_home is None
        assert record.lambda_away is None
        assert record.p_book is None
        assert record.ev_base is None
        assert record.team_strength_home is None
        assert record.team_strength_away is None
        assert record.stability_home is None
        assert record.stability_away is None

        mock_session.commit.assert_awaited_once()

    # ──────────────────────────────────────────────────────────────────────
    # DB write failure → rollback + re-raise
    # ──────────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_db_write_failure_rollbacks_and_reraises(
        self,
        mock_session: AsyncMock,
        sample_features: Dict[str, Any],
    ):
        """
        When ``session.commit()`` raises an exception:
          - ``session.rollback()`` must be called
          - The exception must propagate to the caller.
        """
        mock_session.commit.side_effect = Exception("Connection lost")

        with pytest.raises(Exception, match="Connection lost"):
            await log_features(
                session=mock_session,
                match_id=1,
                market_key="test",
                features=sample_features,
            )

        mock_session.rollback.assert_awaited_once()
        # add() should have been called before the crash
        mock_session.add.assert_called_once()


# ---------------------------------------------------------------------------
# Test: log_bet
# ---------------------------------------------------------------------------


class TestLogBet:
    """Suite: ``log_bet(session, match_id, market_key, odds, p_model, ev_final, recommended_stake_fraction)``"""

    # ──────────────────────────────────────────────────────────────────────
    # Happy path — positive stake
    # ──────────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_inserts_bet_record_with_correct_stake(
        self,
        mock_session: AsyncMock,
        sample_bet_params: Dict[str, Any],
    ):
        """
        With a positive stake fraction, ``log_bet`` must:
          - call ``session.add()`` with a ``Bet`` instance
          - set correct field mapping
          - calculate ``bankroll_after`` = bankroll - (bankroll * stake_frac)
          - set status to ``OPEN``
        """
        await log_bet(
            session=mock_session,
            **sample_bet_params,
        )

        mock_session.add.assert_called_once()
        record: Bet = mock_session.add.call_args[0][0]

        assert isinstance(record, Bet), (
            f"Expected Bet instance, got {type(record)}"
        )

        # Field mapping
        assert record.match_id == sample_bet_params["match_id"]
        assert record.market_key == sample_bet_params["market_key"]
        assert record.decimal_odds == sample_bet_params["odds"]
        assert record.p_model == sample_bet_params["p_model"]
        assert record.ev == sample_bet_params["ev_final"]

        # Stake calculation
        frac = sample_bet_params["recommended_stake_fraction"]  # 0.035
        expected_stake_amount = round(HYPOTHETICAL_BANKROLL * frac, 2)  # $350
        expected_bankroll_after = round(HYPOTHETICAL_BANKROLL - expected_stake_amount, 2)  # $9,650

        assert record.stake == frac
        assert record.bankroll_before == HYPOTHETICAL_BANKROLL
        assert record.bankroll_after == expected_bankroll_after

        # Status
        assert record.status == "OPEN"

        mock_session.commit.assert_awaited_once()

    # ──────────────────────────────────────────────────────────────────────
    # Zero stake (no bet)
    # ──────────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_zero_stake_sets_bankroll_after_equal_to_before(
        self,
        mock_session: AsyncMock,
    ):
        """
        When ``recommended_stake_fraction == 0.0`` (no bet):
          - ``stake`` = 0.0
          - ``bankroll_after`` = ``bankroll_before`` (no change)
        """
        await log_bet(
            session=mock_session,
            match_id=42,
            market_key="under_2.5",
            odds=1.95,
            p_model=0.52,
            ev_final=0.07,
            recommended_stake_fraction=0.0,
        )

        record: Bet = mock_session.add.call_args[0][0]
        assert record.stake == 0.0
        assert record.bankroll_after == record.bankroll_before  # $10,000 = $10,000
        assert record.status == "OPEN"

    # ──────────────────────────────────────────────────────────────────────
    # Custom bankroll
    # ──────────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_custom_bankroll_parameter(
        self,
        mock_session: AsyncMock,
    ):
        """
        Passing an explicit ``bankroll`` should override the default
        ``HYPOTHETICAL_BANKROLL``.
        """
        custom_bankroll = 5000.0
        stake_frac = 0.04  # 4 %
        expected_stake_abs = round(custom_bankroll * stake_frac, 2)  # $200
        expected_after = round(custom_bankroll - expected_stake_abs, 2)  # $4,800

        await log_bet(
            session=mock_session,
            match_id=10,
            market_key="btts_yes",
            odds=2.05,
            p_model=0.62,
            ev_final=0.15,
            recommended_stake_fraction=stake_frac,
            bankroll=custom_bankroll,
        )

        record: Bet = mock_session.add.call_args[0][0]
        assert record.bankroll_before == custom_bankroll
        assert record.bankroll_after == expected_after
        assert record.stake == stake_frac

    # ──────────────────────────────────────────────────────────────────────
    # DB write failure → rollback + re-raise
    # ──────────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_db_write_failure_rollbacks_and_reraises(
        self,
        mock_session: AsyncMock,
        sample_bet_params: Dict[str, Any],
    ):
        """When ``session.commit()`` fails → rollback + re-raise."""
        mock_session.commit.side_effect = Exception("Disk full")

        with pytest.raises(Exception, match="Disk full"):
            await log_bet(
                session=mock_session,
                **sample_bet_params,
            )

        mock_session.rollback.assert_awaited_once()
        mock_session.add.assert_called_once()
