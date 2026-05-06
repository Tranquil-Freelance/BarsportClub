#!/usr/bin/env python3
import json
import re
from pathlib import Path

def extract_js_var(html, var_name):
    pattern = rf'var {var_name}\s*=\s*JSON\.parse\(\'([^\']+)\'\)'
    match = re.search(pattern, html)
    if match:
        json_str = match.group(1).encode().decode('unicode_escape')
        return json.loads(json_str)
    return None

html = Path('league.html').read_text(encoding='utf-8')
dates_data = extract_js_var(html, 'datesData')
if dates_data:
    print(f'Found {len(dates_data)} match days')
    for day in dates_data:
        for match in day.get('matches', []):
            if 'Como' in match.get('h', '') or 'Como' in match.get('a', ''):
                print(f"Match ID: {match.get('id')}, {match.get('h')} vs {match.get('a')}")
else:
    print('datesData not found')
    # try matchesData
    matches_data = extract_js_var(html, 'matchesData')
    if matches_data:
        print(f'Found {len(matches_data)} matches')
        for match in matches_data:
            if 'Como' in match.get('h', '') or 'Como' in match.get('a', ''):
                print(f"Match ID: {match.get('id')}, {match.get('h')} vs {match.get('a')}")
    else:
        print('matchesData not found')
        # try teamData
        team_data = extract_js_var(html, 'teamData')
        if team_data:
            print('teamData found')
        else:
            print('No variables found')