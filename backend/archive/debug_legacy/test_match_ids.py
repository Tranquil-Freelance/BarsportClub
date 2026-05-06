#!/usr/bin/env python3
import requests
import re
import sys

def fetch_match_title(match_id):
    url = f'https://understat.com/match/{match_id}'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        html = resp.text
        # extract title
        title_match = re.search(r'<title>(.*?)</title>', html)
        if title_match:
            return title_match.group(1)
        else:
            return ''
    except Exception as e:
        print(f"Error fetching {match_id}: {e}")
        return None

def main():
    candidate_ids = [21477, 21474, 14878, 99999]
    for mid in candidate_ids:
        title = fetch_match_title(mid)
        if title is None:
            print(f"Match {mid}: Not found (404)")
            continue
        print(f"Match {mid}: {title}")
        # Check if Como in title
        if 'Como' in title:
            print(f"  -> Como match!")
        # Check if Serie A 2024/25
        if 'Serie A' in title and '2024' in title:
            print(f"  -> Serie A 2024/25 season")
        print()

if __name__ == '__main__':
    main()