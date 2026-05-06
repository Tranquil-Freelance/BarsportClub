#!/usr/bin/env python3
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

html_path = Path(__file__).parent.parent / "imports" / "Cagliari 1 - 2 Como.html"
html = html_path.read_text(encoding="utf-8", errors="ignore")
soup = BeautifulSoup(html, "html.parser")
scripts = soup.find_all("script")

for idx, script in enumerate(scripts):
    if not script.string:
        continue
    content = script.string
    # Look for pattern like var something = { ... };
    # We'll search for 'h':[...] or 'a':[...]
    if ('"h":' in content or "'h':" in content) and ('"a":' in content or "'a':" in content):
        print(f"Script {idx} contains h and a keys")
        # print first 500 chars
        print(content[:500])
        print("---")
        # Try to extract JSON-like object
        # Use regex to find something like {\s*'h'\s*:\s*\[.*?\]\s*,\s*'a'\s*:\s*\[.*?\]}
        # but we can just look for var shotsData = ...;
        pass

# Also search for shotsData assignment
for idx, script in enumerate(scripts):
    if not script.string:
        continue
    if 'shotsData' in script.string:
        print(f"Script {idx} mentions shotsData")
        # print context
        lines = script.string.split('\n')
        for i, line in enumerate(lines):
            if 'shotsData' in line:
                print(f"  Line {i}: {line.strip()}")
                # print next few lines
                for j in range(i+1, min(i+3, len(lines))):
                    print(f"    {lines[j].strip()}")
        break

# If still not found, maybe it's in a JSON.parse variable with a different name
# Let's find all JSON.parse assignments
pattern = r'var\s+(\w+)\s*=\s*JSON\.parse\s*\([\'"](.*?)[\'"]\)'
for idx, script in enumerate(scripts):
    if not script.string:
        continue
    matches = re.findall(pattern, script.string, re.DOTALL)
    for var, json_str in matches:
        print(f"Found JSON.parse variable: {var}")
        if var == 'match_info':
            continue
        # decode
        decoded = json_str.encode('utf-8').decode('unicode_escape')
        try:
            data = json.loads(decoded)
            print(f"  Type: {type(data)}")
            if isinstance(data, dict):
                print(f"  Keys: {list(data.keys())}")
                if 'h' in data and 'a' in data:
                    print("  Found h and a keys!")
                    print(f"  h length: {len(data['h']) if isinstance(data['h'], list) else 'not list'}")
                    print(f"  a length: {len(data['a']) if isinstance(data['a'], list) else 'not list'}")
        except json.JSONDecodeError:
            pass