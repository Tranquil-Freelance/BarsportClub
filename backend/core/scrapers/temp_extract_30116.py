#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from app.scraper.understat_engine import get_understat_match_shots
import json

match_id = 30116
try:
    raw = get_understat_match_shots(match_id)
    print(json.dumps(raw, indent=2))
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)