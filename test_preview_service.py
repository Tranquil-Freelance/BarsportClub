"""
Test script for Phase 1: Upcoming Match Preview Service.

Validates the data pipeline:
  1. Query upcoming matches from the database
  2. Calculate average stats from last 5 completed matches for both teams
  3. Enrich with seasonal PPDA / deep completions
  4. Build the data-driven prompt
  5. Call the AI provider (or mock, if no keys are set)
  6. Save the verdict into matchcalendar.ai_verdict
  7. Verify it was persisted

Usage:
  set PYTHONIOENCODING=utf-8
  python test_preview_service.py
"""

import asyncio
import json
import os
import sys

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# ---------------------------------------------------------------------------
# Test configuration
# ---------------------------------------------------------------------------
DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/xpalermostat_db"

# If you have an API key, set it here or in environment variables.
# The test falls back to a local mock if no key is configured.
os.environ.setdefault("DEEPSEEK_API_KEY", "")
os.environ.setdefault("OPENAI_API_KEY", "")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_MOCK = not (DEEPSEEK_API_KEY or OPENAI_API_KEY)


# ═══════════════════════════════════════════════════════════════════════════
# Mock AI provider for testing when no API keys are available
# ═══════════════════════════════════════════════════════════════════════════


def _mock_ai_verdict(
    home: str, away: str, hs: dict, aws: dict
) -> str:
    """Generate a deterministic mock preview purely from the data."""
    xg_edge = abs(hs["avg_xG"] - aws["avg_xG_conceded"])
    ppda_note = (
        f"{home} pressa piu' alto (PPDA {hs['ppda']})"
        if hs["ppda"] < aws["ppda"]
        else f"{away} pressa piu' alto (PPDA {aws['ppda']})"
    )
    deep_note = (
        f"{home} produce piu' passaggi profondi ({hs['deep_completions']})"
        if hs["deep_completions"] > aws["deep_completions"]
        else f"{away} produce piu' passaggi profondi ({aws['deep_completions']})"
    )

    return (
        f"**Analisi tattica**\n"
        f"Sulla base dei dati delle ultime 5 partite, {home} registra una media xG "
        f"di {hs['avg_xG']:.3f} contro {aws['avg_xG']:.3f} di {away}. "
        f"La differenza xG attacco-difesa e' di {xg_edge:.3f} a favore di "
        f"{home if hs['avg_xG'] > aws['avg_xG_conceded'] else away}. "
        f"{ppda_note}. {deep_note}.\n\n"
        f"**Punti di forza/debolezza**\n"
        f"{home}: xG segnato {hs['avg_xG']:.3f}, xG concesso {hs['avg_xG_conceded']:.3f}, "
        f"PPDA {hs['ppda']:.1f}, passaggi profondi {hs['deep_completions']}. "
        f"{away}: xG segnato {aws['avg_xG']:.3f}, xG concesso {aws['avg_xG_conceded']:.3f}, "
        f"PPDA {aws['ppda']:.1f}, passaggi profondi {aws['deep_completions']}.\n\n"
        f"**Pronostico**\n"
        f"Media gol totali: {(hs['avg_goals_scored'] + aws['avg_goals_scored']):.1f}. "
        f"xG combinata: {(hs['avg_xG'] + aws['avg_xG']):.3f}. "
        f"Battaglia chiave: {home if abs(hs['ppda'] - aws['ppda']) > 2 else away} "
        f"nel pressing centrale."
    )


# ═══════════════════════════════════════════════════════════════════════════
# Test functions
# ═══════════════════════════════════════════════════════════════════════════


async def test_data_query(session):
    """Step 1: Query upcoming matches and show them."""
    print("=" * 72)
    print("STEP 1: Query upcoming matches")
    print("=" * 72)

    from app.services.preview_service import get_upcoming_matches

    upcoming = await get_upcoming_matches(session, limit=5)
    print(f"Found {len(upcoming)} upcoming matches:\n")

    if not upcoming:
        print("  WARNING: No upcoming matches found in the database.")
        print("  The test will use a fallback match ID.")
        return None

    for m in upcoming:
        # Resolve team names
        from app.services.preview_service import get_team_name

        home = await get_team_name(session, m["home_team_id"])
        away = await get_team_name(session, m["away_team_id"])
        print(
            f"  Match {m['id']}: {home} (id={m['home_team_id']}) vs "
            f"{away} (id={m['away_team_id']})"
        )
        print(f"           Date: {m['match_datetime']}")
        print()

    return upcoming[0]  # Return the first upcoming match


async def test_stats_aggregation(session, match):
    """Step 2 & 3: Calculate averages and seasonal stats."""
    print("=" * 72)
    print("STEP 2 & 3: Calculate aggregated stats")
    print("=" * 72)

    from app.services.preview_service import (
        get_last_n_completed_avg,
        get_team_season_stats,
        get_team_name,
    )

    home_id = match["home_team_id"]
    away_id = match["away_team_id"]
    home_name = await get_team_name(session, home_id)
    away_name = await get_team_name(session, away_id)

    # Last 5 averages
    print("\n  [Last 5 completed matches averages]")
    home_avg = await get_last_n_completed_avg(session, home_id, 5)
    away_avg = await get_last_n_completed_avg(session, away_id, 5)

    print(f"\n  {home_name}:")
    for k, v in home_avg.items():
        print(f"    {k}: {v}")
    print(f"\n  {away_name}:")
    for k, v in away_avg.items():
        print(f"    {k}: {v}")

    # Seasonal PPDA / deep
    print("\n  [Seasonal PPDA & Deep Completions]")
    home_season = await get_team_season_stats(session, home_id)
    away_season = await get_team_season_stats(session, away_id)

    print(f"\n  {home_name}: PPDA={home_season['ppda']}, Deep={home_season['deep_completions']}")
    print(f"  {away_name}: PPDA={away_season['ppda']}, Deep={away_season['deep_completions']}")

    # Merge
    home_avg.update(home_season)
    away_avg.update(away_season)

    return home_name, away_name, home_avg, away_avg


def test_prompt_construction(home_name, away_name, home_stats, away_stats):
    """Step 4: Test the prompt builder."""
    print("=" * 72)
    print("STEP 4: Prompt construction")
    print("=" * 72)

    from app.services.preview_service import build_preview_prompt

    prompt = build_preview_prompt(home_name, away_name, home_stats, away_stats)

    print("\n  Generated prompt:\n")
    print("  " + prompt.replace("\n", "\n  "))
    print()
    print(f"  Prompt length: {len(prompt)} characters")

    return prompt


async def test_ai_call_and_persist(session, match, prompt, home_name, away_name):
    """Step 5 & 6 & 7: Call AI, save, verify."""
    print("=" * 72)
    print("STEP 5 & 6 & 7: AI call, persist, verify")
    print("=" * 72)

    match_id = match["id"]

    if USE_MOCK:
        print("\n  No AI API keys found. Using MOCK provider.")
        print(f"  Set DEEPSEEK_API_KEY or OPENAI_API_KEY for real AI calls.\n")

        hs = await get_home_away_stats(session, match)
        verdict = _mock_ai_verdict(home_name, away_name, hs["home"], hs["away"])
    else:
        from app.services.preview_service import call_ai_provider

        print("\n  Calling AI provider...")
        verdict = await call_ai_provider(prompt)
        if not verdict:
            print("  AI provider returned None. Falling back to mock.")
            hs = await get_home_away_stats(session, match)
            verdict = _mock_ai_verdict(home_name, away_name, hs["home"], hs["away"])

    # --- Persist into database ---
    print("\n  Generated preview text:\n")
    print("  " + verdict.replace("\n", "\n  "))
    print()

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
    await session.commit()
    print(f"  Preview saved to matchcalendar.ai_verdict for match_id={match_id}")

    # --- Verify persistence ---
    result = await session.execute(
        text(
            """
            SELECT id, "ai_verdict"
            FROM matchcalendar
            WHERE id = :id
            """
        ),
        {"id": match_id},
    )
    row = result.fetchone()
    if row and row[1]:
        print(f"\n  ✅ VERIFIED: ai_verdict is populated (first 120 chars):")
        print(f"     {row[1][:120]}...")
    else:
        print(f"\n  ❌ FAILED: ai_verdict is NULL or empty for match_id={match_id}")

    return verdict


async def get_home_away_stats(session, match):
    """Helper to get merged stats for both teams."""
    from app.services.preview_service import (
        get_last_n_completed_avg,
        get_team_season_stats,
    )

    home_id = match["home_team_id"]
    away_id = match["away_team_id"]

    hs = await get_last_n_completed_avg(session, home_id, 5)
    aws = await get_last_n_completed_avg(session, away_id, 5)

    hs.update(await get_team_season_stats(session, home_id))
    aws.update(await get_team_season_stats(session, away_id))

    return {"home": hs, "away": aws}


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════


async def main():
    engine = create_async_engine(DB_URL, echo=False)

    async with engine.connect() as session:
        # STEP 1
        match = await test_data_query(session)
        if match is None:
            print("No upcoming matches; cannot continue.")
            return

        # STEP 2 & 3
        home_name, away_name, home_stats, away_stats = await test_stats_aggregation(
            session, match
        )

        # STEP 4
        prompt = test_prompt_construction(
            home_name, away_name, home_stats, away_stats
        )

        # STEP 5, 6, 7
        verdict = await test_ai_call_and_persist(
            session, match, prompt, home_name, away_name
        )

    print("\n" + "=" * 72)
    print("TEST COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    asyncio.run(main())
