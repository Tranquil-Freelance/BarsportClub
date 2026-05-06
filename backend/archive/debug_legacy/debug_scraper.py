import sys
sys.path.insert(0, '.')
from scrapers.understat import UnderstatScraper

scraper = UnderstatScraper()
try:
    result = scraper.scrape_match(27362)
    print("Scraping succeeded!")
    print(f"Home team: {result['match_data']['home_team']}")
    print(f"Away team: {result['match_data']['away_team']}")
    print(f"Home shots: {len(result['shots_data']['h'])}")
    print(f"Away shots: {len(result['shots_data']['a'])}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()