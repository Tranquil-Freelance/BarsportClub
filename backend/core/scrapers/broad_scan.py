#!/usr/bin/env python3
import requests
import re
import time

def fetch_title(mid):
    url = f'https://understat.com/match/{mid}'
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code != 200:
            return None
        html = resp.text
        match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        if match:
            title = match.group(1)
            if title.startswith('Understat - '):
                title = title[len('Understat - '):]
            return title
    except:
        pass
    return None

start = 23600
end = 24000
step = 10
found = []
for mid in range(start, end+1, step):
    title = fetch_title(mid)
    if title is None:
        continue
    if 'Serie A' in title and 'Como' in title:
        print(f"Found Como match: {mid} - {title}")
        found.append(mid)
        if len(found) >= 3:
            break
    else:
        # print(f"{mid}: {title[:50]}...")
        pass
    time.sleep(0.1)

print(f"\nFound {len(found)} Como matches: {found}")
if found:
    # also check neighboring IDs +/-1 to ensure we have exact match IDs
    exact = []
    for mid in found:
        for delta in (-1,0,1):
            check = mid + delta
            title = fetch_title(check)
            if title and 'Serie A' in title and 'Como' in title:
                exact.append(check)
                break
    print(f"Exact match IDs: {exact}")
else:
    print("No Como matches found.")