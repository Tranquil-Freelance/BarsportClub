#!/usr/bin/env python3
"""Quick test to see if Como match IDs can be fetched."""
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.understat_service import UnderstatService

async def main():
    try:
        ids = await UnderstatService.get_como_match_ids(season_year=2025)
        print(f"Found {len(ids)} match IDs: {ids}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())