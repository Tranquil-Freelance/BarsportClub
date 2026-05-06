#!/usr/bin/env python3
import re
import json
import os

# team.html is in same directory as this script (backend)
html_path = 'team.html'
if not os.path.exists(html_path):
    print(f"File {html_path} not found. Current dir: {os.getcwd()}")
    sys.exit(1)

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Pattern to find var assignments with JSON.parse
pattern = r'var\s+(\w+)\s*=\s*JSON\.parse\s*\(\s*\'(.*?)\'\s*\)\s*;'
matches = re.findall(pattern, html, re.DOTALL)
print(f"Found {len(matches)} JSON.parse variables:")
for var_name, encoded in matches:
    print(f"Variable: {var_name}")
    # decode
    try:
        decoded = encoded.encode('utf-8').decode('unicode_escape')
        data = json.loads(decoded)
        print(f"  Type: {type(data)}")
        if isinstance(data, list):
            print(f"  Length: {len(data)}")
            if len(data) > 0 and isinstance(data[0], dict):
                # print first keys
                print(f"  First keys: {list(data[0].keys())}")
        elif isinstance(data, dict):
            print(f"  Keys: {list(data.keys())}")
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"  Failed to decode: {e}")
    print()

# Also search for any match IDs in the HTML using regex /match/\d+
match_ids = re.findall(r'/match/(\d+)', html)
if match_ids:
    unique = set(match_ids)
    print(f"Found {len(unique)} unique match IDs: {sorted(unique, key=int)}")
else:
    print("No match IDs found in HTML.")