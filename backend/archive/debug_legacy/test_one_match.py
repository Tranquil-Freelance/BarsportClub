import sys
sys.path.insert(0, '.')
from app.scraper.understat_engine import get_understat_match_shots

match_id = 14878
try:
    shots = get_understat_match_shots(match_id)
    print(f"Success! Type: {type(shots)}")
    if isinstance(shots, dict) and 'h' in shots and 'a' in shots:
        home = shots['h']
        away = shots['a']
        print(f"Home shots: {len(home)}, Away shots: {len(away)}")
        if home:
            print(f"First home shot: {home[0]}")
            print(f"X={home[0].get('X')}, Y={home[0].get('Y')}")
        if away:
            print(f"First away shot: {away[0]}")
except Exception as e:
    print(f"Error: {e}")