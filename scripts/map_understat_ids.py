#!/usr/bin/env python3
"""
Mapping script for Understat match IDs for Serie A season 2025/26.

This script fetches the season calendar from Understat, extracts match IDs,
and inserts/updates the matches table in the database with understat_id,
start_time, status, and basic match info.

Usage:
    python scripts/map_understat_ids.py
"""

import asyncio
import sys
import logging
from datetime import datetime
from typing import List, Dict, Any


from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.db.database import AsyncSessionLocal
from app.db.models import Match
from app.scraper.understat_parser import get_league_season_data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def fetch_understat_calendar() -> List[Dict[str, Any]]:
    """Fetch Serie A 2025/26 calendar from Understat."""
    league_slug = 'serie_a'
    season_year = 2025  # season starting in 2025 (2025/26) - Understat uses start year
    logger.info(f"Fetching calendar for {league_slug} season {season_year}")
    try:
        data = await get_league_season_data(league_slug, season_year)
        logger.info(f"Retrieved {len(data)} match entries")
        return data
    except Exception as e:
        logger.error(f"Failed to fetch Understat calendar: {e}")
        raise


async def upsert_matches(session, matches_data: List[Dict[str, Any]]) -> int:
    """
    Insert or update matches in the database.

    For each match entry, we map Understat fields to our Match model:
        - understat_id → understat_id (unique)
        - datetime → start_time (and date)
        - home_team_name → home_team
        - away_team_name → away_team
        - home_goals → home_score (if present)
        - away_goals → away_score (if present)
        - home_xg → home_xg (if present)
        - away_xg → away_xg (if present)
        - is_completed → status ('finito' if True else 'programmato')
        - matchday → left as NULL (Understat does not provide round)
        - scraping_status → 'PENDING' for finished matches, else 'PENDING'
        - last_scraped_at → NULL
        - error_log → NULL
    """
    updated = 0
    inserted = 0
    skipped = 0
    # Debug Match attributes
    import sys
    logger.info(f"Match module: {Match.__module__}")
    logger.info(f"Match class: {Match}")
    logger.info(f"Match.__table__: {Match.__table__}")
    if hasattr(Match, '__table__') and Match.__table__ is not None:
        logger.info(f"Table columns: {[c.name for c in Match.__table__.c]}")
    if hasattr(Match, '__mapper__'):
        logger.info(f"Mapper columns: {[c.key for c in Match.__mapper__.columns]}")
    logger.info(f"Match attributes (non-private): {[attr for attr in dir(Match) if not attr.startswith('_')]}")

    for entry in matches_data:
        understat_id = entry.get('id')
        if not understat_id:
            logger.warning(f"Entry missing 'id', skipping: {entry}")
            skipped += 1
            continue
        try:
            understat_id = int(understat_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid understat_id '{understat_id}', skipping")
            skipped += 1
            continue

        # Extract nested fields
        home_team = entry.get('h', {})
        away_team = entry.get('a', {})
        home_team_name = home_team.get('title') if isinstance(home_team, dict) else None
        away_team_name = away_team.get('title') if isinstance(away_team, dict) else None
        if not home_team_name or not away_team_name:
            logger.warning(f"Missing team names for match {understat_id}, skipping")
            skipped += 1
            continue

        # Parse datetime
        dt_str = entry.get('datetime')
        start_time = None
        if dt_str:
            try:
                # Understat datetime format: "2025-08-17 14:45:00"
                start_time = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid datetime '{dt_str}' for match {understat_id}: {e}")

        # Determine status
        is_completed = entry.get('isResult', False)
        status = 'finito' if is_completed else 'programmato'

        # Extract goals
        goals = entry.get('goals', {})
        home_score_raw = goals.get('h') if isinstance(goals, dict) else None
        away_score_raw = goals.get('a') if isinstance(goals, dict) else None
        home_score = None
        away_score = None
        if home_score_raw is not None:
            try:
                home_score = int(home_score_raw)
            except (ValueError, TypeError):
                logger.warning(f"Invalid home_score '{home_score_raw}' for match {understat_id}, treating as NULL")
        if away_score_raw is not None:
            try:
                away_score = int(away_score_raw)
            except (ValueError, TypeError):
                logger.warning(f"Invalid away_score '{away_score_raw}' for match {understat_id}, treating as NULL")

        # Extract xG
        xg = entry.get('xG', {})
        home_xg_raw = xg.get('h') if isinstance(xg, dict) else None
        away_xg_raw = xg.get('a') if isinstance(xg, dict) else None
        home_xg = None
        away_xg = None
        if home_xg_raw is not None:
            try:
                home_xg = float(home_xg_raw)
            except (ValueError, TypeError):
                logger.warning(f"Invalid home_xg '{home_xg_raw}' for match {understat_id}, treating as NULL")
        if away_xg_raw is not None:
            try:
                away_xg = float(away_xg_raw)
            except (ValueError, TypeError):
                logger.warning(f"Invalid away_xg '{away_xg_raw}' for match {understat_id}, treating as NULL")

        # Prepare values for upsert
        values = {
            'understat_id': understat_id,
            'home_team': home_team_name,
            'away_team': away_team_name,
            'home_score': home_score,
            'away_score': away_score,
            'home_xg': home_xg,
            'away_xg': away_xg,
            'date': start_time,  # keep legacy date column
            'start_time': start_time,
            'status': status,
            'matchday': None,  # not provided by Understat
            'last_scraped_at': None,
            'scraping_status': 'PENDING',
            'error_log': None,
            'home_shots': None,
            'away_shots': None,
            'home_shots_on_target': None,
            'away_shots_on_target': None,
        }

        # Try to find existing match by understat_id
        result = await session.execute(
            select(Match).where(Match.__table__.c.understat_id == understat_id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing match
            existing.home_team = home_team_name
            existing.away_team = away_team_name
            existing.home_score = home_score
            existing.away_score = away_score
            existing.home_xg = home_xg
            existing.away_xg = away_xg
            existing.date = start_time
            existing.start_time = start_time
            existing.status = status
            existing.matchday = None
            existing.last_scraped_at = None
            existing.scraping_status = 'PENDING'
            existing.error_log = None
            existing.home_shots = None
            existing.away_shots = None
            existing.home_shots_on_target = None
            existing.away_shots_on_target = None
            updated += 1
            logger.debug(f"Updated match {understat_id}: {home_team_name} vs {away_team_name}")
        else:
            # Insert new match
            match = Match(
                understat_id=understat_id,
                home_team=home_team_name,
                away_team=away_team_name,
                home_score=home_score,
                away_score=away_score,
                home_xg=home_xg,
                away_xg=away_xg,
                date=start_time,
                start_time=start_time,
                status=status,
                matchday=None,
                last_scraped_at=None,
                scraping_status='PENDING',
                error_log=None,
                home_shots=None,
                away_shots=None,
                home_shots_on_target=None,
                away_shots_on_target=None,
            )
            session.add(match)
            inserted += 1
            logger.debug(f"Inserted match {understat_id}: {home_team_name} vs {away_team_name}")

    # Commit after processing all entries
    await session.commit()

    # Count actual changes by querying before/after? For now, we'll just log.
    logger.info(f"Upserted matches for {len(matches_data)} entries")
    return len(matches_data)


async def main() -> None:
    """Main async entry point."""
    logger.info("Starting Understat ID mapping for Serie A 2025/26")
    try:
        # Fetch data from Understat
        matches_data = await fetch_understat_calendar()
        if not matches_data:
            logger.warning("No match data retrieved, exiting")
            return

        # Connect to database and upsert
        async with AsyncSessionLocal() as session:
            await upsert_matches(session, matches_data)

        logger.info("Mapping completed successfully")
    except Exception as e:
        logger.error(f"Mapping failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())