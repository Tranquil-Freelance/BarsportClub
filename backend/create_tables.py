"""
Script to create database tables for xPalermoStat.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.db.database import engine, Base
from app.db.models import Article, Match, Shot

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully.")

if __name__ == "__main__":
    asyncio.run(create_tables())