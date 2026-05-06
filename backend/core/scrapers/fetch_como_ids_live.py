#!/usr/bin/env python3
"""
Fetch Como match IDs from Understat Serie A 2024/25 season directly.
"""
import sys
sys.path.insert(0, '.')

from app.scraper.understat_parser import get_league_season_data

def main():
    try:
        data = get_league_season_data('Serie_A', 2025)
    except Exception as e:
        print(f"Error fetching league data: {e}")
        sys.exit(1)
    
    matches = []
    for match in data:
        if not isinstance(match, dict):
            continue
        home = match.get('h', {}).get('title')
        away = match.get('a', {}).get('title')
        if home == 'Como' or away == 'Como':
            match_id = match.get('id')
            home_team = match.get('h', {}).get('title')
            away_team = match.get('a', {}).get('title')
            matches.append((match_id, home_team, away_team, match.get('datetime')))
    
    print(f"Found {len(matches)} Como matches:")
    for match_id, home, away, dt in matches:
        print(f"  {match_id}: {home} vs {away} ({dt})")
    
    # Output first 3 match IDs
    if matches:
        match_ids = [m[0] for m in matches]
        print("\nMatch IDs:", match_ids)
        # Ensure we have at least 3
        if len(match_ids) >= 3:
            print("First 3 IDs:", match_ids[:3])
        else:
            print("Not enough matches, using all")
    else:
        print("No Como matches found.")

if __name__ == '__main__':
    main()