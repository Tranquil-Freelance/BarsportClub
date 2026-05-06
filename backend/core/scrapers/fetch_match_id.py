import sys
sys.path.insert(0, '.')
from app.scraper.understat_parser import get_league_season_data

try:
    data = get_league_season_data('Serie_A', 2025)
    print(f"Total matches: {len(data)}")
    for i, match in enumerate(data[:10]):
        print(f"Match {i}: id={match.get('id')}, home={match.get('h', {}).get('title')}, away={match.get('a', {}).get('title')}")
        if 'Como' in match.get('h', {}).get('title', '') or 'Como' in match.get('a', {}).get('title', ''):
            print(f"Found Como match: {match['id']}")
except Exception as e:
    print(f"Error: {e}")