#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
import logging
logging.basicConfig(level=logging.DEBUG)
from app.scraper.understat_parser import get_league_season_data

def main():
    try:
        print("Fetching Serie_A 2024...")
        data = get_league_season_data('Serie_A', 2024)
        print(f"Success! Number of days: {len(data)}")
        if data:
            day = data[0]
            print(f"Day keys: {list(day.keys())}")
            # print matches length
            matches = day.get('matches', [])
            print(f"Matches in first day: {len(matches)}")
            if matches:
                match = matches[0]
                print(f"Match keys: {list(match.keys())}")
                print(f"Match sample: {match}")
                # Check for round key in match or day
                if 'round' in match:
                    print("Found 'round' in match")
                if 'matchday' in match:
                    print("Found 'matchday' in match")
                if 'giornata' in match:
                    print("Found 'giornata' in match")
            # Also inspect day for round number
            print(f"Day fields: {day}")
        else:
            print("No data returned")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()