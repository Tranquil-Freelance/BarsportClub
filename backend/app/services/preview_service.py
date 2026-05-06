"""
Upcoming Match Preview Service
================================
Phase 1: Backend Data Aggregation & AI Verdict.

Queries the database for upcoming matches, calculates average stats from
the last 5 completed matches for both teams (xG), enriches with seasonal
PPDA/deep-completion data, constructs a strictly data-driven prompt,
sends it to the configured AI provider, and saves the generated preview
into the `ai_verdict` column of `matchcalendar`.
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# AI Provider configuration
# ---------------------------------------------------------------------------
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def get_upcoming_matches(
    session: AsyncSession, limit: int = 20
) -> List[Dict[str, Any]]:
    """Return upcoming matches (is_completed=False, datetime in the future)."""
    now = datetime.now(timezone.utc)
    query = text(
        """
        SELECT id, league_id, home_team_id, away_team_id,
               match_datetime, "round"
        FROM matchcalendar
        WHERE is_completed = false
          AND match_datetime > :now
        ORDER BY match_datetime ASC
        LIMIT :limit
        """
    )
    rows = await session.execute(query, {"now": now, "limit": limit})
    return [
        {
            "id": r[0],
            "league_id": r[1],
            "home_team_id": r[2],
            "away_team_id": r[3],
            "match_datetime": r[4],
            "round": r[5],
        }
        for r in rows
    ]


async def get_last_n_completed_avg(
    session: AsyncSession, team_id: int, n: int = 5
) -> Dict[str, float]:
    """
    Calculate average xG, goals, PPDA, and deep completions from the last `n`
    completed matches for a given team. All stats come from matchcalendar directly.
    """
    query = text(
        """
        SELECT
            AVG(CASE
                WHEN home_team_id = :team_id THEN "home_xG"
                ELSE "away_xG"
            END) AS avg_xG,
            AVG(CASE
                WHEN home_team_id = :team_id THEN "away_xG"
                ELSE "home_xG"
            END) AS avg_xG_conceded,
            AVG(CASE
                WHEN home_team_id = :team_id THEN home_goals
                ELSE away_goals
            END) AS avg_goals_scored,
            AVG(CASE
                WHEN home_team_id = :team_id THEN away_goals
                ELSE home_goals
            END) AS avg_goals_conceded,
            AVG(CASE
                WHEN home_team_id = :team_id THEN home_ppda
                ELSE away_ppda
            END) AS avg_ppda,
            AVG(CASE
                WHEN home_team_id = :team_id THEN home_deep
                ELSE away_deep
            END) AS avg_deep
        FROM (
            SELECT *
            FROM matchcalendar
            WHERE (home_team_id = :team_id OR away_team_id = :team_id)
              AND is_completed = true
              AND "home_xG" IS NOT NULL
            ORDER BY match_datetime DESC
            LIMIT :n
        ) AS recent
        """
    )
    result = await session.execute(
        query, {"team_id": team_id, "n": n}
    )
    row = result.fetchone()
    return {
        "avg_xG": round(float(row[0] or 0.0), 3),
        "avg_xG_conceded": round(float(row[1] or 0.0), 3),
        "avg_goals_scored": round(float(row[2] or 0.0), 1),
        "avg_goals_conceded": round(float(row[3] or 0.0), 1),
        "ppda": round(float(row[4]), 1) if row[4] is not None else None,
        "deep_completions": int(row[5]) if row[5] is not None else None,
    }


async def get_team_season_stats(
    session: AsyncSession, team_id: int
) -> Dict[str, float]:
    """Retrieve the most recent seasonal PPDA & deep_completions for a team."""
    query = text(
        """
        SELECT ppda, deep_completions
        FROM team_season_stat
        WHERE team_id = :team_id
          AND ppda IS NOT NULL
        ORDER BY id DESC
        LIMIT 1
        """
    )
    result = await session.execute(query, {"team_id": team_id})
    row = result.fetchone()
    if row:
        return {
            "ppda": round(float(row[0] or 0.0), 1),
            "deep_completions": int(row[1] or 0),
        }
    logger.warning("No team_season_stat row for team_id=%s; using defaults", team_id)
    return {"ppda": 10.0, "deep_completions": 50}


async def get_team_name(session: AsyncSession, team_id: int) -> str:
    """Resolve team ID to display name."""
    result = await session.execute(
        text("SELECT name FROM team WHERE id = :id"), {"id": team_id}
    )
    row = result.fetchone()
    return row[0] if row else f"Team_{team_id}"


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


def build_preview_prompt(
    home_team: str,
    away_team: str,
    home_stats: Dict[str, float],
    away_stats: Dict[str, float],
) -> str:
    """Build a strictly data-driven prompt – no external knowledge allowed."""
    return f"""You are a professional football tactical analyst. Generate a match preview for:

{home_team} vs {away_team}

You MUST base your analysis EXCLUSIVELY on the data below. Do NOT use any external knowledge, reputation, or historical context about these teams.

=== DATA: Last 5 completed matches averages ===

**{home_team} (Home Team)**
- Avg xG scored: {home_stats['avg_xG']:.3f}
- Avg xG conceded: {home_stats['avg_xG_conceded']:.3f}
- Avg goals scored: {home_stats['avg_goals_scored']:.1f}
- Avg goals conceded: {home_stats['avg_goals_conceded']:.1f}
- PPDA (passes per defensive action): {home_stats['ppda']:.1f}
- Deep completions (passes into final third): {home_stats['deep_completions']}

**{away_team} (Away Team)**
- Avg xG scored: {away_stats['avg_xG']:.3f}
- Avg xG conceded: {away_stats['avg_xG_conceded']:.3f}
- Avg goals scored: {away_stats['avg_goals_scored']:.1f}
- Avg goals conceded: {away_stats['avg_goals_conceded']:.1f}
- PPDA (passes per defensive action): {away_stats['ppda']:.1f}
- Deep completions (passes into final third): {away_stats['deep_completions']}

=== INSTRUCTIONS ===

Write exactly 3 paragraphs in Italian:

1. **Analisi tattica**: Analyse the tactical matchup. Compare xG differentials (scored vs conceded). What does the PPDA gap tell us about pressing intensity? Who creates more deep completions? Be specific with numbers.

2. **Punti di forza/debolezza**: Identify each team's edge. Which team creates more xG? Which concedes more? Who defends deeper (fewer deep completions conceded)? Who presses higher (lower PPDA)?

3. **Pronostico**: Give a data-driven prediction. Which team is favoured by the numbers? Expected goal total? Key tactical battle that will decide the match.

CRITICAL RULES:
- Base EVERY claim on the data above — cite specific numbers.
- Do NOT speculate beyond what the data shows.
- Write in Italian, technical tone, like a Coverciano analyst.
- 3 paragraphs only, no title, no markdown formatting."""


# ---------------------------------------------------------------------------
# AI provider dispatch
# ---------------------------------------------------------------------------


async def _call_deepseek(prompt: str) -> Optional[str]:
    """Call DeepSeek Chat via OpenAI-compatible async API."""
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com",
        )
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional football tactical analyst. "
                        "You always base your analysis strictly on the data "
                        "provided and respond in Italian."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1200,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("AI Gen Failed [DeepSeek]: %s", str(exc), exc_info=True)
        return None


async def _call_openai(prompt: str) -> Optional[str]:
    """Call OpenAI GPT via async API."""
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional football tactical analyst. "
                        "You always base your analysis strictly on the data "
                        "provided and respond in Italian."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1200,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("AI Gen Failed [OpenAI]: %s", str(exc), exc_info=True)
        return None


async def call_ai_provider(prompt: str) -> Optional[str]:
    """
    Dispatch to the configured AI provider.

    Priority: DeepSeek → OpenAI.
    """
    if not DEEPSEEK_API_KEY and not OPENAI_API_KEY:
        logger.error(
            "AI Gen Failed: no API keys configured. "
            "Set DEEPSEEK_API_KEY or OPENAI_API_KEY in the environment."
        )
        return None

    if DEEPSEEK_API_KEY:
        logger.info("AI verdict: calling DeepSeek (key prefix=%s...)", DEEPSEEK_API_KEY[:6])
        result = await _call_deepseek(prompt)
        if result:
            logger.info("AI verdict: DeepSeek returned %d chars", len(result))
            return result
        logger.error("AI Gen Failed: DeepSeek returned None, trying OpenAI fallback...")

    if OPENAI_API_KEY:
        logger.info("AI verdict: calling OpenAI (key prefix=%s...)", OPENAI_API_KEY[:6])
        result = await _call_openai(prompt)
        if result:
            logger.info("AI verdict: OpenAI returned %d chars", len(result))
            return result
        logger.error("AI Gen Failed: OpenAI also returned None. Both providers failed.")

    return None


# ---------------------------------------------------------------------------
# Core orchestration
# ---------------------------------------------------------------------------


async def generate_preview_for_match(
    match_id: int, session: AsyncSession
) -> Optional[str]:
    """
    Generate and persist an AI preview for a specific match.

    Steps
    -----
    1. Fetch match & team info
    2. Compute last-5 averages for both teams
    3. Fetch seasonal PPDA/deep data
    4. Build data-driven prompt
    5. Call AI provider
    6. Save result into ``matchcalendar.ai_verdict``

    Returns
    -------
    The generated preview text, or ``None`` on failure.
    """
    # -- 1. Match info ----------------------------------------------------
    match_row = await session.execute(
        text(
            """
            SELECT id, league_id, home_team_id, away_team_id, match_datetime
            FROM matchcalendar WHERE id = :id
            """
        ),
        {"id": match_id},
    )
    match = match_row.fetchone()
    if not match:
        logger.error("Match %s not found in matchcalendar", match_id)
        return None

    home_id, away_id = match[2], match[3]

    # -- 2. Team names ----------------------------------------------------
    home_team = await get_team_name(session, home_id)
    away_team = await get_team_name(session, away_id)

    # -- 3. Last-5 averages -----------------------------------------------
    home_stats = await get_last_n_completed_avg(session, home_id, n=5)
    away_stats = await get_last_n_completed_avg(session, away_id, n=5)

    # -- 4. Seasonal PPDA / deep completions ------------------------------
    home_season = await get_team_season_stats(session, home_id)
    away_season = await get_team_season_stats(session, away_id)
    home_stats.update(home_season)
    away_stats.update(away_season)

    # -- 5. Build prompt --------------------------------------------------
    prompt = build_preview_prompt(home_team, away_team, home_stats, away_stats)

    logger.info(
        "Prompt built for %s vs %s (match_id=%s)",
        home_team,
        away_team,
        match_id,
    )
    logger.debug("Prompt:\n%s", prompt)

    # -- 6. Call AI -------------------------------------------------------
    verdict = await call_ai_provider(prompt)

    if verdict:
        # -- 7. Persist ---------------------------------------------------
        await session.execute(
            text(
                """
                UPDATE matchcalendar
                SET "ai_verdict" = :verdict
                WHERE id = :id
                """
            ),
            {"verdict": verdict, "id": match_id},
        )
        logger.info("AI verdict saved for match %s (%s vs %s)", match_id, home_team, away_team)
    else:
        logger.warning("No AI verdict generated for match %s", match_id)

    return verdict


async def generate_previews_for_all_upcoming(
    session: AsyncSession, limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Generate previews for the next N upcoming matches.

    Returns a list of dicts with match info and the generated preview.
    """
    upcoming = await get_upcoming_matches(session, limit=limit)
    results = []

    for match in upcoming:
        mid = match["id"]
        logger.info("Processing upcoming match %s...", mid)
        verdict = await generate_preview_for_match(mid, session)
        await session.commit()
        results.append(
            {
                "match_id": mid,
                "home_team_id": match["home_team_id"],
                "away_team_id": match["away_team_id"],
                "datetime": match["match_datetime"].isoformat(),
                "preview": verdict,
            }
        )

    return results
