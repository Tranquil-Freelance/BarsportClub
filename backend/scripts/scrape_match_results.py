#!/usr/bin/env python3
"""
Scrape match results (goals, xG) from Understat and update the matches table.
"""

import asyncio
import sys
import logging
from typing import List, Optional

# Add backend to path
sys.path.append('.')

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.db.models import Match
from scrapers.understat import UnderstatScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


async def update_match_results_for_season(season_year: int = 2025, force: bool = False) -> None:
    """
    For each match in the database that has an understat_id, scrape the match page,
    extract goals and compute xG totals, then update the match record.
    
    Args:
        season_year: Season year (unused but kept for compatibility).
        force: If True, ignore missing shotsData/matchData and continue.
    """
    async with AsyncSessionLocal() as session:
        # Fetch matches with understat_id (only those not yet having scores?).
        stmt = select(Match).where(Match.understat_id.is_not(None))
        result = await session.execute(stmt)
        matches: List[Match] = result.scalars().all()

        logger.info(f"Found {len(matches)} matches with understat_id.")

        scraper = UnderstatScraper()
        updated = 0
        for match in matches:
            understat_id = match.understat_id
            logger.info(f"Processing match {match.id} (understat {understat_id})")
            try:
                # Scrape match data with optional force flag
                scraped = scraper.scrape_match(understat_id, force=force)
                shots_data = scraped['shots_data']
                match_data = scraped['match_data']
                
                # Extract goals
                home_goals = match_data.get('home_goals')
                away_goals = match_data.get('away_goals')
                # If goals are None, maybe they are not available; skip updating scores?
                if home_goals is not None:
                    match.home_score = int(home_goals)
                if away_goals is not None:
                    match.away_score = int(away_goals)
                
                # Compute xG totals from shots data
                home_shots = shots_data.get('h', [])
                away_shots = shots_data.get('a', [])
                home_xg = sum(shot.get('xG', 0.0) for shot in home_shots)
                away_xg = sum(shot.get('xG', 0.0) for shot in away_shots)
                match.home_xg = home_xg
                match.away_xg = away_xg
                
                # Update shot counts
                match.home_shots = len(home_shots)
                match.away_shots = len(away_shots)
                # Optionally compute shots on target (requires result field)
                home_sot = len([s for s in home_shots if s.get('result') in ['Goal', 'Saved', 'SavedToPost']])
                away_sot = len([s for s in away_shots if s.get('result') in ['Goal', 'Saved', 'SavedToPost']])
                match.home_shots_on_target = home_sot
                match.away_shots_on_target = away_sot
                
                # Mark as scraped
                match.scraping_status = 'COMPLETED'
                # Update last_scraped_at timestamp (if column exists)
                # match.last_scraped_at = datetime.utcnow()
                
                updated += 1
                if updated % 5 == 0:
                    await session.commit()  # Periodic commit
                    logger.info(f"Committed {updated} matches.")
            except Exception as e:
                logger.error(f"Failed to scrape match {match.id} (understat {understat_id}): {e}")
                match.scraping_status = 'ERROR'
                match.error_log = str(e)
                # Continue with next match
        
        # Final commit for remaining updates
        await session.commit()
        logger.info(f"Updated {updated} matches out of {len(matches)}.")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description='Scrape match results from Understat.')
    parser.add_argument('--season', type=int, default=2025,
                        help='Season year (default: 2025)')
    parser.add_argument('--force', action='store_true',
                        help='Force scraping even when shotsData/matchData missing')
    args = parser.parse_args()
    
    await update_match_results_for_season(args.season, force=args.force)


if __name__ == '__main__':
    asyncio.run(main())