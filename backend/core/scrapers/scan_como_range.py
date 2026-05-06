#!/usr/bin/env python3
import requests
import time
import sys

def fetch_match_title(match_id):
    url = f'https://understat.com/match/{match_id}'
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if resp.status_code == 404:
            return None
        html = resp.text
        # extract title from <title> tag
        import re
        match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        if match:
            title = match.group(1)
            # remove extra parts
            title = title.replace(' | Understat', '').strip()
            return title
        else:
            return None
    except Exception as e:
        return None

def scan_range(start, end, step=1):
    found = []
    for match_id in range(start, end+1, step):
        title = fetch_match_title(match_id)
        if title is None:
            continue
        if 'Como' in title:
            found.append((match_id, title))
            print(f'FOUND: {match_id} -> {title}')
        else:
            if 'Serie A' in title:
                print(f'Serie A match: {match_id} -> {title}')
        time.sleep(0.1)  # be polite
    return found

if __name__ == '__main__':
    start = 22500
    end = 23500
    step = 5
    print(f'Scanning match IDs {start} to {end} step {step} for Como...')
    found = scan_range(start, end, step)
    print(f'Scan complete. Found {len(found)} matches with Como.')
    for match_id, title in found:
        print(f'{match_id}: {title}')