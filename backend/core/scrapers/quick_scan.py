#!/usr/bin/env python3
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
        print(f"  Error fetching {match_id}: {e}")
        return None

def main(start=22500, end=22530):
    print(f"Scanning match IDs {start} to {end} for Como matches...")
    found = []
    for mid in range(start, end+1):
        sys.stdout.write(f"\rScanning {mid}...")
        sys.stdout.flush()
        title = fetch_match_title(mid)
        if title is None:
            continue
        if 'Serie A' in title:
            print(f"\n{mid}: {title}")
            if 'Como' in title:
                print(f"  *** FOUND COMO MATCH ID: {mid} ***")
                found.append((mid, title))
        time.sleep(0.1)
    print(f"\nScan completed. Found {len(found)} Como matches:")
    for mid, title in found:
        print(f"  {mid}: {title}")
    return found

if __name__ == '__main__':
    found = main()
    if found:
        print("\nMatch IDs:", [mid for mid,_ in found])
    else:
        print("No Como matches found in range.")