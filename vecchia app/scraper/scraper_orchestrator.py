#!/usr/bin/env python3
"""
Scraping orchestrator for xPalermoStat.

This module monitors finished matches, triggers shot‑data scraping from Understat,
updates the database with shot details, and maintains scraping status flags.

Usage:
    python -m app.scraper.scraper_orchestrator   # run once
    # or schedule as a cron job every 5 minutes.
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal
from app.db.models import Match, Shot
from app.scraper.understat_engine import get_understat_match_shots

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Scraping status constants
STATUS_PENDING = 'PENDING'
STATUS_PROCESSING = 'PROCESSING'
STATUS_SUCCESS = 'SUCCESS'
STATUS_FAILED = 'FAILED'
STATUS_RETRYING = 'RETRYING'

# Maximum number of retries for a failed match
MAX_RETRIES = 3
# How long to wait before retrying a failed match (minutes)
RETRY_DELAY_MINUTES = 10


async def fetch_pending_matches(session: AsyncSession) -> List[Match]:
    """
    Retrieve matches that are ready for scraping.

    Criteria:
        - status = 'finito' (match is finished)
        - scraping_status in ('PENDING', 'RETRYING')
        - understat_id IS NOT NULL
        - last_scraped_at is NULL OR (scraping_status = 'FAILED' AND last_scraped_at older than RETRY_DELAY)
    """
    stmt = (
        select(Match)
        .where(Match.status == 'finito')
        .where(Match.understat_id.isnot(None))
        .where(
            (Match.scraping_status == STATUS_PENDING) |
            (Match.scraping_status == STATUS_RETRYING) |
            (
                (Match.scraping_status == STATUS_FAILED) &
                (Match.last_scraped_at < datetime.utcnow() - timedelta(minutes=RETRY_DELAY_MINUTES))
            )
        )
        .order_by(Match.start_time.asc())
        .limit(10)  # process at most 10 matches per run
    )
    result = await session.execute(stmt)
    matches = result.scalars().all()
    logger.info(f"Found {len(matches)} matches ready for scraping")
    return matches


async def update_scraping_status(
    session: AsyncSession,
    match_id: int,
    status: str,
    error_msg: Optional[str] = None,
) -> None:
    """
    Update the scraping status and timestamp of a match.
    If error_msg is provided, store it in error_log.
    """
    values = {
        'scraping_status': status,
        'last_scraped_at': datetime.utcnow(),
    }
    if error_msg:
        values['error_log'] = error_msg
    elif status == STATUS_SUCCESS:
        # Clear previous error log on success
        values['error_log'] = None

    stmt = (
        update(Match)
        .where(Match.id == match_id)
        .values(**values)
    )
    await session.execute(stmt)
    await session.commit()
    logger.debug(f"Updated match {match_id} scraping_status to {status}")


async def normalize_coordinates(shot: dict) -> tuple[float, float]:
    """
    Normalize Understat's (X, Y) coordinates to our frontend coordinate system.

    Understat provides X (horizontal) and Y (vertical) as percentages (0‑100)
    where (0,0) is top‑left corner of the pitch and (100,100) is bottom‑right.
    Our frontend SVG uses the same coordinate system, so no transformation is needed.
    However we ensure values are within 0‑100 and convert to float.
    """
    x = float(shot.get('X', 0.0))
    y = float(shot.get('Y', 0.0))
    # Clamp to 0‑100 (just in case)
    x = max(0.0, min(100.0, x))
    y = max(0.0, min(100.0, y))
    return x, y


async def process_match(session: AsyncSession, match: Match) -> bool:
    """
    Fetch shot data for a single match, insert shots, and update match stats.

    Returns True on success, False on failure.
    """
    understat_id = match.understat_id
    logger.info(f"Processing match {match.id} (Understat ID {understat_id})")

    try:
        # Fetch raw shot data from Understat
        raw_data = await asyncio.to_thread(get_understat_match_shots, understat_id)
    except Exception as e:
        logger.error(f"Failed to fetch shot data for match {match.id}: {e}")
        await update_scraping_status(
            session, match.id, STATUS_FAILED,
            error_msg=f"Network/API error: {e}"
        )
        return False

    # Validate response structure
    if not isinstance(raw_data, dict) or 'h' not in raw_data or 'a' not in raw_data:
        logger.error(f"Unexpected shot data structure for match {match.id}: {raw_data}")
        await update_scraping_status(
            session, match.id, STATUS_FAILED,
            error_msg=f"Invalid data structure: missing 'h'/'a' keys"
        )
        return False

    home_shots = raw_data.get('h', [])
    away_shots = raw_data.get('a', [])
    logger.info(f"Retrieved {len(home_shots)} home shots, {len(away_shots)} away shots")

    # Delete existing shots for this match (if any) to avoid duplicates
    delete_stmt = Shot.__table__.delete().where(Shot.match_id == match.id)
    await session.execute(delete_stmt)

    # Insert new shots
    shots_to_insert = []
    home_xg_total = 0.0
    away_xg_total = 0.0
    home_shots_count = 0
    away_shots_count = 0
    home_shots_on_target = 0
    away_shots_on_target = 0

    # Helper to determine if a shot is on target
    def is_on_target(result: str) -> bool:
        return result in ('Goal', 'Saved')

    for shot_list, team_type in [(home_shots, 'home'), (away_shots, 'away')]:
        for raw_shot in shot_list:
            # Normalize coordinates
            x, y = await normalize_coordinates(raw_shot)
            xg = float(raw_shot.get('xG', 0.0))
            minute = int(raw_shot.get('minute', 0))
            player = raw_shot.get('player', '')
            result = raw_shot.get('result', '')

            if team_type == 'home':
                home_xg_total += xg
                home_shots_count += 1
                if is_on_target(result):
                    home_shots_on_target += 1
            else:
                away_xg_total += xg
                away_shots_count += 1
                if is_on_target(result):
                    away_shots_on_target += 1

            shots_to_insert.append({
                'match_id': match.id,
                'minute': minute,
                'player': player,
                'xG': xg,
                'result': result,
                'team_type': team_type,
                'X': x,
                'Y': y,
            })

    if shots_to_insert:
        # Bulk insert using SQLAlchemy Core for performance
        await session.execute(insert(Shot.__table__), shots_to_insert)
        logger.info(f"Inserted {len(shots_to_insert)} shots for match {match.id}")

    # Update match with aggregated stats
    match.home_xg = home_xg_total
    match.away_xg = away_xg_total
    match.home_shots = home_shots_count
    match.away_shots = away_shots_count
    match.home_shots_on_target = home_shots_on_target
    match.away_shots_on_target = away_shots_on_target
    # If match scores are missing, we could try to extract from shot results (goal shots)
    # but Understat does not provide final score in shot data.
    # We'll keep existing home_score/away_score.

    # Mark scraping as successful
    await update_scraping_status(session, match.id, STATUS_SUCCESS)
    logger.info(f"Successfully processed match {match.id}")
    return True


async def run_once() -> None:
    """Single orchestration cycle: find pending matches, scrape each one."""
    async with AsyncSessionLocal() as session:
        matches = await fetch_pending_matches(session)
        if not matches:
            logger.info("No pending matches to scrape")
            return

        for match in matches:
            # Set status to PROCESSING
            await update_scraping_status(session, match.id, STATUS_PROCESSING)
            success = await process_match(session, match)
            if not success:
                # If failed, decide whether to retry later based on retry count
                # For simplicity, we'll keep FAILED status; the next run will retry after delay.
                pass
            # Small delay between matches to avoid rate‑limiting
            await asyncio.sleep(1)


async def main() -> None:
    """Main entry point for standalone script execution."""
    logger.info("Starting scraper orchestrator")
    try:
        await run_once()
        logger.info("Scraping cycle completed")
    except Exception as e:
        logger.error(f"Unhandled error in orchestrator: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())