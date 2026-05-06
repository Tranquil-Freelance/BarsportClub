import sys
sys.path.insert(0, '.')
from app.scraper.understat_engine import get_understat_match_shots

try:
    match_id = 21477  # random match ID
    shots_data = get_understat_match_shots(match_id)
    print(f"Type: {type(shots_data)}")
    if isinstance(shots_data, dict):
        print(f"Keys: {shots_data.keys()}")
        if 'h' in shots_data and 'a' in shots_data:
            print(f"Home shots: {len(shots_data['h'])}")
            print(f"Away shots: {len(shots_data['a'])}")
            if shots_data['h']:
                shot = shots_data['h'][0]
                print(f"Sample shot keys: {shot.keys()}")
                print(f"X: {shot.get('X')}, Y: {shot.get('Y')}")
                print(f"xG: {shot.get('xG')}, minute: {shot.get('minute')}, player: {shot.get('player')}")
    else:
        print(f"Raw data: {shots_data}")
except Exception as e:
    print(f"Error: {e}")