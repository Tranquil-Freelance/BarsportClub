import requests
import re
import json

match_id = 27362
url = f"https://understat.com/match/{match_id}"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
resp = requests.get(url, headers=headers, timeout=10)
html = resp.text

# Extract match_info
pattern = r'var\s+match_info\s*=\s*JSON\.parse\s*\(\s*["\'](.*?)["\']\s*\)'
match = re.search(pattern, html, re.DOTALL)
if match:
    raw = match.group(1)
    decoded = raw.encode('utf-8').decode('unicode_escape')
    data = json.loads(decoded)
    print("match_info keys:", data.keys())
    print(json.dumps(data, indent=2, ensure_ascii=False))
else:
    print("match_info not found")

# Look for any other JSON.parse variables
all_vars = re.findall(r'var\s+(\w+)\s*=\s*JSON\.parse\s*\(\s*["\'](.*?)["\']\s*\)', html, re.DOTALL)
for var_name, raw_json in all_vars:
    print(f"\nVariable: {var_name}, length {len(raw_json)}")
    try:
        decoded = raw_json.encode('utf-8').decode('unicode_escape')
        data = json.loads(decoded)
        print(f"  Type: {type(data)}")
        if isinstance(data, dict):
            print(f"  Keys: {list(data.keys())}")
        elif isinstance(data, list):
            print(f"  List length: {len(data)}")
            if len(data) > 0 and isinstance(data[0], dict):
                print(f"  First item keys: {data[0].keys()}")
    except Exception as e:
        print(f"  Error: {e}")

# Also search for shotsData in other forms (maybe as a global object)
shots_pattern = r'shotsData\s*=\s*({.*?})\s*;'
match2 = re.search(shots_pattern, html, re.DOTALL)
if match2:
    print("\nFound shotsData direct assignment")
    print(match2.group(1)[:500])

# Search for any script tag with src containing shots
script_src_pattern = r'<script[^>]*src=["\'][^"\']*shots[^"\']*["\'][^>]*>'
src_matches = re.findall(script_src_pattern, html, re.IGNORECASE)
for src in src_matches:
    print("Script src with shots:", src[:200])