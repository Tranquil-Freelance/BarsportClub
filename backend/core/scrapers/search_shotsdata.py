import requests
import re

url = "https://understat.com/match/30116"
resp = requests.get(url)
text = resp.text
# find all lines containing shotsData
lines = text.split('\n')
for i, line in enumerate(lines):
    if 'shotsData' in line:
        print(f"Line {i}: {line.strip()[:200]}")
        # look for JSON.parse
        if 'JSON.parse' in line:
            print("  Contains JSON.parse")
# also search for getMatchShots
if 'getMatchShots' in text:
    print("getMatchShots found in HTML")
else:
    print("getMatchShots NOT found")