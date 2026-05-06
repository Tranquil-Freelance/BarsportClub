import sys
sys.path.insert(0, '.')
from app.scraper.understat_engine import get_understat_match_shots

try:
    data = get_understat_match_shots(27362)
    print(f"Success! Type: {type(data)}")
    if isinstance(data, dict):
        print(f"Keys: {list(data.keys())}")
        if 'h' in data and 'a' in data:
            print(f"Home shots: {len(data['h'])}")
            print(f"Away shots: {len(data['a'])}")
            # Print first shot sample
            if data['h']:
                print(f"Sample home shot: {data['h'][0]}")
            if data['a']:
                print(f"Sample away shot: {data['a'][0]}")
    else:
        print(f"Data: {data}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()