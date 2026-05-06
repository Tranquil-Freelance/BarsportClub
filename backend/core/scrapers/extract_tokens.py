import requests
import re

match_id = 27362
url = f"https://understat.com/match/{match_id}"
resp = requests.get(url)
html = resp.text
# find all var assignments
pattern = r'var\s+(\w+)\s*=\s*([^;]+);'
matches = re.findall(pattern, html, re.DOTALL)
for var, val in matches:
    if 'token' in var.lower():
        print(f"{var} = {val[:200]}")
    if 'key' in var.lower():
        print(f"{var} = {val[:200]}")
    if 'api' in var.lower():
        print(f"{var} = {val[:200]}")
# find all script src
scripts = re.findall(r'<script\s+[^>]*src="([^"]+)"', html)
for src in scripts:
    if 'api' in src or 'shots' in src:
        print(f"Script src: {src}")
# find all fetch/ajax calls
fetch_calls = re.findall(r'fetch\([^)]+\)', html)
for call in fetch_calls[:5]:
    print(f"Fetch: {call}")
ajax_calls = re.findall(r'\$.ajax\([^)]+\)', html)
for call in ajax_calls[:5]:
    print(f"Ajax: {call}")