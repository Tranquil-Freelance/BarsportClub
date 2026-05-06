"""
Understat scraping service for xPalermoStat.

This module provides a service layer that integrates the Understat scraper
with the database CRUD operations, implementing the required upsert logic.
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from scrapers.understat import UnderstatScraper
except ImportError:
    # Fallback for when running as part of the app package
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from scrapers.understat import UnderstatScraper

from app.api.crud import save_match_shots
from app.scraper.understat_parser import get_league_season_data

logger = logging.getLogger(__name__)


class UnderstatService:
    """
    Service for scraping Understat match data and saving it to the database.
    """
    
    def __init__(self, scraper: Optional[UnderstatScraper] = None):
        self.scraper = scraper or UnderstatScraper()
    
    async def scrape_and_save_match(
        self,
        db: AsyncSession,
        match_id: int,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Scrape a match from Understat, scale coordinates, and upsert into PostgreSQL.
        
        This method performs the following steps:
            1. Fetch HTML and extract shotsData and matchData using the scraper.
            2. Scale X/Y coordinates from 0.0‑1.0 to 0‑100.
            3. Extract home/away team names (and other metadata) from matchData.
            4. Call the database layer to upsert the match record and shots.
            5. Return a summary dictionary with counts and metadata.
        
        Args:
            db: SQLAlchemy async session.
            match_id: Understat's internal match identifier.
            force: If True, continue even when shotsData/matchData missing.
            
        Returns:
            Dictionary with keys:
                - match_id (int)
                - home_team (str)
                - away_team (str)
                - home_shots (int)
                - away_shots (int)
                - total_shots (int)
                - message (str)
                
        Raises:
            requests.exceptions.RequestException: If network request fails.
            ValueError: If required data cannot be extracted.
            sqlalchemy.exc.SQLAlchemyError: If database operations fail.
        """
        logger.info(f"Starting scrape for match {match_id} (force={force})")
        
        # 1. Scrape match page
        scraped_data = self.scraper.scrape_match(match_id, force=force)
        shots_data = scraped_data["shots_data"]
        match_data = scraped_data["match_data"]
        
        home_team = match_data.get("home_team", "Home")
        away_team = match_data.get("away_team", "Away")
        
        logger.info(
            f"Scraped match {match_id}: {home_team} vs {away_team}, "
            f"{len(shots_data['h'])} home shots, {len(shots_data['a'])} away shots"
        )
        
        # 2. Save to database (upsert logic is inside save_match_shots)
        await save_match_shots(
            db=db,
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            shots_data=shots_data,
        )
        
        home_shots = len(shots_data["h"])
        away_shots = len(shots_data["a"])
        total_shots = home_shots + away_shots
        
        logger.info(f"Successfully saved {total_shots} shots for match {match_id}")
        
        return {
            "match_id": match_id,
            "home_team": home_team,
            "away_team": away_team,
            "home_shots": home_shots,
            "away_shots": away_shots,
            "total_shots": total_shots,
            "message": f"Match {match_id} scraped and saved successfully.",
        }

    @staticmethod
    async def get_como_match_ids(season_year: int = 2025) -> list[int]:
        """
        Scrape the Serie A calendar for the given season and extract match IDs where
        Como is either the home or away team.

        Args:
            season_year: Understat season end year (e.g., 2025 for 2024/25 season).

        Returns:
            List of Understat match IDs (integers) for Como matches.
        """
        try:
            raw_data = get_league_season_data("Serie_A", season_year)
        except Exception as e:
            logger.error(f"Failed to fetch league calendar: {e}")
            raise

        match_ids = []
        for match in raw_data:
            if not isinstance(match, dict):
                continue
            home = match.get("h", {}).get("title")
            away = match.get("a", {}).get("title")
            if home == "Como" or away == "Como":
                match_id = match.get("id")
                if match_id:
                    match_ids.append(int(match_id))

        logger.info(f"Found {len(match_ids)} Como matches for season {season_year}")
        return match_ids


async def scrape_and_save_match(
    db: AsyncSession,
    match_id: int,
    force: bool = False,
    scraper: Optional[UnderstatScraper] = None,
) -> Dict[str, Any]:
    """
    Convenience async function that creates a service instance and calls scrape_and_save_match.
    
    This is the primary entry point for external callers (e.g., API endpoints).
    """
    service = UnderstatService(scraper=scraper)
    return await service.scrape_and_save_match(db, match_id, force=force)