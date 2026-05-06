import requests
import re
import json

match_id = 27362
url = f"https://understat.com/match/{match_id}"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
resp = requests.get(url, headers=headers, timeout=10)
html = resp.text
print(f"HTML length: {len(html)}")

# Look for any JSON.parse assignments
pattern = r'var\s+(\w+)\s*=\s*JSON\.parse\s*\(\s*["\'](.*?)["\']\s*\)'
matches = re.findall(pattern, html, re.DOTALL)
print(f"Found {len(matches)} JSON.parse assignments")
for var_name, raw_json in matches:
    print(f"\nVariable: {var_name}, raw length: {len(raw_json)}")
    if var_name == 'shotsData':
        print("*** Found shotsData ***")
        try:
            decoded = raw_json.encode('utf-8').decode('unicode_escape')
            data = json.loads(decoded)
            print(f"Parsed successfully. Type: {type(data)}")
            if isinstance(data, dict):
                print(f"Keys: {data.keys()}")
                if 'h' in data and 'a' in data:
                    print(f"Home shots: {len(data['h'])}, Away shots: {len(data['a'])}")
                    # Save to static file
                    with open('static_match_27362.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print("Saved to static_match_27362.json")
            elif isinstance(data, list):
                print(f"List length: {len(data)}")
        except Exception as e:
            print(f"Failed to decode: {e}")
    else:
        # maybe also interesting
        pass

# Also search for shotsData in other forms like shotsData = {...}
pattern2 = r'var\s+shotsData\s*=\s*({.*?})\s*;'
match2 = re.search(pattern2, html, re.DOTALL)
if match2:
    print("\nFound shotsData direct object")
    print(match2.group(1)[:200])

# If no shotsData found, maybe the data is embedded in a script tag with type="application/json"
script_pattern = r'<script[^>]*type="application/json"[^>]*>(.*?)</script>'
script_matches = re.findall(script_pattern, html, re.DOTALL)
for i, script_content in enumerate(script_matches):
    print(f"\nScript application/json {i}: length {len(script_content)}")
    try:
        data = json.loads(script_content)
        print(f"Parsed JSON keys: {data.keys() if isinstance(data, dict) else 'list'}")
    except:
        pass

# If still nothing, we need to manually download data from another source.
# For now, we can try to use an alternative API: maybe understat provides an API for match shots.
# Let's search for known endpoint patterns in the HTML
endpoint_pattern = r'["\'](/match/\d+/[^"\']+)["\']'
endpoints = re.findall(endpoint_pattern, html)
print("\nPotential endpoints found:")
for ep in set(endpoints)[:10]:
    print(ep)