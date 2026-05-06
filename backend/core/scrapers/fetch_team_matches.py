#!/usr/bin/env python3
import requests
import json
import re

url = 'https://understat.com/team/Como/2024/matches'
print(f'Fetching {url}')
resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
print(f'Status: {resp.status_code}')
if resp.status_code == 200:
    html = resp.text
    # look for JSON data
    pattern = r'var matchesData\s*=\s*JSON\.parse\(\'([^\']+)\'\)'
    match = re.search(pattern, html)
    if match:
        json_str = match.group(1).encode().decode('unicode_escape')
        data = json.loads(json_str)
        print(f'Found {len(data)} matches')
        for m in data:
            print(f"ID: {m.get('id')}, {m.get('h')} vs {m.get('a')}, date: {m.get('date')}")
    else:
        print('matchesData not found')
        # try to find any script with data
        scripts = re.findall(r'<script[^>]*>([^<]+)</script>', html, re.DOTALL)
        for i, script in enumerate(scripts):
            if 'id' in script and 'home_team' in script:
                print(f'Script {i} contains potential data')
                # extract JSON-like structures
                import json
                try:
                    # naive extraction
                    data = json.loads(script.strip())
                    print(data)
                except:
                    pass
else:
    print('Page not found')
    # maybe the URL is different