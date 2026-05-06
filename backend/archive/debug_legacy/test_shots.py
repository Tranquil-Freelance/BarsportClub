import sys
sys.path.insert(0, '.')
from app.scraper.understat_engine import get_understat_match_shots

try:
    data = get_understat_match_shots(12345)
    print(f"Success! Type: {type(data)}")
    if isinstance(data, dict):
        print(f"Keys: {data.keys()}")
        if 'h' in data and 'a' in data:
            print(f"Home shots: {len(data['h'])}")
            print(f"Away shots: {len(data['a'])}")
    else:
        print(f"Data: {data}")
except Exception as e:
    print(f"Error: {e}")