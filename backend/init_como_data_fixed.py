#!/usr/bin/env python3
"""
Automation script to populate the database with the last three Como matches.
"""
import asyncio
import logging
import sys
import os
from typing import List, Dict, Any

# Ensure we can import app modules
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.services.understat_service import UnderstatService, scrape_and_save_match

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def populate_como_data() -> None:
    """
    Main orchestration function.
    """
    async with AsyncSessionLocal() as session:
        # 1. Get Como match IDs for Serie A 2024/25 season
        logger.info("Fetching Como match IDs for Serie A 2024/25 season...")
        try:
            all_match_ids = await UnderstatService.get_como_match_ids(season_year=2025)
        except Exception as e:
            logger.error(f"Failed to fetch Como match IDs: {e}")
            return

        if not all_match_ids:
            logger.warning("No Como matches found.")
            return

        logger.info(f"Found {len(all_match_ids)} Como matches.")

        # For simplicity, we'll just take the first three match IDs.
        # In a production scenario you would sort by date and pick the most recent completed matches.
        selected_ids = all_match_ids[:3]
        logger.info(f"Selected match IDs: {selected_ids}")

        # 2. Scrape and save each match
        shot_counts: Dict[int, int] = {}
        for match_id in selected_ids:
            try:
                result = await scrape_and_save_match(session, match_id)
                shot_counts[match_id] = result["total_shots"]
                logger.info(
                    f"Match {match_id}: {result['home_team']} vs {result['away_team']} - "
                    f"{result['total_shots']} shots saved."
                )
            except Exception as e:
                logger.error(f"Failed to scrape match {match_id}: {e}")
                shot_counts[match_id] = 0

        # 3. Log summary
        logger.info("=== Population Summary ===")
        for match_id, shots in shot_counts.items():
            logger.info(f"Match {match_id}: {shots} shots")
        total_shots = sum(shot_counts.values())
        logger.info(f"Total shots saved across {len(shot_counts)} matches: {total_shots}")


if __name__ == "__main__":
    asyncio.run(populate_como_data())