"""
Understat library wrapper for xPalermoStat.

This module provides a simplified interface to the Understat scraper,
specifically for fetching Match 30116 (Cagliari vs Como, Serie A 2024/25).
"""

import asyncio
import logging
from typing import Dict, Any

from app.scraper.understat_engine import get_understat_match_shots
from scrapers.understat import UnderstatScraper
from app.services.understat_service import scrape_and_save_match
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
import aiohttp
from understat import Understat
from app.api.crud import save_match_shots

logger = logging.getLogger(__name__)

# Match ID for Cagliari vs Como (2024-09-22)
MATCH_30116 = 30116


def fetch_match_30116_raw() -> Dict[str, Any]:
    """
    Fetch raw shot data for Match 30116 using the low-level engine.
    
    Returns:
        Dictionary with keys 'h' (home shots) and 'a' (away shots).
    
    Raises:
        requests.exceptions.RequestException: If network request fails.
        ValueError: If data cannot be parsed.
    """
    logger.info(f"Fetching raw shot data for match {MATCH_30116}")
    return get_understat_match_shots(MATCH_30116)


def fetch_match_30116_full() -> Dict[str, Any]:
    """
    Fetch full match data (shots + metadata) using the high-level scraper.
    
    Returns:
        Dictionary with keys:
            - 'match_id' (int)
            - 'shots_data' (dict with 'h'/'a')
            - 'match_data' (dict with home_team, away_team, etc.)
    
    Raises:
        requests.exceptions.RequestException: If network request fails.
        ValueError: If required data cannot be extracted.
    """
    scraper = UnderstatScraper()
    logger.info(f"Scraping full match data for match {MATCH_30116}")
    return scraper.scrape_match(MATCH_30116)


async def save_match_30116() -> bool:
    """
    Scrape Match 30116 and upsert into the database.
    
    Returns:
        True if successful, False otherwise.
    
    Raises:
        Any exception raised by the underlying service.
    """
    logger.info(f"Scraping and saving match {MATCH_30116}")
    async with AsyncSessionLocal() as session:
        try:
            result = await scrape_and_save_match(session, MATCH_30116)
            logger.info(
                f"Saved match {result['match_id']}: "
                f"{result['home_team']} vs {result['away_team']}, "
                f"{result['total_shots']} total shots"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to save match {MATCH_30116}: {e}")
            return False


async def scrape_latest_como_match() -> bool:
    """
    Scrape the latest Como match (currently Match 30116) and save to database.
    This function is used by the scheduler and manual trigger.
    
    Returns:
        True if successful, False otherwise.
    """
    logger.info("Starting scrape of latest Como match (match 30116)")
    try:
        async with aiohttp.ClientSession() as session:
            understat = Understat(session)
            # Fetch shots data
            shots = await understat.get_match_shots(MATCH_30116)
            # Fetch match data for team names
            match = await understat.get_match_players(MATCH_30116)
            home_team = match.get('h', {}).get('title', 'Home')
            away_team = match.get('a', {}).get('title', 'Away')
            # Scale coordinates from 0.0-1.0 to 0-100
            scaled_shots = {'h': [], 'a': []}
            for team_key in ('h', 'a'):
                for shot in shots.get(team_key, []):
                    scaled_shot = shot.copy()
                    scaled_shot['X'] = round(float(shot['X']) * 100, 2)
                    scaled_shot['Y'] = round(float(shot['Y']) * 100, 2)
                    scaled_shots[team_key].append(scaled_shot)
            # Save to database
            async with AsyncSessionLocal() as db:
                await save_match_shots(db, MATCH_30116, home_team, away_team, scaled_shots)
            logger.info(f"Successfully saved {len(scaled_shots['h']) + len(scaled_shots['a'])} shots for match {MATCH_30116}")
            return True
    except Exception as e:
        logger.error(f"Failed to scrape match {MATCH_30116}: {e}")
        return False


# For backward compatibility
fetch_latest_como_match = scrape_latest_como_match

if __name__ == "__main__":
    # Quick test when run directly
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1 and sys.argv[1] == "raw":
        print(fetch_match_30116_raw())
    elif len(sys.argv) > 1 and sys.argv[1] == "full":
        print(fetch_match_30116_full())
    else:
        success = asyncio.run(scrape_latest_como_match())
        sys.exit(0 if success else 1)