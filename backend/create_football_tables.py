#!/usr/bin/env python3
"""
Create or update database tables for the football analytics schema (SQLAlchemy 2.0).
This script ensures that the newly added advanced columns and the TeamSeasonStat table
are present in the database.
"""

import asyncio
import sys
sys.path.insert(0, '.')

from app.db.database import engine
from app.db.base_class import Base
from app.models.football import League, Team, Player, MatchCalendar, PlayerMatchStat, TeamSeasonStat

async def create_football_tables():
    """
    Create all tables defined in the football models (if they do not already exist).
    This operation is idempotent – existing tables are left unchanged.
    """
    async with engine.begin() as conn:
        # Bind the football Base metadata to the engine and create tables
        await conn.run_sync(Base.metadata.create_all)
    print("Football tables created/verified successfully.")

if __name__ == "__main__":
    asyncio.run(create_football_tables())