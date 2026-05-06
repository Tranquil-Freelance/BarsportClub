#!/usr/bin/env python3
import requests
import re
import sys

def get_title(mid):
    url = f'https://understat.com/match/{mid}'
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code != 200:
            return None
        html = resp.text
        m = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        if m:
            title = m.group(1)
            if title.startswith('Understat - '):
                title = title[len('Understat - '):]
            return title
    except:
        pass
    return None

for mid in range(22500, 23501, 100):
    title = get_title(mid)
    if title and 'Serie A' in title:
        print(f'{mid}: {title}')
        if 'Como' in title:
            print('   *** COMO ***')
    elif title:
        print(f'{mid}: {title[:50]}')
    else:
        print(f'{mid}: no title or error')
    sys.stdout.flush()