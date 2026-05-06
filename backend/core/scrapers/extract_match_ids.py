#!/usr/bin/env python3
"""
Extract match IDs from Understat team page.
"""
import sys
import os
sys.path.insert(0, '.')

import json
import re
from bs4 import BeautifulSoup

def extract_match_ids_from_html(html):
    """Find match IDs in the HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script')
    matches = []
    for script in scripts:
        if script.string is None:
            continue
        # Look for variable names that might contain match data
        # Pattern for match IDs in URLs
        url_pattern = r'/match/(\d+)'
        found = re.findall(url_pattern, script.string)
        if found:
            matches.extend(found)
        # Look for JSON data containing match IDs
        # Understat stores match data in variables like matchesData, datesData, etc.
        # We'll try to find any JSON.parse('...') and parse it
        pattern = r'var\s+(\w+)\s*=\s*JSON\.parse\s*\(\s*\'(.*?)\'\s*\)\s*;'
        for var_name, encoded in re.findall(pattern, script.string, re.DOTALL):
            try:
                decoded = encoded.encode('utf-8').decode('unicode_escape')
                data = json.loads(decoded)
                # Recursively search for match IDs in the data
                def find_ids(obj):
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            if k == 'id' and isinstance(v, (int, str)):
                                matches.append(str(v))
                            elif k == 'match_id':
                                matches.append(str(v))
                            else:
                                find_ids(v)
                    elif isinstance(obj, list):
                        for item in obj:
                            find_ids(item)
                find_ids(data)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
    return list(set(matches))

def main():
    # Read the team HTML file
    with open('team.html', 'r', encoding='utf-8') as f:
        html = f.read()
    match_ids = extract_match_ids_from_html(html)
    print(f"Found {len(match_ids)} unique match IDs:")
    for mid in sorted(match_ids, key=int):
        print(f"  {mid}")
    # Also try league page
    with open('league.html', 'r', encoding='utf-8') as f:
        html = f.read()
    league_ids = extract_match_ids_from_html(html)
    print(f"Found {len(league_ids)} unique match IDs from league page:")
    for mid in sorted(league_ids, key=int):
        print(f"  {mid}")
    # Combine and output first 10
    all_ids = list(set(match_ids + league_ids))
    print(f"Total unique IDs: {len(all_ids)}")
    if all_ids:
        print("First 10:", all_ids[:10])
    else:
        print("No match IDs found. Need to inspect manually.")

if __name__ == '__main__':
    main()