import requests
import re

match_id = 27362
url = f"https://understat.com/match/{match_id}"
headers = {"User-Agent": "Mozilla/5.0"}
resp = requests.get(url, headers=headers, timeout=10)
resp.raise_for_status()
html = resp.text

# Find all var assignments with JSON.parse
pattern = re.compile(r'var\s+(\w+)\s*=\s*JSON\.parse\s*\(\s*\'(.*?)\'\s*\)\s*;', re.DOTALL)
matches = pattern.findall(html)
print(f"Found {len(matches)} variables:")
for var_name, encoded in matches:
    print(f"  {var_name}")
    # decode and inspect
    try:
        decoded = encoded.encode('utf-8').decode('unicode_escape')
        data = eval(decoded)  # safe? but we can use json.loads if valid JSON
        if isinstance(data, dict):
            print(f"    dict with keys: {list(data.keys())}")
        elif isinstance(data, list):
            print(f"    list length {len(data)}")
    except:
        pass

# Also look for any JavaScript object assignments like shotsData: {...}
pattern2 = re.compile(r'(\w+)\s*:\s*\{', re.DOTALL)
matches2 = pattern2.findall(html)
shot_vars = [m for m in matches2 if 'shot' in m.lower()]
if shot_vars:
    print(f"\nPotential shot-related keys: {shot_vars}")

# Look for URLs in script
pattern3 = re.compile(r'["\'](https?://understat\.com/[^"\']+)["\']', re.DOTALL)
matches3 = pattern3.findall(html)
if matches3:
    print("\nURLs found:")
    for u in matches3[:10]:
        print(f"  {u}")