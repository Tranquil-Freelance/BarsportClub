import requests
import re

match_id = 27362
url = f"https://understat.com/match/{match_id}"
headers = {"User-Agent": "Mozilla/5.0"}
resp = requests.get(url, headers=headers, timeout=10)
html = resp.text

# Find all var assignments
pattern = re.compile(r'var\s+(\w+)\s*=')
vars = set(pattern.findall(html))
print(f"Found {len(vars)} variable assignments:")
for v in sorted(vars):
    print(f"  {v}")

# Look for JSON.parse assignments
pattern2 = re.compile(r'var\s+(\w+)\s*=\s*JSON\.parse')
vars2 = pattern2.findall(html)
print(f"\nJSON.parse variables: {vars2}")

# Look for any data structures that might contain shots
for v in vars2:
    # extract the encoded JSON
    pattern3 = re.compile(r'var\s+' + re.escape(v) + r'\s*=\s*JSON\.parse\s*\(\s*\'(.*?)\'\s*\)\s*;', re.DOTALL)
    match = pattern3.search(html)
    if match:
        encoded = match.group(1)
        try:
            decoded = encoded.encode('utf-8').decode('unicode_escape')
            data = eval(decoded)  # might be unsafe but okay for debugging
            print(f"\nVariable {v}:")
            if isinstance(data, dict):
                print(f"  dict keys: {list(data.keys())}")
                # if any key contains 'shot'
                for key in data.keys():
                    if 'shot' in str(key).lower():
                        print(f"    contains shot key: {key}")
            elif isinstance(data, list):
                print(f"  list length {len(data)}")
                if len(data) > 0 and isinstance(data[0], dict):
                    sample_keys = data[0].keys()
                    print(f"    sample keys: {sample_keys}")
        except Exception as e:
            print(f"  error parsing: {e}")

# Also look for window.__INITIAL_STATE__ or similar
if 'window.__' in html:
    print("\nFound window.__ pattern")