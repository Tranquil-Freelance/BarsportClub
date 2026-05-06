import asyncio
import logging
import sys
sys.path.insert(0, '.')
from scrapers.understat_lib import scrape_latest_como_match

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def main():
    success = await scrape_latest_como_match()
    print(f"Result: {success}")
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())