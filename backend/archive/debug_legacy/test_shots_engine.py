#!/usr/bin/env python3
"""
Test the low-level shot extraction engine.
"""
import sys
sys.path.insert(0, '.')

from app.scraper.understat_engine import get_understat_match_shots

match_id = 27362  # from existing JSON file
try:
    data = get_understat_match_shots(match_id)
    print(f"Successfully retrieved shots data for match {match_id}")
    print(f"Type: {type(data)}")
    if isinstance(data, dict):
        print(f"Keys: {data.keys()}")
        if 'h' in data and 'a' in data:
            print(f"Home shots: {len(data['h'])}")
            print(f"Away shots: {len(data['a'])}")
    elif isinstance(data, list):
        print(f"List length: {len(data)}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()