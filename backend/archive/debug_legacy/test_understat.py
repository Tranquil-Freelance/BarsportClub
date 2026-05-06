#!/usr/bin/env python3
"""Quick test to see what variables are present in Understat league page."""
import re
import requests

url = "https://understat.com/league/Serie_A/2025"
resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
html = resp.text

# Find all var assignments with JSON.parse
pattern = re.compile(r'var\s+(\w+)\s*=\s*JSON\.parse\s*\(\s*\'(.*?)\'\s*\)', re.DOTALL)
matches = pattern.findall(html)
print(f"Found {len(matches)} variables")
for var_name, encoded in matches[:10]:
    print(f"{var_name}: length {len(encoded)}")
    # Decode and maybe show a snippet
    try:
        decoded = encoded.encode('utf-8').decode('unicode_escape')
        data = eval(decoded) if decoded else None
        print(f"  type: {type(data)}")
        if isinstance(data, list):
            print(f"  list length: {len(data)}")
        elif isinstance(data, dict):
            print(f"  dict keys: {list(data.keys())[:5]}")
    except:
        print("  decode error")
        pass

# Also look for teamsData specifically
if 'teamsData' in html:
    print("\nteamsData found in html")
    # extract using regex
    teams_match = re.search(r'var teamsData\s*=\s*JSON\.parse\s*\(\s*\'(.*?)\'\s*\)', html, re.DOTALL)
    if teams_match:
        print("Extracted teamsData")
        encoded = teams_match.group(1)
        decoded = encoded.encode('utf-8').decode('unicode_escape')
        import json
        data = json.loads(decoded)
        print(f"Teams data keys: {list(data.keys())}")
        for team_id, team_data in list(data.items())[:2]:
            print(f"Team {team_id}: {team_data.get('title')}")
else:
    print("\nteamsData not found in html")