import sys
sys.path.insert(0, '.')
from app.scraper.understat_engine import get_understat_match_shots

try:
    data = get_understat_match_shots(30116)
    print("Success!")
    print("Keys:", data.keys())
    print("Home shots:", len(data['h']))
    print("Away shots:", len(data['a']))
    if data['h']:
        print("Sample home shot:", data['h'][0])
except Exception as e:
    print("Error:", e)