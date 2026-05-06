import sys
import re
import requests
from bs4 import BeautifulSoup

def fetch_league_matches(league='Serie_A', season=2024):
    url = f'https://understat.com/league/{league}/{season}'
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return []
    soup = BeautifulSoup(resp.text, 'html.parser')
    # Find all links that contain '/match/'
    match_ids = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        match = re.search(r'/match/(\d+)', href)
        if match:
            match_id = int(match.group(1))
            # Get team names from the link text maybe
            text = link.get_text(strip=True)
            if 'Como' in text:
                print(f"Found Como match: {match_id} - {text}")
                match_ids.append(match_id)
    return match_ids

if __name__ == '__main__':
    ids = fetch_league_matches('Serie_A', 2024)
    if ids:
        print(f"Match IDs: {ids}")
    else:
        print("No matches found for Serie A 2024, trying 2025...")
        ids = fetch_league_matches('Serie_A', 2025)
        if ids:
            print(f"Match IDs: {ids}")
        else:
            print("No matches found.")