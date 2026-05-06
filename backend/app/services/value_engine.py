"""
Quantitative Value Betting Engine
==================================
Phase 1: Rolling Data & λ (Lambda) Calculation Engine.

This module computes the core goal-rate parameters (λ_home, λ_away)
for a given match using:
  1. Rolling averages from a team's last N completed matches
  2. League contextual averages (home/away xG, goals)
  3. Attack/Defence strength ratios
  4. Team strength correction + Home Field Advantage
  5. Clamping to realistic bounds

All data is sourced from the ``matchcalendar`` table.
"""

import math
import logging
import statistics
from typing import Dict, List, Optional, Tuple, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.staking_engine import calculate_kelly_fraction

logger = logging.getLogger(__name__)

# ─── Constants ───────────────────────────────────────────────────────────────

DEFAULT_ROLLING_LIMIT: int = 5
"""Number of past completed matches to use for rolling averages."""

TEAM_STRENGTH_ALPHA: float = 0.15
"""Correction factor applied to λ via team_strength."""

HFA_DEFAULT_BOOST: float = 0.20
"""Default Home Field Advantage adjustment when ratio cannot be computed."""

LAMBDA_MIN: float = 0.1
LAMBDA_MAX: float = 4.5
"""Sane bounds for expected goals per match (Poisson λ)."""


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Rolling Data Extraction
# ═══════════════════════════════════════════════════════════════════════════════


async def get_rolling_stats(
    session: AsyncSession,
    team_id: int,
    league_id: int,
    limit: int = DEFAULT_ROLLING_LIMIT,
) -> Dict[str, Any]:
    """
    Extract rolling statistics for a team from its last ``limit`` completed matches.

    Returns
    -------
    dict with keys:
        - ``xG_for``       : avg xG the team generated (home or away, depending on venue)
        - ``xG_against``   : avg xG the team conceded
        - ``matches_used`` : number of matches actually found (may be < limit)
        - ``league_avg_xG_home``  : league-wide avg home xG (current season, completed)
        - ``league_avg_xG_away``  : league-wide avg away xG
        - ``league_avg_goals_home`` : league-wide avg home goals
        - ``league_avg_goals_away`` : league-wide avg away goals
    """
    # ── 1a. Rolling team stats ──────────────────────────────────────────
    rolling_query = text("""
        SELECT
            AVG(CASE
                WHEN home_team_id = :team_id THEN "home_xG"
                ELSE "away_xG"
            END) AS xG_for,
            AVG(CASE
                WHEN home_team_id = :team_id THEN "away_xG"
                ELSE "home_xG"
            END) AS xG_against
        FROM (
            SELECT *
            FROM matchcalendar
            WHERE (home_team_id = :team_id OR away_team_id = :team_id)
              AND is_completed = true
              AND league_id = :league_id
              AND "home_xG" IS NOT NULL
            ORDER BY match_datetime DESC
            LIMIT :limit
        ) AS recent
    """)

    result = await session.execute(
        rolling_query,
        {"team_id": team_id, "league_id": league_id, "limit": limit},
    )
    row = result.fetchone()

    # Count how many matches actually contributed
    count_query = text("""
        SELECT COUNT(*)
        FROM matchcalendar
        WHERE (home_team_id = :team_id OR away_team_id = :team_id)
          AND is_completed = true
          AND league_id = :league_id
          AND "home_xG" IS NOT NULL
    """)
    cnt_result = await session.execute(
        count_query, {"team_id": team_id, "league_id": league_id}
    )
    matches_used = cnt_result.scalar() or 0

    # ── 1b. League contextual averages ──────────────────────────────────
    league_avg_query = text("""
        SELECT
            AVG("home_xG")   AS league_avg_xG_home,
            AVG("away_xG")   AS league_avg_xG_away,
            AVG(home_goals)  AS league_avg_goals_home,
            AVG(away_goals)  AS league_avg_goals_away
        FROM matchcalendar
        WHERE league_id = :league_id
          AND is_completed = true
          AND "home_xG" IS NOT NULL
          AND home_goals IS NOT NULL
    """)

    league_result = await session.execute(
        league_avg_query, {"league_id": league_id}
    )
    league_row = league_result.fetchone()

    return {
        "xG_for":          float(row[0] or 0.0) if row else 0.0,
        "xG_against":      float(row[1] or 0.0) if row else 0.0,
        "matches_used":    matches_used,
        "league_avg_xG_home":    float(league_row[0] or 0.0) if league_row else 0.0,
        "league_avg_xG_away":    float(league_row[1] or 0.0) if league_row else 0.0,
        "league_avg_goals_home": float(league_row[2] or 0.0) if league_row else 0.0,
        "league_avg_goals_away": float(league_row[3] or 0.0) if league_row else 0.0,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Team Strength Calculation
# ═══════════════════════════════════════════════════════════════════════════════


def calculate_team_strength(
    xG_for: float,
    xG_against: float,
    league_avg_xG: float,
) -> Dict[str, float]:
    """
    Compute team strength metrics from rolling averages and league context.

    Parameters
    ----------
    xG_for : float
        Rolling average xG the team generates.
    xG_against : float
        Rolling average xG the team concedes.
    league_avg_xG : float
        League average xG for the appropriate venue (home/away).

    Returns
    -------
    dict with keys:
        - ``attack_strength``  : xG_for / league_avg_xG  (how much better/worse than league avg)
        - ``defense_strength`` : xG_against / league_avg_xG
        - ``xG_diff``          : xG_for - xG_against
    """
    attack_strength  = xG_for / league_avg_xG if league_avg_xG > 0 else 1.0
    defense_strength = xG_against / league_avg_xG if league_avg_xG > 0 else 1.0

    # ── INSTITUTIONAL CLAMP ─────────────────────────────────────────
    # Prevent Poisson λ drift from low league averages producing
    # extreme EV percentages.  Attack and defence strength ratios
    # are clamped to [0.5, 1.6] — a realistic band for professional
    # football.  Ratios outside this range indicate insufficient
    # rolling data or anomalous league context.
    attack_strength  = max(0.5, min(1.6, attack_strength))
    defense_strength = max(0.5, min(1.6, defense_strength))

    xG_diff = xG_for - xG_against

    return {
        "attack_strength":  round(attack_strength, 4),
        "defense_strength": round(defense_strength, 4),
        "xG_diff":          round(xG_diff, 4),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 & 4 — Core Goal Model (Lambda λ)
# ═══════════════════════════════════════════════════════════════════════════════


def calculate_lambdas(
    attack_home: float,
    defense_home: float,
    attack_away: float,
    defense_away: float,
    league_avg_xG_home: float,
    league_avg_xG_away: float,
    team_strength_home: float,
    team_strength_away: float,
    league_avg_goals_home: Optional[float] = None,
    league_avg_goals_away: Optional[float] = None,
) -> Dict[str, float]:
    """
    Compute the expected goal rates (λ) for a match using the full model.

    Formula sequence
    ----------------
    1. **Base λ** (attack × defence × league avg):
       λ_home_base = (attack_home × defense_away) × league_avg_xG_home
       λ_away_base = (attack_away × defense_home) × league_avg_xG_away

    2. **Team-strength correction** (α = 0.15):
       λ_home_adj = λ_home_base × (1 + 0.15 × team_strength_home)
       λ_away_adj = λ_away_base × (1 + 0.15 × team_strength_away)

    3. **Home Field Advantage**:
       home_boost = league_avg_goals_home / league_avg_goals_away
       If either is 0/missing, defaults to ``HFA_DEFAULT_BOOST`` (0.20).
       λ_home_final = λ_home_adj + home_boost
       λ_away_final = max(0.1, λ_away_adj - home_boost)

    4. **Clamp** (Step 4.4):
       λ_home = max(0.1, min(4.5, λ_home_final))
       λ_away = max(0.1, min(4.5, λ_away_final))

    Parameters
    ----------
    attack_home, defense_home : float
        Home team's attack_strength and defense_strength.
    attack_away, defense_away : float
        Away team's attack_strength and defense_strength.
    league_avg_xG_home, league_avg_xG_away : float
        Season-wide average xG for home/away in this league.
    team_strength_home, team_strength_away : float
        Rolling average of xG_diff for each team.
    league_avg_goals_home, league_avg_goals_away : float, optional
        Season-wide average goals for home/away (used for HFA ratio).
        Defaults to ``None``, which triggers the default HFA boost.

    Returns
    -------
    dict with keys:
        - ``lambda_home``          : final clamped λ for home team
        - ``lambda_away``          : final clamped λ for away team
        - ``lambda_home_base``     : pre-correction base λ (debugging)
        - ``lambda_away_base``     : pre-correction base λ (debugging)
        - ``lambda_home_adj``      : after strength correction
        - ``lambda_away_adj``      : after strength correction
        - ``lambda_home_final``    : after HFA adjustment
        - ``lambda_away_final``    : after HFA adjustment
        - ``home_boost_used``      : the HFA boost value applied
        - ``attack_home``          : input (echoed for debugging)
        - ``defense_home``         : input (echoed for debugging)
        - ``attack_away``          : input (echoed for debugging)
        - ``defense_away``         : input (echoed for debugging)
        - ``team_strength_home``   : input (echoed for debugging)
        - ``team_strength_away``   : input (echoed for debugging)
    """
    # ── 3. Base λ ───────────────────────────────────────────────────────
    lambda_home_base = (attack_home * defense_away) * league_avg_xG_home
    lambda_away_base = (attack_away * defense_home) * league_avg_xG_away

    # ── 4.1 Team-strength correction ────────────────────────────────────
    lambda_home_adj = lambda_home_base * (1 + TEAM_STRENGTH_ALPHA * team_strength_home)
    lambda_away_adj = lambda_away_base * (1 + TEAM_STRENGTH_ALPHA * team_strength_away)

    # ── 4.2 Home Field Advantage ────────────────────────────────────────
    # Compute the empirical HFA ratio for reference; formulas use a flat 0.20.
    if (
        league_avg_goals_home is not None
        and league_avg_goals_away is not None
        and league_avg_goals_away > 0
    ):
        home_boost_ratio = league_avg_goals_home / league_avg_goals_away
    else:
        home_boost_ratio = HFA_DEFAULT_BOOST  # fallback for informational use

    # Exact formulas from spec:
    #   λ_home_final = λ_home_adj + 0.20
    #   λ_away_final = max(0.1, λ_away_adj - 0.20)
    lambda_home_final = lambda_home_adj + HFA_DEFAULT_BOOST
    lambda_away_final = max(LAMBDA_MIN, lambda_away_adj - HFA_DEFAULT_BOOST)

    # ── 4.4 Clamp ───────────────────────────────────────────────────────
    lambda_home = max(LAMBDA_MIN, min(LAMBDA_MAX, lambda_home_final))
    lambda_away = max(LAMBDA_MIN, min(LAMBDA_MAX, lambda_away_final))

    return {
        "lambda_home":        round(lambda_home, 4),
        "lambda_away":        round(lambda_away, 4),
        # Debugging intermediates
        "lambda_home_base":   round(lambda_home_base, 4),
        "lambda_away_base":   round(lambda_away_base, 4),
        "lambda_home_adj":    round(lambda_home_adj, 4),
        "lambda_away_adj":    round(lambda_away_adj, 4),
        "lambda_home_final":  round(lambda_home_final, 4),
        "lambda_away_final":  round(lambda_away_final, 4),
        "home_boost_ratio":   round(home_boost_ratio, 4),
        "hfa_applied":        HFA_DEFAULT_BOOST,
        # Echoed inputs for verification
        "attack_home":        round(attack_home, 4),
        "defense_home":       round(defense_home, 4),
        "attack_away":        round(attack_away, 4),
        "defense_away":       round(defense_away, 4),
        "team_strength_home": round(team_strength_home, 4),
        "team_strength_away": round(team_strength_away, 4),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR — Full pipeline for a single match
# ═══════════════════════════════════════════════════════════════════════════════


async def compute_match_lambdas(
    session: AsyncSession,
    home_team_id: int,
    away_team_id: int,
    league_id: int,
    rolling_limit: int = DEFAULT_ROLLING_LIMIT,
) -> Dict[str, Any]:
    """
    Run the full λ computation pipeline for a single match.

    Steps
    -----
    1. Extract rolling stats for both teams.
    2. Calculate team-strength metrics (attack, defence, xG_diff).
    3. Combine into the final λ_home / λ_away via the core model.

    Parameters
    ----------
    session : AsyncSession
        Active DB session.
    home_team_id, away_team_id : int
        Team identifiers.
    league_id : int
        League context for averages.
    rolling_limit : int
        Number of past matches for rolling averages (default 5).

    Returns
    -------
    dict with keys:
        - ``lambda_home``, ``lambda_away`` (final clamped values)
        - All intermediate metrics for debugging / logging
        - ``home_rolling``, ``away_rolling`` (raw rolling stats dicts)
    """
    # ── 1. Rolling data for both teams ──────────────────────────────────
    home_rolling = await get_rolling_stats(
        session, home_team_id, league_id, limit=rolling_limit
    )
    away_rolling = await get_rolling_stats(
        session, away_team_id, league_id, limit=rolling_limit
    )

    # ── 2. Team strength for each team (using venue-appropriate avg) ────
    home_strength = calculate_team_strength(
        xG_for=home_rolling["xG_for"],
        xG_against=home_rolling["xG_against"],
        league_avg_xG=home_rolling["league_avg_xG_home"],  # home team uses home avg
    )
    away_strength = calculate_team_strength(
        xG_for=away_rolling["xG_for"],
        xG_against=away_rolling["xG_against"],
        league_avg_xG=away_rolling["league_avg_xG_away"],  # away team uses away avg
    )

    # Team strength (rolling xG_diff) for the λ correction
    # We recompute it as the simple xG_diff from rolling data
    team_strength_home = home_strength["xG_diff"]
    team_strength_away = away_strength["xG_diff"]

    # ── 3. Compute λ ────────────────────────────────────────────────────
    lambdas = calculate_lambdas(
        attack_home=home_strength["attack_strength"],
        defense_home=home_strength["defense_strength"],
        attack_away=away_strength["attack_strength"],
        defense_away=away_strength["defense_strength"],
        league_avg_xG_home=home_rolling["league_avg_xG_home"],
        league_avg_xG_away=away_rolling["league_avg_xG_away"],
        team_strength_home=team_strength_home,
        team_strength_away=team_strength_away,
        league_avg_goals_home=home_rolling.get("league_avg_goals_home"),
        league_avg_goals_away=home_rolling.get("league_avg_goals_away"),
    )

    # Attach rolling data for full transparency
    lambdas["home_rolling"] = home_rolling
    lambdas["away_rolling"] = away_rolling
    lambdas["home_strength"] = home_strength
    lambdas["away_strength"] = away_strength

    return lambdas


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — Poisson Distribution, Score Matrix & Market Derivation
# ═══════════════════════════════════════════════════════════════════════════════


def poisson_probability(lam: float, k: int) -> float:
    """
    Poisson probability mass function.

    ``P(X = k) = (λ^k × e^{-λ}) / k!``

    Parameters
    ----------
    lam : float
        The expected goal rate (λ).
    k : int
        Number of goals.

    Returns
    -------
    float
        The probability of exactly ``k`` goals given rate ``lam``.
    """
    if lam <= 0 or k < 0:
        return 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def generate_score_matrix(
    lambda_home: float,
    lambda_away: float,
    max_goals: int = 6,
) -> Dict[str, Any]:
    """
    Generate a full score probability matrix using independent Poisson distributions.

    For each combination of home goals ``k`` and away goals ``j`` (0..max_goals):

        P(k, j) = Poisson(λ_home, k) × Poisson(λ_away, j)

    Also accumulates:

    - ``P_total`` : probability of ``n = k + j`` total goals
    - ``P_diff``  : probability of ``d = k - j`` goal difference

    Parameters
    ----------
    lambda_home, lambda_away : float
        Expected goal rates for home and away team.
    max_goals : int
        Maximum goals considered per team (default 6; covers >99.9 % of mass).

    Returns
    -------
    dict with keys:
        - ``matrix``   : dict[(k, j)] → probability  (sparse 2-D grid)
        - ``P_total``  : dict[n] → probability        (0..2×max_goals)
        - ``P_diff``   : dict[d] → probability        (-max_goals..+max_goals)
        - ``lambda_home``, ``lambda_away``, ``max_goals`` (echoed for context)
    """
    # Precompute marginals so each Poisson is evaluated once per rate
    home_pmf = [poisson_probability(lambda_home, k) for k in range(max_goals + 1)]
    away_pmf = [poisson_probability(lambda_away, j) for j in range(max_goals + 1)]

    matrix: Dict[Tuple[int, int], float] = {}
    P_total: Dict[int, float] = {}
    P_diff: Dict[int, float] = {}

    for k in range(max_goals + 1):
        for j in range(max_goals + 1):
            prob = home_pmf[k] * away_pmf[j]
            if prob < 1e-12:
                continue  # skip negligible mass

            matrix[(k, j)] = prob

            n = k + j
            P_total[n] = P_total.get(n, 0.0) + prob

            d = k - j
            P_diff[d] = P_diff.get(d, 0.0) + prob

    return {
        "matrix": matrix,
        "P_total": P_total,
        "P_diff": P_diff,
        "lambda_home": lambda_home,
        "lambda_away": lambda_away,
        "max_goals": max_goals,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7 — Standard Market Derivation
# ═══════════════════════════════════════════════════════════════════════════════


def derive_standard_markets(score_matrix: Dict[str, Any]) -> Dict[str, float]:
    """
    Derive standard betting markets from the score probability matrix.

    Markets computed
    ----------------
    - **Over / Under 2.5** : total goals ≥3 or ≤2
    - **Both Teams to Score** : whether both teams score ≥1
    - **1X2 (Match Result)** : home win / draw / away win via goal difference

    Parameters
    ----------
    score_matrix : dict
        The output of :func:`generate_score_matrix`.

    Returns
    -------
    dict with keys:
        ``over_2_5``, ``under_2_5``,
        ``btts_yes``, ``btts_no``,
        ``home_win``, ``draw``, ``away_win``,
        plus all input λ values for context.
    """
    P_total = score_matrix["P_total"]
    P_diff = score_matrix["P_diff"]
    matrix = score_matrix["matrix"]

    # ── Over / Under 2.5 ────────────────────────────────────────────────
    over_2_5 = sum(prob for n, prob in P_total.items() if n >= 3)
    under_2_5 = sum(prob for n, prob in P_total.items() if n <= 2)

    # ── Both Teams to Score ─────────────────────────────────────────────
    # P(home=0) = sum of all probabilities where home goals = 0
    P_home_0 = sum(prob for (k, _j), prob in matrix.items() if k == 0)
    # P(away=0) = sum of all probabilities where away goals = 0
    P_away_0 = sum(prob for (_k, j), prob in matrix.items() if j == 0)
    # P(0, 0) from matrix
    P_0_0 = matrix.get((0, 0), 0.0)

    # Inclusion-exclusion: P(both score) = 1 - P(home=0) - P(away=0) + P(0,0)
    btts_yes = 1.0 - P_home_0 - P_away_0 + P_0_0
    btts_no = 1.0 - btts_yes

    # ── 1X2 (Match Result) via goal difference ──────────────────────────
    home_win = sum(prob for d, prob in P_diff.items() if d > 0)
    draw = P_diff.get(0, 0.0)
    away_win = sum(prob for d, prob in P_diff.items() if d < 0)

    return {
        "over_2_5":  round(over_2_5, 6),
        "under_2_5": round(under_2_5, 6),
        "btts_yes":  round(btts_yes, 6),
        "btts_no":   round(btts_no, 6),
        "home_win":  round(home_win, 6),
        "draw":      round(draw, 6),
        "away_win":  round(away_win, 6),
        # Echo λ for context
        "lambda_home": score_matrix.get("lambda_home"),
        "lambda_away": score_matrix.get("lambda_away"),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7.4 — Asian Handicap Engine
# ═══════════════════════════════════════════════════════════════════════════════


def _resolve_ah_line(
    P_diff: Dict[int, float],
    line: float,
    eps: float = 1e-9,
) -> Dict[str, float]:
    """
    Resolve a single integer-or-half Asian Handicap line.

    For each goal difference ``d`` (home - away):

        adj_diff = d + line

        - adj_diff > +eps   → win
        - |adj_diff| ≤ eps  → push (void / refund)
        - adj_diff < -eps   → loss

    Returns dict with ``P_win``, ``P_push``, ``P_loss``.
    """
    P_win = 0.0
    P_push = 0.0
    P_loss = 0.0

    for d, prob in P_diff.items():
        adj = d + line
        if adj > eps:
            P_win += prob
        elif abs(adj) <= eps:
            P_push += prob
        else:
            P_loss += prob

    return {
        "P_win":  round(P_win, 6),
        "P_push": round(P_push, 6),
        "P_loss": round(P_loss, 6),
    }


def derive_asian_handicap_prob(
    score_matrix: Dict[str, Any],
    line: float,
) -> Dict[str, float]:
    """
    Derive Asian Handicap win/push/loss probabilities for the HOME team.

    Handles full/half lines (multiples of 0.5) directly via goal-difference
    comparison.  Handles **quarter lines** (e.g. -0.25, -0.75, +0.25) by
    splitting into two adjacent half/integer lines and averaging:

        line1 = line + 0.25
        line2 = line - 0.25
        P_win  = 0.5 × P_win(line1) + 0.5 × P_win(line2)
        P_push = 0.5 × P_push(line1) + 0.5 × P_push(line2)
        P_loss = 0.5 × P_loss(line1) + 0.5 × P_loss(line2)

    Parameters
    ----------
    score_matrix : dict
        Output of :func:`generate_score_matrix` (must contain ``P_diff``).
    line : float
        Asian Handicap line for the HOME team (e.g. -0.5, 0.0, +0.25, -1.0).

    Returns
    -------
    dict with keys ``P_win``, ``P_push``, ``P_loss`` (each rounded to 6 decimals).
    """
    P_diff = score_matrix["P_diff"]

    # ── Detect quarter line ─────────────────────────────────────────────
    # A quarter line has a non-zero fractional part in 0.25 increments.
    # line % 0.5 != 0  →  quarter line  (e.g. -0.25, -0.75, +0.25, +0.75)
    remainder = abs(line) % 0.5
    if remainder > 1e-9 and abs(remainder - 0.5) > 1e-9:
        # Quarter line: split into two adjacent half/integer lines
        line1 = line + 0.25
        line2 = line - 0.25

        res1 = _resolve_ah_line(P_diff, line1)
        res2 = _resolve_ah_line(P_diff, line2)

        return {
            "P_win":  round(0.5 * res1["P_win"] + 0.5 * res2["P_win"], 6),
            "P_push": round(0.5 * res1["P_push"] + 0.5 * res2["P_push"], 6),
            "P_loss": round(0.5 * res1["P_loss"] + 0.5 * res2["P_loss"], 6),
        }

    # ── Integer / half line ─────────────────────────────────────────────
    return _resolve_ah_line(P_diff, line)


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — Bookmaker Margin Removal & Expected Value
# ═══════════════════════════════════════════════════════════════════════════════


# ─── Step 8: Margin Removal ────────────────────────────────────────────────


def remove_margin_2way(
    odds_1: float,
    odds_2: float,
) -> Dict[str, float]:
    """
    Remove the bookmaker margin (vig) from a two-way market.

    Converts decimal odds to implied probabilities, normalises them
    so they sum to 1.0, and returns the true probabilities plus the
    margin.

    Parameters
    ----------
    odds_1, odds_2 : float
        Decimal odds for the two outcomes (e.g. Over / Under).

    Returns
    -------
    dict with keys:
        - ``p1_true`` : margin-free probability for outcome 1
        - ``p2_true`` : margin-free probability for outcome 2
        - ``margin``  : the vig = (implied_1 + implied_2) - 1

    Returns ``None`` for all keys if either odds value is ≤ 1.0.
    """
    if odds_1 <= 1.0 or odds_2 <= 1.0:
        return {"p1_true": None, "p2_true": None, "margin": None}

    implied_1 = 1.0 / odds_1
    implied_2 = 1.0 / odds_2
    total_margin = implied_1 + implied_2

    p1_true = implied_1 / total_margin
    p2_true = implied_2 / total_margin

    return {
        "p1_true": round(p1_true, 6),
        "p2_true": round(p2_true, 6),
        "margin":  round(total_margin - 1.0, 6),
    }


def remove_margin_3way(
    odds_1: float,
    odds_X: float,
    odds_2: float,
) -> Dict[str, float]:
    """
    Remove the bookmaker margin from a three-way market (1X2).

    Parameters
    ----------
    odds_1, odds_X, odds_2 : float
        Decimal odds for Home Win, Draw, Away Win.

    Returns
    -------
    dict with keys:
        - ``p1_true``, ``pX_true``, ``p2_true`` : margin-free probabilities
        - ``margin`` : the vig

    Returns ``None`` for all keys if any odds value is ≤ 1.0.
    """
    if odds_1 <= 1.0 or odds_X <= 1.0 or odds_2 <= 1.0:
        return {"p1_true": None, "pX_true": None, "p2_true": None, "margin": None}

    implied_1 = 1.0 / odds_1
    implied_X = 1.0 / odds_X
    implied_2 = 1.0 / odds_2
    total_margin = implied_1 + implied_X + implied_2

    p1_true = implied_1 / total_margin
    pX_true = implied_X / total_margin
    p2_true = implied_2 / total_margin

    return {
        "p1_true": round(p1_true, 6),
        "pX_true": round(pX_true, 6),
        "p2_true": round(p2_true, 6),
        "margin":  round(total_margin - 1.0, 6),
    }


# ─── Step 9: Expected Value & Delta ────────────────────────────────────────


def calculate_edge_metrics(
    p_model: float,
    decimal_odds: float,
    p_book: Optional[float] = None,
) -> Dict[str, Optional[float]]:
    """
    Compute the absolute Expected Value and probability delta.

    Parameters
    ----------
    p_model : float
        Our model's estimated probability of the outcome.
    decimal_odds : float
        Bookmaker's decimal odds for that outcome.
    p_book : float, optional
        The margin-free (true) probability from the bookmaker.
        If not provided, ``diff`` will be ``None``.

    Returns
    -------
    dict with keys:
        - ``ev_base`` : absolute Expected Value = (p_model × odds) - 1
        - ``diff``    : p_model - p_book (probability delta, or None)

    Returns ``None`` for ``ev_base`` if odds ≤ 1.0 or p_model is invalid.
    """
    if decimal_odds <= 1.0 or p_model is None or p_model <= 0.0:
        return {"ev_base": None, "diff": None}

    ev_base = (p_model * decimal_odds) - 1.0

    diff = None
    if p_book is not None:
        diff = p_model - p_book

    return {
        "ev_base": round(ev_base, 6),
        "diff":    round(diff, 6) if diff is not None else None,
    }


# ─── Orchestrator — Full Market Evaluation ────────────────────────────────


def evaluate_all_markets(
    model_probs: Dict[str, Any],
    real_odds: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Bridge Phase 2 model probabilities with Phase 3 real bookmaker odds.

    For every market present in ``real_odds``, this function:

    1. Calls the appropriate margin-removal function to get ``p_book``.
    2. Fetches corresponding ``p_model`` from ``model_probs``.
    3. Calls ``calculate_edge_metrics`` for EV and delta.
    4. Attaches the raw odds for reference.

    ``real_odds`` expected structure::

        {
            "1x2": {"home": 2.10, "draw": 3.40, "away": 3.80},
            "over_under": {"line": 2.5, "over": 1.90, "under": 1.90},
            "btts": {"yes": 1.80, "no": 2.00},
            "asian_handicap": {
                "0.0":  {"home": 1.85, "away": 1.95},
                "-0.5": {"home": 2.00, "away": 1.80},
                "-1.0": {"home": 2.15, "away": 1.70},
            },
        }

    Parameters
    ----------
    model_probs : dict
        Output from :func:`derive_standard_markets` (contains ``home_win``,
        ``draw``, ``away_win``, ``over_2_5``, ``under_2_5``, ``btts_yes``,
        ``btts_no``) plus optional AH probabilities.
    real_odds : dict
        Bookmaker odds keyed by market type (see structure above).

    Returns
    -------
    dict mapping each market / line to a dict with:
        ``p_model``, ``p_book``, ``ev_base``, ``diff``, ``odds``.
    """
    results: Dict[str, Any] = {}

    # ── Helper to safely get model probability ─────────────────────────
    def _lookup(key: str, default: Optional[float] = None) -> Optional[float]:
        return model_probs.get(key, default)

    # ── Helper to compute & store a market leg ─────────────────────────
    def _evaluate_leg(
        market_key: str,
        p_model: Optional[float],
        odds: float,
        p_book: Optional[float],
    ) -> None:
        edge = calculate_edge_metrics(p_model, odds, p_book) if p_model is not None else {"ev_base": None, "diff": None}
        results[market_key] = {
            "p_model": p_model,
            "p_book":  p_book,
            "ev_base": edge["ev_base"],
            "diff":    edge["diff"],
            "odds":    odds,
        }

    # ────────────────────────────────────────────────────────────────────
    # 1. 1X2 (three-way)
    # ────────────────────────────────────────────────────────────────────
    if "1x2" in real_odds:
        m = real_odds["1x2"]
        margined = remove_margin_3way(m["home"], m["draw"], m["away"])
        if margined["p1_true"] is not None:
            _evaluate_leg("1x2_home", _lookup("home_win"), m["home"], margined["p1_true"])
            _evaluate_leg("1x2_draw", _lookup("draw"),     m["draw"], margined["pX_true"])
            _evaluate_leg("1x2_away", _lookup("away_win"), m["away"], margined["p2_true"])
        else:
            # Edge case: invalid odds — store raw odds with no derived values
            for leg, odds_key in [("1x2_home", "home"), ("1x2_draw", "draw"), ("1x2_away", "away")]:
                results[leg] = {"p_model": _lookup(odds_key), "p_book": None, "ev_base": None, "diff": None, "odds": m[odds_key]}

    # ────────────────────────────────────────────────────────────────────
    # 2. Over / Under (two-way)
    # ────────────────────────────────────────────────────────────────────
    if "over_under" in real_odds:
        ou = real_odds["over_under"]
        line = ou.get("line", 2.5)
        margined = remove_margin_2way(ou["over"], ou["under"])
        if margined["p1_true"] is not None:
            _evaluate_leg(f"over_{line}",  _lookup("over_2_5"),  ou["over"],  margined["p1_true"])
            _evaluate_leg(f"under_{line}", _lookup("under_2_5"), ou["under"], margined["p2_true"])
        else:
            results[f"over_{line}"]  = {"p_model": _lookup("over_2_5"),  "p_book": None, "ev_base": None, "diff": None, "odds": ou["over"]}
            results[f"under_{line}"] = {"p_model": _lookup("under_2_5"), "p_book": None, "ev_base": None, "diff": None, "odds": ou["under"]}

    # ────────────────────────────────────────────────────────────────────
    # 3. BTTS (two-way)
    # ────────────────────────────────────────────────────────────────────
    if "btts" in real_odds:
        btts = real_odds["btts"]
        margined = remove_margin_2way(btts["yes"], btts["no"])
        if margined["p1_true"] is not None:
            _evaluate_leg("btts_yes", _lookup("btts_yes"), btts["yes"], margined["p1_true"])
            _evaluate_leg("btts_no",  _lookup("btts_no"),  btts["no"],  margined["p2_true"])
        else:
            results["btts_yes"] = {"p_model": _lookup("btts_yes"), "p_book": None, "ev_base": None, "diff": None, "odds": btts["yes"]}
            results["btts_no"]  = {"p_model": _lookup("btts_no"),  "p_book": None, "ev_base": None, "diff": None, "odds": btts["no"]}

    # ────────────────────────────────────────────────────────────────────
    # 4. Asian Handicap (two-way per line)
    # ────────────────────────────────────────────────────────────────────
    if "asian_handicap" in real_odds:
        ah = real_odds["asian_handicap"]
        for line_str, legs in ah.items():
            try:
                line = float(line_str)
            except (ValueError, TypeError):
                continue  # skip unparseable line keys

            # Derive model probability for this AH line
            sm = model_probs.get("_score_matrix")
            if sm is not None:
                ah_model = derive_asian_handicap_prob(sm, line)
                p_model_home = ah_model["P_win"]
                # P_win for home = home covers the spread; away = 1 - P_win (ignoring push for EV purposes)
                p_model_away = 1.0 - p_model_home
            else:
                p_model_home = None
                p_model_away = None

            home_odds = legs.get("home")
            away_odds = legs.get("away")

            if home_odds is not None and away_odds is not None:
                margined = remove_margin_2way(home_odds, away_odds)
                if margined["p1_true"] is not None:
                    _evaluate_leg(f"ah_{line}_home", p_model_home, home_odds, margined["p1_true"])
                    _evaluate_leg(f"ah_{line}_away", p_model_away, away_odds, margined["p2_true"])
                else:
                    results[f"ah_{line}_home"] = {"p_model": p_model_home, "p_book": None, "ev_base": None, "diff": None, "odds": home_odds}
                    results[f"ah_{line}_away"] = {"p_model": p_model_away, "p_book": None, "ev_base": None, "diff": None, "odds": away_odds}

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4 — AI Meta-Model Integration & Pick Selection
# ═══════════════════════════════════════════════════════════════════════════════


# ─── Step 11: Feature Extraction & Stability ─────────────────────────────


def calculate_stability(
    xg_diff_array: List[float],
    default_penalty: float = 1.5,
) -> float:
    """
    Compute a team's stability score from its rolling xG_diff history.

    A lower value means the team is **more stable** (consistent performance).
    A higher value signals erratic form, which should penalise confidence.

    Parameters
    ----------
    xg_diff_array : list of float
        Rolling xG_diff values from the team's last N matches
        (e.g. [0.3, -0.1, 0.8, -0.4, 0.2]).
    default_penalty : float
        Fallback value when fewer than 2 data points are available
        (default 1.5 — high uncertainty).

    Returns
    -------
    float
        Standard deviation of the xG_diff array, or ``default_penalty``
        if the array has fewer than 2 elements.
    """
    if len(xg_diff_array) < 2:
        return default_penalty

    return round(statistics.stdev(xg_diff_array), 4)


def build_ai_features(
    match_context: Dict[str, Any],
    market_evaluation: Dict[str, Any],
    stability_home: float,
    stability_away: float,
) -> Dict[str, Any]:
    """
    Build a flat numerical feature vector for the AI risk model.

    Parameters
    ----------
    match_context : dict
        Must contain ``lambda_home`` and ``lambda_away``.
    market_evaluation : dict
        A single market result from :func:`evaluate_all_markets`,
        containing ``p_model``, ``p_book``, ``ev_base``, ``diff``,
        ``odds``, and a ``_market_type`` override or inferred key.
    stability_home, stability_away : float
        Stability scores from :func:`calculate_stability`.

    Returns
    -------
    dict with exactly the following keys::

        {
            "lam_home": float,
            "lam_away": float,
            "p_model": float,
            "p_book": float,
            "ev_base": float,
            "diff": float,
            "stability_home": float,
            "stability_away": float,
            "market_type": str,
            "odds": float,
            "variance_match": float,
        }
    """
    lam_home = match_context.get("lambda_home", 0.0) or 0.0
    lam_away = match_context.get("lambda_away", 0.0) or 0.0

    p_model = market_evaluation.get("p_model", 0.0) or 0.0
    p_book  = market_evaluation.get("p_book", 0.0) or 0.0
    ev_base = market_evaluation.get("ev_base", 0.0) or 0.0
    diff    = market_evaluation.get("diff", 0.0) or 0.0
    odds    = market_evaluation.get("odds", 0.0) or 0.0
    market_type = market_evaluation.get("_market_type", "unknown")

    return {
        "lam_home":       round(lam_home, 4),
        "lam_away":       round(lam_away, 4),
        "p_model":        round(p_model, 6),
        "p_book":         round(p_book, 6),
        "ev_base":        round(ev_base, 6),
        "diff":           round(diff, 6),
        "stability_home": round(stability_home, 4),
        "stability_away": round(stability_away, 4),
        "market_type":    market_type,
        "odds":           round(odds, 4),
        "variance_match": round(lam_home + lam_away, 4),
    }


# ─── Step 11.2: AI Prompt Builder ────────────────────────────────────────


AI_RISK_SYSTEM_PROMPT = (
    "You are a quantitative betting risk manager. "
    "You are given statistical features for a specific betting market. "
    "Your job is to evaluate the ev_base against the team stabilities and match variance. "
    "If the variance is high and stability is poor, penalize the EV. "
    'Output ONLY a JSON containing '
    '{"ev_final": float, "confidence_score": int (1-100), '
    '"reasoning": "brief strict tactical/math reason"}.'
)


def generate_ai_risk_prompt(features: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Build the exact message payload to send to DeepSeek / OpenAI.

    The system prompt instructs the LLM to act as a quantitative risk
    manager.  The user message contains the raw feature vector as a
    formatted block so the model can reason over the numbers.

    Parameters
    ----------
    features : dict
        The flat feature dict from :func:`build_ai_features`.

    Returns
    -------
    list of dict
        A messages list compatible with the OpenAI Chat Completions API::

            [
                {"role": "system", "content": AI_RISK_SYSTEM_PROMPT},
                {"role": "user",   "content": "<formatted features>"},
            ]
    """
    # Format the features as a clean key: value block
    feature_lines = "\n".join(
        f"  {k}: {v}" for k, v in features.items()
    )

    user_content = (
        "Evaluate this betting market feature vector:\n"
        f"{feature_lines}\n\n"
        "Consider:\n"
        "  1. Is ev_base reliable given the team stabilities?\n"
        "  2. If variance_match is high AND stabilities are high (unstable), "
        "penalise the EV by 10-30%.\n"
        "  3. Assign a confidence score 1-100 reflecting data quality.\n"
        "Output ONLY a JSON object with keys ev_final, confidence_score, reasoning."
    )

    return [
        {"role": "system", "content": AI_RISK_SYSTEM_PROMPT},
        {"role": "user",   "content": user_content},
    ]


# ─── Step 12: Pick Filtering & Ranking ────────────────────────────────────

# Market priority hierarchy (lower index = higher priority)
MARKET_PRIORITY = [
    "over_under",
    "btts",
    "team_goals",
    "asian_handicap",
    "1x2",
]


def _infer_market_priority(market_key: str) -> int:
    """Map a market key string to its priority index (0 = highest)."""
    mk = market_key.lower()
    if "over" in mk or "under" in mk:
        return 0
    if "btts" in mk:
        return 1
    if "team" in mk or "goal" in mk:
        return 2
    if "ah_" in mk or "asian" in mk:
        return 3
    if "1x2" in mk or "home" in mk or "draw" in mk or "away" in mk:
        return 4
    return 5  # unknown — lowest


def filter_and_rank_picks(
    ai_evaluated_markets: List[Dict[str, Any]],
    min_ev: float = 0.05,
    min_p_model: float = 0.35,
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """
    Strictly filter, score, and rank AI-evaluated markets into final picks.

    Pipeline
    --------
    1. **Filter by EV**:  ``ev_final > min_ev``  (default +5 %).
    2. **Filter by prob**: ``p_model > min_p_model``  (default 0.35).
    3. **Score**: ``score = ev_final * (1.0 / avg_stability)``.
    4. **Sort** descending by score.
    5. **Priority tie-break** via market hierarchy:
       Over/Under → BTTS → Team Goals → Asian Handicap → 1X2.
    6. **Cap** at ``max_results`` (default 5).

    Parameters
    ----------
    ai_evaluated_markets : list of dict
        Each dict requires at least::

            {
                "ev_final": float,
                "p_model": float,
                "stability_home": float,
                "stability_away": float,
                "market_key": str,   # e.g. "over_2.5", "1x2_home"
                ...
            }
    min_ev : float
        Minimum ``ev_final`` threshold (default 0.05 = +5 %).
    min_p_model : float
        Minimum model probability (default 0.35).
    max_results : int
        Maximum number of picks to return (default 5).

    Returns
    -------
    list of dict
        Each pick dict includes the original market data plus::

            {
                "score": float,
                "market_priority": int,
                "rank": int,
                ...
            }
    """
    # ── Step 1 & 2: Strict filters ──────────────────────────────────────
    candidates = []
    for market in ai_evaluated_markets:
        ev_final = market.get("ev_final")
        p_model  = market.get("p_model", 0.0) or 0.0

        if ev_final is None:
            continue
        if ev_final <= min_ev:
            continue
        if p_model <= min_p_model:
            continue

        candidates.append(market)

    if not candidates:
        return []

    # ── Step 3: Score each candidate ─────────────────────────────────────
    scored = []
    for market in candidates:
        stab_h = market.get("stability_home", 1.5) or 1.5
        stab_a = market.get("stability_away", 1.5) or 1.5
        avg_stability = (stab_h + stab_a) / 2.0

        # Guard against division by zero (clamp to a large value)
        if avg_stability < 0.001:
            avg_stability = 0.001

        ev_final = market["ev_final"]
        score = ev_final * (1.0 / avg_stability)

        market_key = market.get("market_key", "unknown")
        priority = _infer_market_priority(market_key)

        # ── Fractional Kelly stake ───────────────────────────────────────
        p_model = market.get("p_model", 0.0) or 0.0
        odds    = market.get("odds", 0.0) or 0.0
        recommended_stake_fraction = calculate_kelly_fraction(
            p_model=p_model, decimal_odds=odds,
        )

        scored.append({
            **market,
            "score":                     round(score, 6),
            "market_priority":           priority,
            "avg_stability":             round(avg_stability, 4),
            "recommended_stake_fraction": recommended_stake_fraction,
        })

    # ── Step 4 & 5: Sort by score DESC, then priority ASC ───────────────
    scored.sort(key=lambda x: (-x["score"], x["market_priority"]))

    # ── Step 6: Cap results and attach rank ─────────────────────────────
    final = scored[:max_results]
    for i, pick in enumerate(final):
        pick["rank"] = i + 1

    return final
