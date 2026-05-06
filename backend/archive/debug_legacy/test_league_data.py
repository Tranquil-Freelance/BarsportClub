#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from app.scraper.understat_parser import get_league_season_data

try:
    data = get_league_season_data('Serie_A', 2024)
    print(f"Retrieved {len(data)} entries")
    if data:
        print("First entry keys:", data[0].keys() if isinstance(data[0], dict) else 'not dict')
        # look for match IDs
        for entry in data[:5]:
            print(entry)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()