#!/usr/bin/env python3
import re
import json

with open('backend/team.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find all script tags
scripts = re.findall(r'<script[^>]*>([^<]+)</script>', html, re.DOTALL)
for idx, script in enumerate(scripts):
    # Look for JSON.parse patterns
    matches = re.findall(r'var\s+(\w+)\s*=\s*JSON\.parse\s*\(\s*\'(.*?)\'\s*\)\s*;', script, re.DOTALL)
    for var_name, json_str in matches:
        print(f'Variable: {var_name}')
        try:
            decoded = json_str.encode('utf-8').decode('unicode_escape')
            data = json.loads(decoded)
            print(f'  Type: {type(data)}')
            if isinstance(data, list):
                print(f'  Length: {len(data)}')
                if data and isinstance(data[0], dict):
                    print(f'  First keys: {list(data[0].keys())}')
            elif isinstance(data, dict):
                print(f'  Keys: {list(data.keys())}')
                # if matches data, print some
                if 'matches' in str(data).lower():
                    print('  Contains matches')
        except Exception as e:
            print(f'  Error: {e}')
        print()
# Also look for plain JSON objects
matches = re.findall(r'var\s+(\w+)\s*=\s*(\{.*?\})\s*;', html, re.DOTALL)
for var_name, json_str in matches:
    if len(json_str) > 100:
        print(f'Plain object: {var_name}')
        try:
            data = json.loads(json_str)
            print(f'  Keys: {list(data.keys())}')
        except:
            pass