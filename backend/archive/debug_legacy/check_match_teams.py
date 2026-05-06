#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from app.scraper.understat_parser import get_match_roster, get_match_shots

def inspect_match(match_id):
    print(f"\n=== Match {match_id} ===")
    try:
        roster = get_match_roster(match_id)
        # roster is dict with 'h' and 'a' keys each dict of players
        # we can infer team names from player data? Not directly.
        # Let's fetch shots data which may contain team names
        shots = get_match_shots(match_id)
        # shots is list of dicts each with 'h_a' field? Actually shotsData structure.
        # Let's just print first shot
        if shots and len(shots) > 0:
            first = shots[0]
            print(f"First shot keys: {first.keys()}")
            if 'h_a' in first:
                print(f"Home/Away: {first['h_a']}")
            if 'player' in first:
                print(f"Player: {first['player']}")
        # Also try to get match title from HTML
        import requests
        from bs4 import BeautifulSoup
        url = f"https://understat.com/match/{match_id}"
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string if soup.title else ''
        print(f"Page title: {title}")
        # Extract team names from title (e.g., "Juventus vs Como")
        import re
        match = re.search(r'(.+?)\s+vs\s+(.+?)\s+\|', title)
        if match:
            home, away = match.group(1), match.group(2)
            print(f"Home: {home}, Away: {away}")
        else:
            print("Could not parse team names")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    for mid in [21474, 21477, 14878]:
        inspect_match(mid)