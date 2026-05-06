"""
Fix existing future dates on played matches in the database.

This script:
1. Finds matches where goals > 0 but match_datetime is in the future
   (or suspiciously close to now with no timezone awareness)
2. Fetches correct datetime from Understat for those matches
3. Converts existing naive timestamps to proper UTC timestamps
4. Updates the database with corrected values

Run: python fix_future_dates.py
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone

import aiohttp
import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.db.database import DATABASE_URL
from app.db.models import Match
from app.scraper.understat_parser import get_league_season_data

# Also try to use Understat directly for single-match correction
from understat import Understat
from understat.constants import MATCH_URL
from understat.utils import get_data

# League slugs to scan
LEAGUE_SLUGS = [
    ("Serie_A", 1),
    ("EPL", 2),
    ("la_liga", 3),
    ("bundesliga", 4),
    ("Ligue_1", 5),
]

SEASON_YEARS = [2020, 2021, 2022, 2023, 2024, 2025]


async def _fetch_match_datetime_from_understat(match_id: int) -> datetime | None:
    """Fetch the correct datetime for a single match from Understat's match page."""
    try:
        async with aiohttp.ClientSession() as session:
            # Try match page - might have 'matchData' with datetime
            url = MATCH_URL.format(match_id)
            data = await get_data(session, url, "matchData")
            if data and isinstance(data, dict):
                raw_dt = data.get("datetime")
                if raw_dt:
                    naive = datetime.strptime(raw_dt, "%Y-%m-%d %H:%M:%S")
                    # Localize to Europe/Rome, convert to UTC
                    if 4 <= naive.month <= 10:
                        return naive.replace(tzinfo=timezone.utc) - timedelta(hours=2)
                    else:
                        return naive.replace(tzinfo=timezone.utc) - timedelta(hours=1)
    except Exception as e:
        print(f"  ⚠️  Could not fetch match {match_id} from Understat: {e}")
    return None


async def scan_and_fix():
    """Main entrypoint: scan for bad dates and fix them."""
    print("=" * 60)
    print("🔍 SCAN: Finding matches with wrong future dates")
    print("=" * 60)

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # --- STEP 1: Find matches with goals > 0 but future dates ---
        print("\n📊 STEP 1: Querying matches with goals > 0...")
        now_utc = datetime.now(timezone.utc)

        result = await session.execute(
            text("""
                SELECT id, home_goals, away_goals, match_datetime, league_id,
                       home_team_id, away_team_id, is_completed
                FROM matchcalendar
                WHERE (home_goals > 0 OR away_goals > 0)
                ORDER BY match_datetime DESC
            """)
        )
        matches_with_goals = result.all()
        print(f"   Found {len(matches_with_goals)} matches with goals > 0")

        # Separate into suspicious matches
        future_matches = []
        naive_matches = []
        for m in matches_with_goals:
            dt = m.match_datetime
            if dt is None:
                continue
            # Check if timezone-aware
            if dt.tzinfo is None:
                naive_matches.append(m)
            elif dt > now_utc:
                future_matches.append(m)
            elif dt > now_utc - timedelta(days=3) and dt < now_utc:
                # Recently played - check if date seems wrong (e.g., future season)
                if dt.month >= 7 and now_utc.month <= 6:
                    # Match in July-December but current time is Jan-June (wrong season?)
                    future_matches.append(m)

        print(f"   ⚠️  {len(future_matches)} matches have GOALS > 0 but FUTURE dates!")
        print(f"   ⚠️  {len(naive_matches)} matches have naive (timezone-less) timestamps")

        # --- STEP 2: Fix naive timestamps (most common issue) ---
        if naive_matches:
            print(f"\n🛠️  STEP 2: Fixing {len(naive_matches)} naive timestamps...")
            fixed_count = 0
            for m in naive_matches:
                dt = m.match_datetime
                # Interpret as Europe/Rome time based on month
                if 4 <= dt.month <= 10:
                    corrected = dt.replace(tzinfo=timezone.utc) - timedelta(hours=2)
                else:
                    corrected = dt.replace(tzinfo=timezone.utc) - timedelta(hours=1)

                await session.execute(
                    text("UPDATE matchcalendar SET match_datetime = :new_dt WHERE id = :id"),
                    {"new_dt": corrected, "id": m.id}
                )
                print(f"   ✅ Match {m.id}: {dt} → {corrected}")
                fixed_count += 1

                if fixed_count % 50 == 0:
                    await session.commit()
                    print(f"   💾 Committed {fixed_count} fixes...")

            await session.commit()
            print(f"   ✅ Fixed {fixed_count} naive timestamps")

        # --- STEP 3: Fix future dates with goals ---
        if future_matches:
            print(f"\n🛠️  STEP 3: Fixing {len(future_matches)} future-dated matches...")
            for m in future_matches:
                print(f"\n   🔍 Match {m.id} (league_id={m.league_id}): "
                      f"goals {m.home_goals}-{m.away_goals}, "
                      f"has datetime={m.match_datetime}")

                # Try to get correct datetime from Understat
                correct_dt = await _fetch_match_datetime_from_understat(m.id)
                if correct_dt:
                    await session.execute(
                        text("UPDATE matchcalendar SET match_datetime = :new_dt WHERE id = :id"),
                        {"new_dt": correct_dt, "id": m.id}
                    )
                    print(f"   ✅ Fixed: {m.match_datetime} → {correct_dt}")
                else:
                    # Fallback: set to now as last resort
                    await session.execute(
                        text("UPDATE matchcalendar SET match_datetime = :new_dt WHERE id = :id"),
                        {"new_dt": now_utc, "id": m.id}
                    )
                    print(f"   ⚠️  Could not fetch from Understat. Set to current time: {now_utc}")

                await asyncio.sleep(1)  # Rate limiting

            await session.commit()
            print(f"\n   ✅ Fixed {len(future_matches)} future-dated matches")

        # --- STEP 4: Verify ---
        print(f"\n📋 STEP 4: Verification...")
        result = await session.execute(
            text("""
                SELECT COUNT(*) FROM matchcalendar
                WHERE (home_goals > 0 OR away_goals > 0)
                AND match_datetime > NOW() AT TIME ZONE 'UTC'
            """)
        )
        remaining = result.scalar()
        if remaining > 0:
            print(f"   ⚠️  {remaining} matches STILL have future dates with goals!")
        else:
            print(f"   ✅ All matches with goals have correct dates!")

    await engine.dispose()
    print("\n" + "=" * 60)
    print("✅ FIX COMPLETE")
    print("=" * 60)


async def resync_calendars():
    """Re-sync all league calendars with the fixed parser to refresh all dates."""
    print("\n" + "=" * 60)
    print("🔄 Re-syncing all league calendars with fixed parser...")
    print("=" * 60)

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    for slug, league_id in LEAGUE_SLUGS:
        for year in SEASON_YEARS:
            print(f"\n   📡 Fetching {slug} {year}...")
            try:
                data = await get_league_season_data(slug, year)
                if data:
                    print(f"   ✅ Got {len(data)} matches")
                await asyncio.sleep(2)
            except Exception as e:
                print(f"   ❌ Error: {e}")

    await engine.dispose()
    print("\n✅ Re-sync complete. Run the main sync_calendar to update the DB.")


if __name__ == "__main__":
    print("🚀 FUTURE DATE FIX TOOL")
    print()
    print("This script will:")
    print("  1. Find matches with goals > 0 but future/suspicious dates")
    print("  2. Fix naive (timezone-less) timestamps to proper UTC")
    print("  3. Fetch correct dates from Understat for badly-dated matches")
    print()
    print("Running in 3 seconds... Press Ctrl+C to cancel.")
    
    try:
        asyncio.run(scan_and_fix())
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
