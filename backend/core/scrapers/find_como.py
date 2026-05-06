#!/usr/bin/env python3
"""
Find Como match IDs by scanning Understat match IDs.
"""
import requests
import re
import time
import sys

def fetch_match_title(match_id):
    url = f'https://understat.com/match/{match_id}'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None
        html = resp.text
        title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        if title_match:
            title = title_match.group(1)
            if title.startswith('Understat - '):
                title = title[len('Understat - '):]
            return title
        else:
            return None
    except Exception as e:
        # print(f"  Error fetching {match_id}: {e}")
        return None

def scan_range(start, end):
    found = []
    for mid in range(start, end+1):
        if mid % 100 == 0:
            print(f"Progress: {mid}/{end}")
        title = fetch_match_title(mid)
        if title is None:
            continue
        if 'Serie A' in title and 'Como' in title:
            print(f"FOUND: {mid} - {title}")
            found.append((mid, title))
        # optional: also print Serie A matches for debugging
        # elif 'Serie A' in title:
        #     print(f"Serie A: {mid} - {title}")
        time.sleep(0.3)  # be polite
    return found

if __name__ == '__main__':
    # scan 22500-23500 (likely 2024/25 season)
    start = 22500
    end = 23500
    print(f"Scanning {start} to {end} for Como matches...")
    results = scan_range(start, end)
    print(f"\nScan completed. Found {len(results)} Como matches:")
    for mid, title in results:
        print(f"  {mid}: {title}")
    # write to file
    with open('como_matches.txt', 'w') as f:
        for mid, title in results:
            f.write(f"{mid}\t{title}\n")
    print("Results written to como_matches.txt")