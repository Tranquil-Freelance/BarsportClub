#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.services.understat_service import UnderstatService

async def main():
    # Create a temporary async session (not needed for scraping but for service)
    DATABASE_URL = 'postgresql+asyncpg://postgres:postgres@localhost:5432/xpalermostat_db'
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        service = UnderstatService()
        try:
            result = await service.scrape_and_save_match(session, 29, force=True)
            print(f"Scraping succeeded: {result}")
        except Exception as e:
            print(f"Scraping failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())