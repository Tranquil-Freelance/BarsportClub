import requests
import re
from bs4 import BeautifulSoup

match_id = 27362
url = f"https://understat.com/match/{match_id}"
headers = {"User-Agent": "Mozilla/5.0"}
resp = requests.get(url, headers=headers, timeout=10)
resp.raise_for_status()
html = resp.text

soup = BeautifulSoup(html, "html.parser")
scripts = soup.find_all("script")
for i, script in enumerate(scripts):
    if script.string:
        content = script.string
        if 'shots' in content.lower() or 'player' in content.lower():
            print(f"=== Script {i} ===")
            # print first 2000 chars
            lines = content.split('\n')
            for line in lines:
                if 'shots' in line.lower() or 'player' in line.lower():
                    print(line[:200])
            print()

# Also look for any API endpoints in the HTML
api_patterns = [
    r'https?://understat\.com/main/[a-zA-Z]+',
    r'/main/[a-zA-Z]+',
    r'fetch\(["\']([^"\']+)["\']\)',
    r'axios\.get\(["\']([^"\']+)["\']\)',
]
for pattern in api_patterns:
    matches = re.findall(pattern, html)
    if matches:
        print(f"Pattern {pattern}:")
        for m in matches[:5]:
            print(f"  {m}")