import sys
sys.path.insert(0, '.')
from app.scraper.understat_engine import get_understat_match_shots

match_id = 29845
try:
    shots = get_understat_match_shots(match_id)
    print(f'Success: {len(shots.get("h", []))} home shots, {len(shots.get("a", []))} away shots')
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)