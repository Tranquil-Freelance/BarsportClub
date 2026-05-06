#!/usr/bin/env python3
"""
Test script to simulate soccerdata output using existing understat engine.
This is a temporary demonstration until soccerdata installation is resolved.
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
from app.scraper.understat_engine import get_understat_match_shots

def scale_coordinate(val):
    """Scale X/Y from 0-1 to 0-100."""
    return round(float(val) * 100, 2)

def main(match_id=30116):
    print(f"Fetching match {match_id} via understat engine...")
    try:
        raw_shots = get_understat_match_shots(match_id)
    except Exception as e:
        print(f"Error fetching data: {e}")
        sys.exit(1)

    if not isinstance(raw_shots, dict) or 'h' not in raw_shots or 'a' not in raw_shots:
        print(f"Unexpected data format: {type(raw_shots)}")
        sys.exit(1)

    # Build DataFrame similar to soccerdata's output
    rows = []
    for team_key, shot_list in raw_shots.items():
        for shot in shot_list:
            rows.append({
                'X': shot['X'],
                'Y': shot['Y'],
                'xG': shot['xG'],
                'player': shot['player'],
                'result': shot['result'],
                'minute': shot['minute'],
                'team': team_key,  # 'h' or 'a'
                'home_team': 'Home',  # placeholder
                'away_team': 'Away',
            })

    df = pd.DataFrame(rows)
    print(f"DataFrame shape: {df.shape}")
    print("\nFirst 5 rows:")
    print(df.head().to_string())
    print("\nColumns:", list(df.columns))

    # Scale coordinates (as would be done by soccerdata_engine)
    df['X_scaled'] = df['X'].apply(scale_coordinate)
    df['Y_scaled'] = df['Y'].apply(scale_coordinate)

    # Count shots per team
    home_shots = len(raw_shots['h'])
    away_shots = len(raw_shots['a'])
    total_shots = home_shots + away_shots
    print(f"\nShot counts: home={home_shots}, away={away_shots}, total={total_shots}")

    # Simulate DB insertion (just count)
    print(f"\nSimulated SQL shot count after insertion: {total_shots} shots would be saved.")

if __name__ == '__main__':
    match_id = 30116 if len(sys.argv) < 2 else int(sys.argv[1])
    main(match_id)