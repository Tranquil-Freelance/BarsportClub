import requests
import re

match_id = 27362
url = f"https://understat.com/match/{match_id}"
headers = {"User-Agent": "Mozilla/5.0"}
resp = requests.get(url, headers=headers, timeout=10)
html = resp.text

# Look for any API endpoints (patterns)
patterns = [
    r'https?://api\.understat\.com/[^"\']+',
    r'https?://understat\.com/api/[^"\']+',
    r'https?://understat\.com/main/[^"\']+',
    r'"/main/[^"\']+"',
    r'"/api/[^"\']+"',
    r'fetch\(["\'][^"\']+["\']\)',
    r'axios\.get\(["\'][^"\']+["\']\)',
    r'\.get\(["\'][^"\']+["\']\)',
]
for p in patterns:
    matches = re.findall(p, html, re.IGNORECASE)
    if matches:
        print(f"\nPattern: {p}")
        for m in matches[:5]:
            print(f"  {m}")

# Also look for any JSONP callbacks
if 'callback' in html:
    print("\nFound callback")

# Look for any script src that might be loading data
script_srcs = re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', html, re.IGNORECASE)
for src in script_srcs:
    if 'main' in src or 'api' in src:
        print(f"Script src: {src}")