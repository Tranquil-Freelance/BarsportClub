import asyncio
import sys
sys.path.insert(0, '.')
from app.scraper.understat_parser import get_league_season_data

async def main():
    data = await get_league_season_data('Serie_A', 2025)
    print(f"Total entries: {len(data)}")
    if not data:
        return
    first = data[0]
    print("\nFirst entry keys:")
    for k, v in first.items():
        print(f"  {k}: {type(v).__name__} = {repr(v)[:80]}")
    # Check if 'round' or 'giornata' exists
    if 'round' in first:
        print("\nFound 'round' key!")
    if 'matchday' in first:
        print("\nFound 'matchday' key!")
    # Also check nested structures
    print("\nChecking nested dicts:")
    for k, v in first.items():
        if isinstance(v, dict):
            print(f"  {k}: keys {list(v.keys())}")
    # Print a few more entries to see variation
    print("\nFirst 5 entries:")
    for i, entry in enumerate(data[:5]):
        print(f"{i}: id={entry.get('id')}, datetime={entry.get('datetime')}, h={entry.get('h', {}).get('title')} vs a={entry.get('a', {}).get('title')}")

asyncio.run(main())