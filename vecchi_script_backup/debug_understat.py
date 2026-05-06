import requests
from bs4 import BeautifulSoup
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
url = 'https://understat.com/league/Serie_A/2025'
print(f'Fetching {url}')
r = requests.get(url, headers=headers, timeout=10)
html = r.text
print(f'Status: {r.status_code}, length: {len(html)}')

soup = BeautifulSoup(html, 'html.parser')
scripts = soup.find_all('script')
print(f'Found {len(scripts)} script tags')

for i, script in enumerate(scripts):
    if script.string:
        content = script.string
        # Look for var variableName = JSON.parse(...)
        matches = re.findall(r'var\s+(\w+)\s*=\s*JSON\.parse\s*\(', content)
        if matches:
            print(f'Script {i}: found variables {matches}')
            # print first 200 chars of content
            print(content[:200])
        # Look for var variableName = {...} (direct object)
        matches2 = re.findall(r'var\s+(\w+)\s*=\s*\{', content)
        if matches2:
            print(f'Script {i}: direct object variables {matches2}')
            # print snippet
            lines = content.split('\n')
            for line in lines:
                if 'var ' + matches2[0] + ' = {' in line:
                    print(line[:200])
                    break
        # Look for datesData specifically
        if 'datesData' in content:
            print(f'Script {i} contains datesData')
            # extract the line
            for line in content.split('\n'):
                if 'datesData' in line:
                    print(line[:200])
                    break

# Also search for any JSON-like structures
print('\n--- Searching for JSON-like data ---')
# Use regex to find JSON.parse('...')
pattern = re.compile(r"JSON\.parse\s*\(\s*'([^']+)'")
for script in scripts:
    if script.string:
        matches = pattern.findall(script.string)
        if matches:
            print(f'Found JSON.parse with {len(matches)} matches')
            for idx, encoded in enumerate(matches[:2]):
                try:
                    decoded = encoded.encode('utf-8').decode('unicode_escape')
                    data = json.loads(decoded)
                    print(f'Match {idx}: type {type(data)}, sample keys: {list(data.keys()) if isinstance(data, dict) else "list len " + str(len(data))}')
                except:
                    pass