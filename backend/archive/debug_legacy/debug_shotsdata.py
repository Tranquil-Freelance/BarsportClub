import requests
from bs4 import BeautifulSoup
import re

url = "https://understat.com/match/30116"
headers = {"User-Agent": "Mozilla/5.0"}
resp = requests.get(url, headers=headers)
print(f"Status: {resp.status_code}")
soup = BeautifulSoup(resp.text, "html.parser")
scripts = soup.find_all("script")
print(f"Number of script tags: {len(scripts)}")
for i, script in enumerate(scripts):
    if script.string:
        if 'shotsData' in script.string:
            print(f"Script {i} contains shotsData")
            # find the variable assignment
            pattern = r"var\s+shotsData\s*=\s*JSON\.parse\s*\(\s*'(.*?)'\s*\)\s*;"
            match = re.search(pattern, script.string, re.DOTALL)
            if match:
                print("Found shotsData assignment")
                # print first 200 chars of encoded string
                encoded = match.group(1)
                print(f"Encoded length: {len(encoded)}")
                print(f"First 200 chars: {encoded[:200]}")
            else:
                print("No shotsData variable found in script")
                # maybe it's a different pattern
                # search for 'shotsData' line
                lines = script.string.split('\n')
                for idx, line in enumerate(lines):
                    if 'shotsData' in line:
                        print(f"Line {idx}: {line[:200]}")
        else:
            # maybe shotsData is in a different script with no string? 
            pass
    else:
        print(f"Script {i} has no string (maybe src)")