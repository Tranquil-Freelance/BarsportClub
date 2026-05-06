import sys
sys.path.insert(0, '.')
import cloudscraper
import requests
import re
import json
import time

match_id = 27362
url = f"https://understat.com/match/{match_id}"

def try_scrape_with_user_agent(user_agent):
    headers = {"User-Agent": user_agent}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html = response.text
        print(f"UA {user_agent[:30]}... -> status {response.status_code}, length {len(html)}")
        # Try to extract shotsData
        match = re.search(r"var\s+shotsData\s*=\s*JSON\.parse\s*\(\s*'(.*?)'\s*\)\s*;", html, re.DOTALL)
        if match:
            raw_json = match.group(1)
            decoded = raw_json.encode('utf-8').decode('unicode_escape')
            data = json.loads(decoded)
            print(f"Success! Found shotsData with keys: {data.keys() if isinstance(data, dict) else len(data)}")
            return data
        else:
            print("shotsData not found in HTML")
            # print first 500 chars of HTML for debugging
            print("HTML snippet:", html[:500])
    except Exception as e:
        print(f"Error with UA {user_agent[:30]}: {e}")
    return None

def try_cloudscraper():
    scraper = cloudscraper.create_scraper()
    try:
        resp = scraper.get(url, timeout=10)
        html = resp.text
        print(f"Cloudscraper -> status {resp.status_code}, length {len(html)}")
        match = re.search(r"var\s+shotsData\s*=\s*JSON\.parse\s*\(\s*'(.*?)'\s*\)\s*;", html, re.DOTALL)
        if match:
            raw_json = match.group(1)
            decoded = raw_json.encode('utf-8').decode('unicode_escape')
            data = json.loads(decoded)
            print(f"Cloudscraper success! Found shotsData with keys: {data.keys() if isinstance(data, dict) else len(data)}")
            return data
        else:
            print("Cloudscraper: shotsData not found")
            print("HTML snippet:", html[:500])
    except Exception as e:
        print(f"Cloudscraper error: {e}")
    return None

# List of user agents
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
]

print(f"Testing match {match_id}...")
data = None
for i, ua in enumerate(user_agents):
    print(f"\nAttempt {i+1}/5 with UA")
    data = try_scrape_with_user_agent(ua)
    if data:
        break
    time.sleep(1)  # be polite

if not data:
    print("\nTrying cloudscraper...")
    data = try_cloudscraper()

if data:
    print("\nScraping succeeded!")
    # Save to static file as fallback
    import os
    static_file = "static_match_27362.json"
    with open(static_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved to {static_file}")
else:
    print("\nAll attempts failed. Need to manually fetch data.")