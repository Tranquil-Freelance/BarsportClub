#!/usr/bin/env python3
"""
Purge mock data from xpalermostat_db.

Deletes:
- All shots where match_id = 99999 or match title (home_team/away_team) contains 'Palermo'
- All matches where id = 99999 or home_team/away_team contains 'Palermo'
- Optionally deletes articles with title containing 'Palermo' (if needed)
"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import or_
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.db.models import Match, Shot, Article


async def purge_mock_data():
    """Delete mock data from database."""
    async with AsyncSessionLocal() as db:
        # Find match IDs to delete
        stmt = select(Match.id).where(
            or_(
                Match.id == 99999,
                Match.home_team.ilike('%Palermo%'),
                Match.away_team.ilike('%Palermo%'),
            )
        )
        result = await db.execute(stmt)
        match_ids_to_delete = [row[0] for row in result.fetchall()]
        
        if not match_ids_to_delete:
            print("No mock matches found to delete.")
        else:
            # Delete shots for those matches
            delete_shots_stmt = Shot.__table__.delete().where(
                Shot.match_id.in_(match_ids_to_delete)
            )
            await db.execute(delete_shots_stmt)
            print(f"Deleted shots for matches: {match_ids_to_delete}")
            
            # Delete matches
            delete_matches_stmt = Match.__table__.delete().where(
                Match.id.in_(match_ids_to_delete)
            )
            await db.execute(delete_matches_stmt)
            print(f"Deleted matches: {match_ids_to_delete}")
        
        # Optionally delete articles with title containing 'Palermo'
        delete_articles_stmt = Article.__table__.delete().where(
            Article.title.ilike('%Palermo%')
        )
        result = await db.execute(delete_articles_stmt)
        deleted_articles = result.rowcount
        if deleted_articles:
            print(f"Deleted {deleted_articles} articles with title containing 'Palermo'.")
        
        await db.commit()
        print("Purge completed successfully.")


if __name__ == "__main__":
    asyncio.run(purge_mock_data())