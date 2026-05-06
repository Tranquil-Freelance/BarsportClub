#!/usr/bin/env python3
"""Test the existing understat_parser to see what data it returns."""
import sys
sys.path.insert(0, '.')
from app.scraper.understat_parser import get_league_season_data

try:
    data = get_league_season_data('Serie_A', 2025)
    print(f"Successfully fetched data, type: {type(data)}")
    if isinstance(data, list):
        print(f"Length: {len(data)}")
        if data:
            print(f"First element keys: {data[0].keys() if isinstance(data[0], dict) else 'not dict'}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()