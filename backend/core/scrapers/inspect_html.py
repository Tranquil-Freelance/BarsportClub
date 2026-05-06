import requests
import re
match_id = 27362
url = f"https://understat.com/match/{match_id}"
headers = {"User-Agent": "Mozilla/5.0"}
resp = requests.get(url, headers=headers)
print(f"Status: {resp.status_code}")
html = resp.text
# Look for script tags with src
script_srcs = re.findall(r'<script\s+[^>]*src="([^"]+)"', html)
print("Script srcs:")
for src in script_srcs[:20]:
    print(src)
# Look for API calls in inline scripts
pattern = r'["\'](/[^"\']*shots[^"\']*)["\']'
matches = re.findall(pattern, html, re.IGNORECASE)
print("\nPotential shot-related paths:")
for m in set(matches):
    print(m)
# Look for JSON.parse
pattern2 = r'JSON\.parse\(["\']([^"\']+)["\']'
matches2 = re.findall(pattern2, html, re.DOTALL)
print("\nJSON.parse occurrences (first 5):")
for m in matches2[:5]:
    print(m[:200])
# Look for fetch or axios calls
pattern3 = r'fetch\(["\']([^"\']+)["\']'
matches3 = re.findall(pattern3, html)
print("\nFetch calls:")
for m in matches3[:10]:
    print(m)