import asyncio
import sys
sys.path.insert(0, '.')
from app.scraper.sync_calendar import run_daily_sync

if __name__ == "__main__":
    asyncio.run(run_daily_sync(2025))