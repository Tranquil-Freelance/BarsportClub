#!/usr/bin/env python3
import requests
import re
import sys

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

start = 23500
end = 23520
found = []
for mid in range(start, end+1):
    title = fetch_title(mid)
    if title is None:
        continue
    if 'Serie A' in title and 'Como' in title:
        print(f"Found Como match: {mid} - {title}")
        found.append(mid)
    else:
        print(f"{mid}: {title}")
print(f"Found {len(found)} Como matches.")