#!/usr/bin/env python3
import requests
import re
from bs4 import BeautifulSoup
import sys

def get_match_title(match_id):
    url = f"https://understat.com/match/{match_id}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"Match {match_id}: HTTP error {e}")
        return None
    html = resp.text
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.string if soup.title else ''
    print(f"Match {match_id}: {title}")
    # Look for team names in title pattern "Team1 vs Team2 | Understat"
    pattern = r'(.+?)\s+vs\s+(.+?)\s+\|'
    match = re.search(pattern, title)
    if match:
        home, away = match.group(1), match.group(2)
        print(f"  Home: {home}, Away: {away}")
        if 'Como' in home or 'Como' in away:
            print("  *** Includes Como ***")
            return True
    # Also check for "Como" in page content
    if 'Como' in html:
        print("  Found 'Como' in HTML")
    return False

if __name__ == '__main__':
    ids = [14878, 21474, 21477, 20000, 20001, 20002]  # add a few more guesses
    for mid in ids:
        get_match_title(mid)