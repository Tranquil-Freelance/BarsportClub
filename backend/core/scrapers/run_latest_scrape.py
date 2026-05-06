#!/usr/bin/env python3
"""
Run the scraper for the latest Palermo match only.
"""
import asyncio
import logging
import sys
sys.path.insert(0, '.')

from scrapers.palermo_full_season import (
    get_latest_palermo_match,
    scrape_match,
    ensure_league_exists,
)
from app.db.session import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)

async def main():
    async with AsyncSessionLocal() as session:
        # Ensure league exists (should already)
        league_id = await ensure_league_exists(session)
        logging.info(f"League ID: {league_id}")
        
        # Get latest Palermo match
        match = await get_latest_palermo_match(session)
        if not match:
            logging.error("No latest Palermo match found.")
            return
        
        logging.info(f"Found latest match ID {match.id} ({match.home_team_id} vs {match.away_team_id})")
        
        # Scrape the match (this will call FBref and upsert player stats)
        await scrape_match(session, match)
        
        logging.info("Scraping completed.")

if __name__ == "__main__":
    asyncio.run(main())