#!/usr/bin/env python3
import re
import json
from pathlib import Path

html = Path('team.html').read_text(encoding='utf-8')
# find all script tags
scripts = re.findall(r'<script[^>]*>([^<]+)</script>', html, re.DOTALL)
print(f'Found {len(scripts)} script tags')
for i, script in enumerate(scripts):
    if 'matchesData' in script:
        print(f'Script {i} contains matchesData')
        # extract variable
        matches = re.findall(r'var matchesData\s*=\s*JSON\.parse\(\'([^\']+)\'\)', script)
        if matches:
            json_str = matches[0].encode().decode('unicode_escape')
            data = json.loads(json_str)
            print(f'Found matchesData with {len(data)} matches')
            for match in data[:5]:
                print(f"  ID: {match.get('id')}, {match.get('h')} vs {match.get('a')}")
        else:
            print('No matchesData variable found')
    if 'datesData' in script:
        print(f'Script {i} contains datesData')
        matches = re.findall(r'var datesData\s*=\s*JSON\.parse\(\'([^\']+)\'\)', script)
        if matches:
            json_str = matches[0].encode().decode('unicode_escape')
            data = json.loads(json_str)
            print(f'Found datesData with {len(data)} days')
            for day in data[:3]:
                for match in day.get('matches', []):
                    print(f"  ID: {match.get('id')}, {match.get('h')} vs {match.get('a')}")
        else:
            print('No datesData variable found')

# also search for any JSON.parse containing match IDs
pattern = r'var \w+Data\s*=\s*JSON\.parse\(\'([^\']+)\'\)'
all_vars = re.findall(pattern, html)
print(f'Found {len(all_vars)} data variables')
for var in all_vars[:5]:
    try:
        json_str = var.encode().decode('unicode_escape')
        data = json.loads(json_str)
        if isinstance(data, list):
            print(f'  Variable list length {len(data)}')
            if len(data) > 0 and isinstance(data[0], dict) and 'id' in data[0]:
                print(f'    First item ID: {data[0].get("id")}')
    except:
        pass