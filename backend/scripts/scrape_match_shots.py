#!/usr/bin/env python3
"""
Scrape shot data for a given Understat match ID and store it in the database.
"""
import asyncio
import sys
import argparse
from pathlib import Path
import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

# Add the parent directory to sys.path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.understat import UnderstatScraper
from app.api.crud import save_match_shots
from app.db.session import AsyncSessionLocal

async def scrape_and_save(match_id: int, force: bool = False) -> None:
    """Scrape shot data for a given Understat match ID and persist it."""
    scraper = UnderstatScraper()
    try:
        result = scraper.scrape_match(match_id, force=force)
    except Exception as e:
        print(f"Failed to scrape match {match_id}: {e}")
        raise

    shots_data = result["shots_data"]
    match_data = result["match_data"]
    home_team = match_data.get("home_team") or "Home"
    away_team = match_data.get("away_team") or "Away"
    
    print(f"Scraped match {match_id}: {len(shots_data.get('h', []))} home shots, {len(shots_data.get('a', []))} away shots")
    print(f"Teams: {home_team} vs {away_team}")
    
    # Save to database
    async with AsyncSessionLocal() as db:
        await save_match_shots(db, match_id, home_team, away_team, shots_data)
        await db.commit()
        print(f"Match {match_id} saved to database.")

def main():
    parser = argparse.ArgumentParser(description="Scrape shot data for an Understat match.")
    parser.add_argument("--match_id", type=int, required=True, help="Understat match identifier")
    parser.add_argument("--force", action="store_true", default=False, help="Force scraping even if match page missing or data incomplete")
    args = parser.parse_args()
    
    try:
        asyncio.run(scrape_and_save(args.match_id, force=args.force))
        print("Success.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()