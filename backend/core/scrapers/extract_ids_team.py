#!/usr/bin/env python3
import re
import json
from pathlib import Path

html = Path('team.html').read_text(encoding='utf-8')
# find all JSON.parse patterns
pattern = r'JSON\.parse\(\'([^\']+)\'\)'
matches = re.findall(pattern, html)
for i, m in enumerate(matches):
    try:
        json_str = m.encode().decode('unicode_escape')
        data = json.loads(json_str)
        if isinstance(data, dict) and 'id' in data:
            print(f'Dict with id: {data.get("id")}')
        if isinstance(data, list):
            for item in data[:5]:
                if isinstance(item, dict) and 'id' in item:
                    print(f'List item id: {item.get("id")}')
    except:
        pass

# find all numbers that could be match IDs (6 digits?)
ids = re.findall(r'"id"\s*:\s*(\d+)', html)
print(f'Found {len(ids)} id fields')
for id in ids[:20]:
    print(id)

# find "matches" pattern
if 'matchesData' in html:
    print('matchesData present')
if 'datesData' in html:
    print('datesData present')