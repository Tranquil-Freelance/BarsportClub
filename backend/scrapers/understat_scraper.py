"""
Understat.com shot scraper for xPalermoStat.

This module provides a function to scrape shot data from a given Understat match,
scale coordinates, and store the results in the PostgreSQL database.
"""

import asyncio
import sys
from typing import Dict, List, Any

# Add the parent directory to the path to allow imports from app
sys.path.insert(0, '..')

from app.db.database import AsyncSessionLocal
from app.scraper.understat_engine import get_understat_match_shots
from app.api.crud import save_match_shots


def scale_coordinates(shots_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Scale X and Y coordinates from Understat's 0.0‑1.0 range to 0‑100.

    Understat stores shot locations as proportions of the pitch length/width.
    The database expects integer percentages (0‑100). This function multiplies
    each X and Y value by 100 and rounds to two decimal places.

    The input dictionary must have the structure {'h': [...], 'a': [...]}.
    Returns a new dictionary with scaled coordinates (original dict is not mutated).
    """
    scaled = {}
    for team_key, shot_list in shots_data.items():
        scaled_list = []
        for shot in shot_list:
            # Create a copy to avoid mutating the original
            scaled_shot = shot.copy()
            # Scale X and Y
            scaled_shot['X'] = round(float(shot['X']) * 100, 2)
            scaled_shot['Y'] = round(float(shot['Y']) * 100, 2)
            scaled_list.append(scaled_shot)
        scaled[team_key] = scaled_list
    return scaled


async def scrape_and_store_shots(match_id: int) -> int:
    """
    Fetch shot data for a given Understat match, scale coordinates, and store in PostgreSQL.

    Steps:
        1. Fetch raw shots data via get_understat_match_shots.
        2. Scale X and Y coordinates from 0.0‑1.0 to 0‑100.
        3. Use a database session to upsert the match record and insert shots.
        4. Return the total number of shots saved.

    Args:
        match_id: Understat's internal match identifier.

    Returns:
        Total number of shots stored (home + away).

    Raises:
        ValueError: If the match ID is invalid or the fetched data lacks 'h'/'a' keys.
        Exception: For any network, parsing, or database errors.
    """
    # 1. Fetch raw JSON from Understat
    raw_shots = get_understat_match_shots(match_id)
    if not isinstance(raw_shots, dict) or 'h' not in raw_shots or 'a' not in raw_shots:
        raise ValueError(
            f"Fetched data for match {match_id} is not a dict with 'h' and 'a' keys. "
            f"Got: {type(raw_shots)}"
        )

    # 2. Scale coordinates
    scaled_shots = scale_coordinates(raw_shots)

    # 3. Save to database (placeholder team names – can be improved by parsing the match page)
    home_team = "Home"
    away_team = "Away"

    async with AsyncSessionLocal() as session:
        await save_match_shots(
            db=session,
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            shots_data=scaled_shots,
        )

    # 4. Count shots
    total_shots = len(scaled_shots['h']) + len(scaled_shots['a'])
    return total_shots


async def main() -> None:
    """Command‑line entry point."""
    if len(sys.argv) != 2:
        print("Usage: python understat_scraper.py <match_id>")
        sys.exit(1)

    try:
        match_id = int(sys.argv[1])
    except ValueError:
        print("Error: match_id must be an integer.")
        sys.exit(1)

    try:
        total = await scrape_and_store_shots(match_id)
        print(f"Successfully stored {total} shots for match {match_id}.")
    except Exception as e:
        print(f"Failed to scrape/store match {match_id}: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())