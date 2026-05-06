"""
Unit tests for the Betting API router (Phase 2 – API Integration).

Validates:
  1. ``GET /api/v1/betting/value-bets`` returns 200 with valid match_ids.
  2. Response payload includes ``recommended_stake_fraction`` from the
     Fractional Kelly Staking Engine.
  3. Empty / missing match_ids returns 400.
  4. No qualifying picks returns an empty list.
"""

import pytest
from unittest.mock import AsyncMock, patch
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.betting_routes import router
from app.schemas.betting_schemas import ValueBetResponse


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_picks() -> List[Dict[str, Any]]:
    """Simulates the result of ``evaluate_value_bets`` → ``top_picks``."""
    return [
        {
            "match_id": 27362,
            "market_key": "over_2.5",
            "odds": 2.10,
            "p_model": 0.58,
            "ev_final": 0.12,
            "recommended_stake_fraction": 0.035,  # 3.5 % of bankroll
        },
        {
            "match_id": 27363,
            "market_key": "1x2_home",
            "odds": 1.95,
            "p_model": 0.55,
            "ev_final": 0.08,
            "recommended_stake_fraction": 0.021,  # 2.1 % of bankroll
        },
        {
            "match_id": 27362,
            "market_key": "btts_yes",
            "odds": 2.05,
            "p_model": 0.62,
            "ev_final": 0.15,
            "recommended_stake_fraction": 0.042,  # 4.2 % of bankroll
        },
    ]


@pytest.fixture
def app() -> FastAPI:
    """Build a minimal FastAPI app that only includes the betting router."""
    application = FastAPI()
    application.include_router(router, prefix="/api/v1")
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """TestClient bound to the minimal app."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGetValueBets:
    """Suite: ``GET /api/v1/betting/value-bets``"""

    # ── Happy path ────────────────────────────────────────────────────

    @patch("app.api.betting_routes.evaluate_value_bets", new_callable=AsyncMock)
    def test_returns_value_bets_with_stake_fraction(
        self,
        mock_eval: AsyncMock,
        client: TestClient,
        mock_picks: List[Dict[str, Any]],
    ):
        """Valid match_ids → 200 OK + every pick has recommended_stake_fraction."""
        mock_eval.return_value = {
            "top_picks": mock_picks,
            "total_evaluated": len(mock_picks),
            "matches_processed": 2,
        }

        resp = client.get("/api/v1/betting/value-bets?match_ids=27362,27363")

        assert resp.status_code == 200, resp.text
        data: List[Dict[str, Any]] = resp.json()
        assert len(data) == 3

        for pick, expected in zip(data, mock_picks):
            assert pick["match_id"] == expected["match_id"]
            assert pick["market"] == expected["market_key"]
            assert pick["odds"] == expected["odds"]
            assert pick["p_model"] == expected["p_model"]
            assert pick["ev_final"] == expected["ev_final"]
            assert (
                pick["recommended_stake_fraction"]
                == expected["recommended_stake_fraction"]
            ), f"Missing or wrong stake fraction for {pick['market']}"

        # Verify the underlying service was called with the correct args
        mock_eval.assert_awaited_once()
        call_args = mock_eval.call_args[1]  # kwargs
        assert call_args["match_ids"] == [27362, 27363]

    # ── Single match id ──────────────────────────────────────────────

    @patch("app.api.betting_routes.evaluate_value_bets", new_callable=AsyncMock)
    def test_single_match_id(
        self,
        mock_eval: AsyncMock,
        client: TestClient,
    ):
        """Single match_id → 200 OK with one matching pick."""
        mock_eval.return_value = {
            "top_picks": [
                {
                    "match_id": 100,
                    "market_key": "under_2.5",
                    "odds": 1.85,
                    "p_model": 0.52,
                    "ev_final": 0.07,
                    "recommended_stake_fraction": 0.018,
                }
            ],
            "total_evaluated": 1,
            "matches_processed": 1,
        }

        resp = client.get("/api/v1/betting/value-bets?match_ids=100")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["recommended_stake_fraction"] == 0.018

    # ── Empty / missing match_ids ────────────────────────────────────

    @patch("app.api.betting_routes.evaluate_value_bets", new_callable=AsyncMock)
    def test_empty_match_ids_returns_400(
        self,
        mock_eval: AsyncMock,
        client: TestClient,
    ):
        """Empty string → 400 because no integers to parse."""
        resp = client.get("/api/v1/betting/value-bets?match_ids=")
        assert resp.status_code == 400
        assert "match_ids" in resp.json()["detail"].lower()

    def test_missing_match_ids_returns_422(self, client: TestClient):
        """Omitting match_ids param → 422 validation error."""
        resp = client.get("/api/v1/betting/value-bets")
        assert resp.status_code == 422

    # ── No qualifying picks ──────────────────────────────────────────

    @patch("app.api.betting_routes.evaluate_value_bets", new_callable=AsyncMock)
    def test_no_qualifying_picks_returns_empty_list(
        self,
        mock_eval: AsyncMock,
        client: TestClient,
    ):
        """No top_picks → empty JSON array ``[]``."""
        mock_eval.return_value = {
            "top_picks": [],
            "total_evaluated": 0,
            "matches_processed": 0,
        }

        resp = client.get("/api/v1/betting/value-bets?match_ids=99999")
        assert resp.status_code == 200
        assert resp.json() == []

    # ── Response schema conformity ───────────────────────────────────

    @patch("app.api.betting_routes.evaluate_value_bets", new_callable=AsyncMock)
    def test_response_matches_value_bet_response_schema(
        self,
        mock_eval: AsyncMock,
        client: TestClient,
        mock_picks: List[Dict[str, Any]],
    ):
        """Each element can be deserialised into ``ValueBetResponse``."""
        mock_eval.return_value = {
            "top_picks": mock_picks,
            "total_evaluated": len(mock_picks),
            "matches_processed": 2,
        }

        resp = client.get("/api/v1/betting/value-bets?match_ids=27362,27363")
        assert resp.status_code == 200

        for item in resp.json():
            # Pydantic validation will raise if shape is wrong
            validated = ValueBetResponse(**item)
            assert validated.recommended_stake_fraction >= 0.0


class TestValueBetResponseSchema:
    """Unit-level validation of the ``ValueBetResponse`` model."""

    def test_valid_values(self):
        """All fields populated → constructs cleanly."""
        obj = ValueBetResponse(
            match_id=42,
            market="over_2.5",
            odds=2.10,
            p_model=0.58,
            ev_final=0.12,
            recommended_stake_fraction=0.035,
        )
        assert obj.match_id == 42
        assert obj.recommended_stake_fraction == 0.035

    def test_zero_stake_on_low_ev(self):
        """Stake can be 0.0 for low/no EV picks."""
        obj = ValueBetResponse(
            match_id=42,
            market="over_2.5",
            odds=1.50,
            p_model=0.30,
            ev_final=-0.02,
            recommended_stake_fraction=0.0,
        )
        assert obj.recommended_stake_fraction == 0.0

    def test_minimal_required_fields_only(self):
        """No optional extras → still constructs."""
        obj = ValueBetResponse(
            match_id=1,
            market="test",
            odds=1.0,
            p_model=0.5,
            ev_final=0.0,
            recommended_stake_fraction=0.0,
        )
        assert obj.match_id == 1
