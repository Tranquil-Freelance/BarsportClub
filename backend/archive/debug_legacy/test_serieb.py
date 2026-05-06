#!/usr/bin/env python3
import sys
sys.path.append('.')
from app.scraper.understat_parser import get_league_season_data
import traceback

try:
    print("Fetching Serie B 2025...")
    data = get_league_season_data('Serie_B', 2025)
    print(f'Success: {len(data)} matches')
    for match in data[:10]:
        print(match)
except Exception as e:
    print(f'Error: {e}')
    traceback.print_exc()