import sys
sys.path.append('backend')
from scrapers.understat import UnderstatScraper
import requests.exceptions
import traceback

scraper = UnderstatScraper()
print("Testing match 29 without force...")
try:
    result = scraper.scrape_match(29, force=False)
    print('Scraping succeeded (force=False)')
    print(f"Shots data keys: {list(result['shots_data'].keys())}")
    print(f"Home shots: {len(result['shots_data'].get('h', []))}")
    print(f"Away shots: {len(result['shots_data'].get('a', []))}")
    print(f"Match data: {result['match_data']}")
except Exception as e:
    print(f'Error: {e}')
    traceback.print_exc()

print("\nTesting with force=True...")
try:
    result = scraper.scrape_match(29, force=True)
    print('Scraping succeeded (force=True)')
    print(f"Shots data keys: {list(result['shots_data'].keys())}")
    print(f"Home shots: {len(result['shots_data'].get('h', []))}")
    print(f"Away shots: {len(result['shots_data'].get('a', []))}")
    print(f"Match data: {result['match_data']}")
except Exception as e:
    print(f'Error: {e}')
    traceback.print_exc()