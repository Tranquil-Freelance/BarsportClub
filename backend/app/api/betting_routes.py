"""
Quantitative Betting Engine – FastAPI Router
=============================================
Exposes the Phase 5 value‑engine orchestration to the frontend.

- POST /api/v1/betting/evaluate-picks-batch  → full institutional pipeline
- GET  /api/v1/betting/value-bets            → value bets with staking output
- GET  /api/v1/betting/lab1-analytics        → raw market delta (Lab 1)
- GET  /api/v1/betting/lab2-matrix           → Poisson matrix (Lab 2)
- GET  /api/v1/betting/available-matches     → league→match dropdown data
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.betting_schemas import ValueBetResponse
from app.services.betting_evaluator import (
    compute_lab2_matrix,
    evaluate_lab1_analytics,
    evaluate_picks_batch,
    evaluate_value_bets,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["betting-quant"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class MatchOddsEntry(BaseModel):
    """A single match with its real bookmaker odds."""

    match_id: int = Field(..., description="matchcalendar.id")
    real_odds: Dict[str, Any] = Field(
        ...,
        description=(
            "Bookmaker odds in evaluate_all_markets format. Example:\n"
            '{"1x2": {"home": 2.10, "draw": 3.40, "away": 3.80},\n'
            ' "over_under": {"line": 2.5, "over": 1.90, "under": 1.90},\n'
            ' "btts": {"yes": 1.80, "no": 2.00},\n'
            ' "asian_handicap": {"0.0": {"home": 1.85, "away": 1.95}}}'
        ),
    )


class BatchEvaluateRequest(BaseModel):
    """Batch evaluation request — multiple matches with odds."""

    matches: List[MatchOddsEntry] = Field(
        ..., max_length=50, description="Up to 50 matches to evaluate"
    )


class TopPickResponse(BaseModel):
    """One final Top Pick."""

    rank: int = Field(..., description="1‑based rank")
    market_key: str = Field(..., description="Machine key, e.g. 'over_2.5'")
    market_label: str = Field("", description="Human label, e.g. 'Over 2.5 Goals'")
    match_id: int = Field(..., description="matchcalendar.id")
    home_team: str = Field(..., description="Home team name")
    away_team: str = Field(..., description="Away team name")
    league_name: str = Field("", description="League name")
    match_datetime: Optional[str] = Field(None, description="ISO datetime")
    odds: float = Field(0.0, description="Decimal odds")
    p_model: float = Field(0.0, description="Model probability")
    p_book: Optional[float] = Field(None, description="Margin‑free book probability")
    ev_base: Optional[float] = Field(None, description="Raw expected value")
    ev_final: float = Field(0.0, description="AI‑corrected expected value")
    confidence_score: int = Field(50, ge=1, le=100, description="AI confidence 1‑100")
    ai_reasoning: str = Field("", description="AI risk‑assessment reasoning")
    score: float = Field(0.0, description="Scoring metric for ranking")


class BatchEvaluateResponse(BaseModel):
    """Response from the full quantitative pipeline."""

    top_picks: List[TopPickResponse] = Field(
        ..., description="Highest‑ranked picks (max 5)"
    )
    total_evaluated: int = Field(
        ..., description="Number of markets that passed the AI gate"
    )
    matches_processed: int = Field(
        ..., description="Number of matches successfully processed"
    )


class Lab1AnalyticsEntry(BaseModel):
    """Raw market analytics entry — no AI correction, no filters applied."""

    match_name: str = Field(..., description="Home vs Away display name")
    match_id: int = Field(..., description="matchcalendar.id")
    market_key: str = Field(..., description="Machine key, e.g. 'over_2.5'")
    market_label: str = Field("", description="Human-readable market label")
    odds: Optional[float] = Field(None, description="Bookmaker odds (None when unavailable)")
    p_book: Optional[float] = Field(None, description="Margin-removed bookmaker probability (None when unavailable)")
    p_model: Optional[float] = Field(None, description="Model probability from Poisson pipeline")
    diff: Optional[float] = Field(None, description="p_model - p_book (None when bookmaker data missing)")
    ev_base: Optional[float] = Field(None, description="Raw expected value (None when bookmaker data missing)")


class Lab1AnalyticsResponse(BaseModel):
    """Response from the Lab 1 raw analytics endpoint."""

    markets: List[Lab1AnalyticsEntry] = Field(
        ..., description="All evaluated markets across all requested matches"
    )


# ---------------------------------------------------------------------------
# Available Matches — dropdown population
# ---------------------------------------------------------------------------


class AvailableMatch(BaseModel):
    """A single match entry for the frontend dropdown."""

    match_id: int = Field(..., description="matchcalendar.id")
    label: str = Field(
        ...,
        description="Human-readable 'Home vs Away' string",
    )


class LeagueMatches(BaseModel):
    """League grouping with its matches."""

    league_name: str = Field(..., description="League display name, e.g. 'Serie A'")
    matches: List[AvailableMatch] = Field(
        ..., description="Matches belonging to this league"
    )


AvailableMatchesResponse = List[LeagueMatches]


# ---------------------------------------------------------------------------
# POST /api/v1/betting/evaluate-picks-batch
# ---------------------------------------------------------------------------


@router.post(
    "/betting/evaluate-picks-batch",
    response_model=BatchEvaluateResponse,
)
async def evaluate_batch(
    req: BatchEvaluateRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    Run the full Institutional Quantitative Betting Engine on a batch of
    matches.

    Pipeline for each match:

    1.  **λ computation** (rolling stats → attack/defence strength → Poisson λ).
    2.  **Score matrix** (independent Poisson for home & away, 0‑6 goals).
    3.  **Market derivation** (Over/Under 2.5, BTTS, 1X2, Asian Handicap).
    4.  **Margin removal** + **Expected Value** calculation.
    5.  **Cost optimisation** — only markets with ``ev_base > 2 %`` proceed.
    6.  **AI risk assessment** (DeepSeek → OpenAI) — penalises EV for
        high variance / low stability.
    7.  **Strict filtering** (ev_final > 5 %, p_model > 35 %) + ranking.

    Returns the top 5 picks across all submitted matches.
    """
    if not req.matches:
        raise HTTPException(status_code=400, detail="matches list is empty")

    try:
        result = await evaluate_picks_batch(
            session=session,
            matches_data=[
                {"match_id": m.match_id, "real_odds": m.real_odds}
                for m in req.matches
            ],
        )
    except Exception as exc:
        logger.exception("Batch evaluation failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return BatchEvaluateResponse(
        top_picks=[
            TopPickResponse(
                rank=p.get("rank", 0),
                market_key=p.get("market_key", ""),
                market_label=p.get("market_label", ""),
                match_id=p.get("match_id", 0),
                home_team=p.get("home_team", ""),
                away_team=p.get("away_team", ""),
                league_name=p.get("league_name", ""),
                match_datetime=p.get("match_datetime"),
                odds=p.get("odds", 0.0),
                p_model=p.get("p_model", 0.0),
                p_book=p.get("p_book"),
                ev_base=p.get("ev_base"),
                ev_final=p.get("ev_final", 0.0),
                confidence_score=p.get("confidence_score", 50),
                ai_reasoning=p.get("ai_reasoning", ""),
                score=p.get("score", 0.0),
            )
            for p in result.get("top_picks", [])
        ],
        total_evaluated=result.get("total_evaluated", 0),
        matches_processed=result.get("matches_processed", 0),
    )


# ---------------------------------------------------------------------------
# GET /api/v1/betting/value-bets
# ---------------------------------------------------------------------------


@router.get(
    "/betting/value-bets",
    response_model=List[ValueBetResponse],
)
async def get_value_bets(
    match_ids: str = Query(
        ...,
        description="Comma-separated matchcalendar.id values, e.g. '27362,27363'",
    ),
    session: AsyncSession = Depends(get_db),
):
    """
    Retrieve value bets for one or more matches.

    Pipeline
    --------
    1. Match context is fetched from the DB for each ``match_id``.
    2. The full Poisson λ → Score Matrix → Market Evaluation pipeline runs.
    3. AI risk assessment (DeepSeek → OpenAI) applies corrections.
    4. ``filter_and_rank_picks`` applies strict filters (``ev_final > 5 %``,
       ``p_model > 35 %``) and ranks by score.
    5. The **Fractional Kelly Staking Engine** computes
       ``recommended_stake_fraction`` for every qualifying pick.

    Returns
    -------
    list of :class:`ValueBetResponse`
        Each element contains ``match_id``, ``market``, ``odds``, ``p_model``,
        ``ev_final``, and ``recommended_stake_fraction``.
    """
    parsed_ids = [
        int(x.strip()) for x in match_ids.split(",") if x.strip()
    ]
    if not parsed_ids:
        raise HTTPException(
            status_code=400,
            detail="match_ids must contain at least one valid integer",
        )

    result = await evaluate_value_bets(
        session=session,
        match_ids=parsed_ids,
    )

    picks = result.get("top_picks", [])

    return [
        ValueBetResponse(
            match_id=p.get("match_id", 0),
            market=p.get("market_key", ""),
            odds=p.get("odds", 0.0),
            p_model=p.get("p_model", 0.0),
            ev_final=p.get("ev_final", 0.0),
            recommended_stake_fraction=p.get("recommended_stake_fraction", 0.0),
        )
        for p in picks
    ]


# ---------------------------------------------------------------------------
# GET /api/v1/betting/lab1-analytics
# ---------------------------------------------------------------------------


@router.get(
    "/betting/lab1-analytics",
    response_model=Lab1AnalyticsResponse,
)
async def get_lab1_analytics(
    match_ids: str = Query(
        ...,
        description="Comma-separated matchcalendar.id values, e.g. '27362,27363'",
    ),
    session: AsyncSession = Depends(get_db),
):
    """
    Retrieve raw market analytics for one or more matches (Lab 1).

    This endpoint runs the full Poisson λ → Score Matrix → Market Evaluation
    pipeline but deliberately **skips**:

    - Cost-optimisation filter (``ev_base > 0.02``)
    - AI risk assessment (DeepSeek → OpenAI)
    - Final strict filters (``ev_final > 0.05``, ``p_model > 0.35``)

    Returns **ALL** evaluated markets, including negative-EV bets,
    for full transparency and auditing.
    """
    parsed_ids = [
        int(x.strip()) for x in match_ids.split(",") if x.strip()
    ]
    if not parsed_ids:
        raise HTTPException(
            status_code=400,
            detail="match_ids must contain at least one valid integer",
        )

    markets = await evaluate_lab1_analytics(
        session=session,
        match_ids=parsed_ids,
    )

    return Lab1AnalyticsResponse(
        markets=[
            Lab1AnalyticsEntry(
                match_name=m.get("match_name", ""),
                match_id=m.get("match_id", 0),
                market_key=m.get("market_key", ""),
                market_label=m.get("market_label", ""),
                odds=m.get("odds", 0.0),
                p_book=m.get("p_book", 0.0),
                p_model=m.get("p_model", 0.0),
                diff=m.get("diff", 0.0),
                ev_base=m.get("ev_base", 0.0),
            )
            for m in markets
        ]
    )


# ---------------------------------------------------------------------------
# GET /api/v1/betting/lab2-matrix
# ---------------------------------------------------------------------------


class AhComponent(BaseModel):
    """One split component of a quarter Asian Handicap line."""

    line: float = Field(..., description="The resolved sub-line (e.g. -0.5 or -1.0)")
    P_win: float = Field(..., description="Probability the sub-line wins")
    P_push: float = Field(..., description="Probability the sub-line pushes (void)")
    P_loss: float = Field(..., description="Probability the sub-line loses")


class AsianHandicapBreakdown(BaseModel):
    """Asian Handicap breakdown for a quarter line (e.g. -0.75)."""

    line: float = Field(..., description="The original quarter line")
    full_win_component: AhComponent = Field(
        ..., description="The -0.5 (full win) component of the split"
    )
    half_component: AhComponent = Field(
        ..., description="The -1.0 (half/push) component of the split"
    )
    combined_ev: float = Field(
        ..., description="0.5 × P_win(-0.5) + 0.5 × P_win(-1.0)"
    )


class Lab2MatrixResponse(BaseModel):
    """Poisson score matrix and Asian Handicap breakdown for a single match."""

    home_team: str = Field(..., description="Home team name")
    away_team: str = Field(..., description="Away team name")
    lambda_home: float = Field(..., description="Poisson λ for home goals")
    lambda_away: float = Field(..., description="Poisson λ for away goals")
    score_matrix: List[List[float]] = Field(
        ...,
        description=(
            "6×6 probability grid: rows = home goals 0..5, "
            "cols = away goals 0..5"
        ),
    )
    asian_handicap_breakdown: AsianHandicapBreakdown = Field(
        ..., description="Split-line breakdown for Home -0.75"
    )


@router.get(
    "/betting/lab2-matrix",
    response_model=Lab2MatrixResponse,
)
async def get_lab2_matrix(
    match_id: int = Query(
        ...,
        description="A single matchcalendar.id, e.g. 27362",
    ),
    session: AsyncSession = Depends(get_db),
):
    """
    Retrieve the Poisson score matrix and Asian Handicap breakdown
    for a **single** match (Lab 2).

    Pipeline
    --------
    1. Match context is fetched from the DB.
    2. Poisson λ (attack/defence strength) is computed.
    3. A full 6×6 score probability matrix (0‑0 … 5‑5) is generated.
    4. Asian Handicap **-0.75** is split into its two components
       (-0.5 full win, -1.0 half/push) with combined expected value.

    Returns
    -------
    :class:`Lab2MatrixResponse`
        Includes ``home_team``, ``away_team``, ``lambda_home``,
        ``lambda_away``, ``score_matrix`` (6×6), and
        ``asian_handicap_breakdown``.
    """
    result = await compute_lab2_matrix(session=session, match_id=match_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Lab 2 matrix not available for match_id={match_id}",
        )

    return Lab2MatrixResponse(
        home_team=result["home_team"],
        away_team=result["away_team"],
        lambda_home=result["lambda_home"],
        lambda_away=result["lambda_away"],
        score_matrix=result["score_matrix"],
        asian_handicap_breakdown=AsianHandicapBreakdown(
            line=result["asian_handicap_breakdown"]["line"],
            full_win_component=AhComponent(
                line=result["asian_handicap_breakdown"]["full_win_component"]["line"],
                P_win=result["asian_handicap_breakdown"]["full_win_component"]["P_win"],
                P_push=result["asian_handicap_breakdown"]["full_win_component"]["P_push"],
                P_loss=result["asian_handicap_breakdown"]["full_win_component"]["P_loss"],
            ),
            half_component=AhComponent(
                line=result["asian_handicap_breakdown"]["half_component"]["line"],
                P_win=result["asian_handicap_breakdown"]["half_component"]["P_win"],
                P_push=result["asian_handicap_breakdown"]["half_component"]["P_push"],
                P_loss=result["asian_handicap_breakdown"]["half_component"]["P_loss"],
            ),
            combined_ev=result["asian_handicap_breakdown"]["combined_ev"],
        ),
    )


# ---------------------------------------------------------------------------
# GET /api/v1/betting/top-picks  (auto-fetch upcoming matches + evaluate)
# ---------------------------------------------------------------------------


@router.get(
    "/betting/top-picks",
    response_model=BatchEvaluateResponse,
)
async def get_top_picks(
    session: AsyncSession = Depends(get_db),
):
    """
    Auto-evaluate the next upcoming matches and return the top value picks.

    Fetches up to 20 upcoming (not-yet-completed) matches from the DB,
    runs the full Poisson → AI pipeline via ``evaluate_value_bets``, and
    returns the highest-ranked picks.  No request body required — the
    frontend can call this on mount to populate the hero sections.
    """
    try:
        id_query = text("""
            SELECT m.id
            FROM matchcalendar m
            WHERE m.is_completed = false
              AND (m.match_datetime IS NULL OR m.match_datetime > NOW())
            ORDER BY m.match_datetime ASC NULLS LAST
            LIMIT 20
        """)
        rows = await session.execute(id_query)
        match_ids = [row[0] for row in rows]
    except Exception as exc:
        logger.exception("top-picks: DB query for upcoming matches failed: %s", exc)
        return BatchEvaluateResponse(top_picks=[], total_evaluated=0, matches_processed=0)

    if not match_ids:
        return BatchEvaluateResponse(top_picks=[], total_evaluated=0, matches_processed=0)

    try:
        result = await evaluate_value_bets(session=session, match_ids=match_ids)
    except Exception as exc:
        logger.exception("top-picks: evaluate_value_bets failed: %s", exc)
        return BatchEvaluateResponse(top_picks=[], total_evaluated=0, matches_processed=0)

    return BatchEvaluateResponse(
        top_picks=[
            TopPickResponse(
                rank=p.get("rank", 0),
                market_key=p.get("market_key", ""),
                market_label=p.get("market_label", ""),
                match_id=p.get("match_id", 0),
                home_team=p.get("home_team", ""),
                away_team=p.get("away_team", ""),
                league_name=p.get("league_name", ""),
                match_datetime=p.get("match_datetime"),
                odds=p.get("odds", 0.0),
                p_model=p.get("p_model", 0.0),
                p_book=p.get("p_book"),
                ev_base=p.get("ev_base"),
                ev_final=p.get("ev_final", 0.0),
                confidence_score=p.get("confidence_score", 50),
                ai_reasoning=p.get("ai_reasoning", ""),
                score=p.get("score", 0.0),
            )
            for p in result.get("top_picks", [])
        ],
        total_evaluated=result.get("total_evaluated", 0),
        matches_processed=result.get("matches_processed", 0),
    )


# ---------------------------------------------------------------------------
# GET /api/v1/betting/available-matches
# ---------------------------------------------------------------------------


@router.get(
    "/betting/available-matches",
    response_model=AvailableMatchesResponse,
)
async def get_available_matches(
    session: AsyncSession = Depends(get_db),
):
    """
    Retrieve all matches available for analysis, grouped by league.

    Returns a list of league objects, each containing an array of
    matches with ``match_id`` and ``label`` ("Home vs Away") for
    populating the frontend two‑tier dropdown selector.

    Query logic
    -----------
    Joins ``matchcalendar`` → ``team`` (home & away) → ``league``,
    filtering for matches that have xG data (indicating they are
    ready for analysis) OR upcoming not-yet-completed matches.
    Ordered by league name then match datetime descending.
    """
    try:
        query = text("""
            SELECT
                l.name              AS league_name,
                m.id                AS match_id,
                th.name || ' vs ' || ta.name  AS label
            FROM matchcalendar m
            JOIN team     th ON m.home_team_id = th.id
            JOIN team     ta ON m.away_team_id = ta.id
            JOIN league   l  ON m.league_id    = l.id
            WHERE   m."home_xG" IS NOT NULL
                OR m."away_xG" IS NOT NULL
                OR m.is_completed = false
            ORDER BY
                l.name ASC,
                m.match_datetime DESC
        """)

        rows = await session.execute(query)
        raw: List[Dict[str, Any]] = [dict(r._mapping) for r in rows]

        # Group by league_name
        league_map: Dict[str, List[AvailableMatch]] = {}
        for row in raw:
            league = row["league_name"]
            league_map.setdefault(league, []).append(
                AvailableMatch(match_id=row["match_id"], label=row["label"])
            )

        return [
            LeagueMatches(league_name=ln, matches=ms)
            for ln, ms in league_map.items()
        ]
    except Exception as exc:
        logger.exception("available-matches query failed: %s", exc)
        # Return empty list so the frontend never gets a 500
        return []
