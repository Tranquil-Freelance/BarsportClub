import requests
import re
import json

match_id = 27362
url = f"https://understat.com/match/{match_id}"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
resp = requests.get(url, headers=headers, timeout=10)
html = resp.text
print(f"HTML length: {len(html)}")
# find all script tags
import bs4
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')
scripts = soup.find_all('script')
for i, script in enumerate(scripts):
    if script.string:
        content = script.string.strip()
        if 'shotsData' in content:
            print(f"\n=== Script {i} contains shotsData ===")
            # print first 500 chars
            print(content[:500])
            # try to find var shotsData = JSON.parse(...)
            match = re.search(r'var\s+shotsData\s*=\s*JSON\.parse\s*\(\s*["\'](.*?)["\']\s*\)', content, re.DOTALL)
            if match:
                print("Found shotsData assignment!")
                raw = match.group(1)
                print(f"Raw length: {len(raw)}")
                # decode
                try:
                    decoded = raw.encode('utf-8').decode('unicode_escape')
                    data = json.loads(decoded)
                    print(f"Parsed JSON type: {type(data)}")
                    if isinstance(data, dict):
                        print(f"Keys: {data.keys()}")
                    elif isinstance(data, list):
                        print(f"List length: {len(data)}")
                except Exception as e:
                    print(f"Decode error: {e}")
        # also look for matchData
        if 'matchData' in content:
            print(f"\n=== Script {i} contains matchData ===")
            print(content[:500])
        # look for any JSON.parse
        matches = re.findall(r'var\s+(\w+)\s*=\s*JSON\.parse\s*\(\s*["\'](.*?)["\']\s*\)', content, re.DOTALL)
        for var_name, raw_json in matches:
            print(f"Found variable {var_name} with JSON length {len(raw_json)}")
            try:
                decoded = raw_json.encode('utf-8').decode('unicode_escape')
                data = json.loads(decoded)
                print(f"  Parsed type: {type(data)}")
            except:
                pass

# Also print a few lines of HTML around the script tags
print("\n=== All script tags ===")
for i, script in enumerate(scripts):
    if script.string:
        lines = script.string.split('\n')
        for line in lines:
            if 'var' in line and '=' in line:
                print(f"Script {i}: {line.strip()[:200]}")