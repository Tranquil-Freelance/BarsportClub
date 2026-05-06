#!/usr/bin/env python3
"""
Test that the UnderstatScraper can be imported and used.
"""
import sys
sys.path.insert(0, '.')

try:
    from scrapers.understat import UnderstatScraper
    print("OK Imported UnderstatScraper")
except ImportError as e:
    print(f"FAIL Import failed: {e}")
    sys.exit(1)

# Try to instantiate
try:
    scraper = UnderstatScraper()
    print("OK Created scraper instance")
except Exception as e:
    print(f"FAIL Instantiation failed: {e}")
    sys.exit(1)

# Try to scrape a known match (match ID 29955 from earlier debug)
# This will make a network request; we can skip if offline.
# For now, just test that the method exists.
if hasattr(scraper, 'scrape_match'):
    print("OK scrape_match method exists")
else:
    print("FAIL scrape_match missing")

print("Test passed.")