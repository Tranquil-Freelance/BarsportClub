"""
Pydantic schemas for the Betting API endpoints.
"""

from pydantic import BaseModel, Field


class ValueBetResponse(BaseModel):
    """Response schema for a single value bet pick.

    This is the structured payload returned by ``GET /api/v1/betting/value-bets``.
    It includes the output of the Fractional Kelly Staking Engine so that
    downstream consumers (Lab interfaces) can immediately size their positions.
    """

    match_id: int = Field(
        ...,
        description="matchcalendar.id of the evaluated match",
    )
    market: str = Field(
        ...,
        description="Machine-readable market key, e.g. 'over_2.5', '1x2_home'",
    )
    odds: float = Field(
        ...,
        description="Bookmaker decimal odds for this market leg",
    )
    p_model: float = Field(
        ...,
        description="Model's estimated probability of the outcome (0.0 – 1.0)",
    )
    ev_final: float = Field(
        ...,
        description="AI-corrected expected value (decimal, e.g. 0.08 = +8 %)",
    )
    recommended_stake_fraction: float = Field(
        ...,
        description=(
            "Fraction of bankroll to stake, computed by the Fractional Kelly "
            "Staking Engine.  Already capped at MAX_STAKE_FRACTION (5 %) and "
            "subject to the minimum threshold (0.5 %).  0.0 means no bet."
        ),
    )
