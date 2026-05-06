import sys
sys.path.insert(0, '.')
from app.scraper.understat_engine import get_understat_match_shots
import traceback

try:
    data = get_understat_match_shots(30116)
    print("Success!")
    print(data)
except Exception as e:
    print("Error:", e)
    traceback.print_exc()