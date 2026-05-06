import sys
import time
sys.path.insert(0, '.')
from app.scraper.understat_engine import get_understat_match_shots

def test_match_id(match_id):
    try:
        shots = get_understat_match_shots(match_id)
        if isinstance(shots, dict) and 'h' in shots and 'a' in shots:
            home_shots = len(shots['h'])
            away_shots = len(shots['a'])
            print(f"Match {match_id}: found {home_shots}+{away_shots} shots")
            return True
        else:
            print(f"Match {match_id}: unexpected structure")
            return False
    except Exception as e:
        if '404' in str(e) or 'not found' in str(e).lower():
            pass  # silent
        else:
            print(f"Match {match_id}: error {e}")
        return False

if __name__ == '__main__':
    # Try a range of likely match IDs (based on known Understat IDs)
    start = 27362
    end = 27400
    found = False
    for mid in range(start, end + 1):
        if test_match_id(mid):
            found = True
            print(f"Valid match ID: {mid}")
            break
        time.sleep(0.5)  # be polite
    if not found:
        print(f"No valid match found in range {start}-{end}")