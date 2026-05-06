#!/usr/bin/env python3
import requests
import re
import time

def fetch_match(match_id):
    url = f"https://understat.com/match/{match_id}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.RequestException:
        return None

def parse_title(html):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.string if soup.title else ''
    return title

def main():
    # Serie A 2024/25 likely match IDs? Let's guess based on known IDs: 20000 (2023), 14878 (2020)
    # Assume linear increase: 2000 per year? 2023->2024 +~2000 => 22000
    start = 22000
    end = 22500
    found = []
    for mid in range(start, end+1):
        print(f"Scanning {mid}...", end='')
        html = fetch_match(mid)
        if html is None:
            print(" 404")
            continue
        title = parse_title(html)
        print(f" {title[:50]}")
        if 'Serie A' in title and ('Como' in title or 'como' in title.lower()):
            print(f"  *** FOUND COMO MATCH ID: {mid} ***")
            found.append((mid, title))
        time.sleep(0.5)  # be polite
    print(f"\nFound {len(found)} matches:")
    for mid, title in found:
        print(f"  {mid}: {title}")

if __name__ == '__main__':
    main()