#!/usr/bin/env python3
import requests
import re
import json

url = 'https://understat.com/team/Como/2024'
print(f'Fetching {url}')
resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
html = resp.text
# look for matchesData variable
pattern = r'var matchesData\s*=\s*JSON\.parse\(\'([^\']+)\'\)'
match = re.search(pattern, html)
if match:
    json_str = match.group(1).encode().decode('unicode_escape')
    data = json.loads(json_str)
    print(f'Found {len(data)} matches')
    for m in data[:10]:
        print(f"ID: {m.get('id')}, {m.get('h')} vs {m.get('a')}, date: {m.get('date')}")
else:
    print('matchesData not found')
    # try datesData
    pattern = r'var datesData\s*=\s*JSON\.parse\(\'([^\']+)\'\)'
    match = re.search(pattern, html)
    if match:
        json_str = match.group(1).encode().decode('unicode_escape')
        data = json.loads(json_str)
        print(f'Found {len(data)} days')
        for day in data[:3]:
            for m in day.get('matches', []):
                print(f"ID: {m.get('id')}, {m.get('h')} vs {m.get('a')}")
    else:
        print('datesData not found')
        # search for any JSON.parse containing match IDs
        pattern = r'var \w+Data\s*=\s*JSON\.parse\(\'([^\']+)\'\)'
        all_vars = re.findall(pattern, html)
        print(f'Found {len(all_vars)} data variables')
        for var in all_vars[:3]:
            try:
                json_str = var.encode().decode('unicode_escape')
                data = json.loads(json_str)
                if isinstance(data, list) and len(data) > 0 and 'id' in data[0]:
                    print(f'List length {len(data)}')
                    for m in data[:5]:
                        if 'Como' in str(m.get('h')) or 'Como' in str(m.get('a')):
                            print(f"  Found Como match ID: {m.get('id')}")
            except:
                pass