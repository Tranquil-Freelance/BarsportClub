import requests
import json
import re

match_id = 27362
base = "https://understat.com"
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
})

# First get the match page to capture cookies
print("Fetching match page...")
match_page = session.get(f"{base}/match/{match_id}")
print(f"Status: {match_page.status_code}")
cookies = session.cookies.get_dict()
print(f"Cookies: {cookies}")

# Extract possible tokens
html = match_page.text
tokens = re.findall(r'name="csrf-token" content="([^"]+)"', html)
if tokens:
    csrf_token = tokens[0]
    print(f"CSRF token: {csrf_token}")
else:
    csrf_token = None

# Headers for API requests
headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": f"{base}/match/{match_id}",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": base,
}

# Candidate endpoints and payloads
candidates = []

# POST JSON with id
candidates.append(("POST", f"{base}/main/getMatchShots", {"id": match_id}, {"Content-Type": "application/json"}))
# POST JSON with match_id
candidates.append(("POST", f"{base}/main/getMatchShots", {"match_id": match_id}, {"Content-Type": "application/json"}))
# POST form data with match_id
candidates.append(("POST", f"{base}/main/getMatchShots", {"match_id": match_id}, {"Content-Type": "application/x-www-form-urlencoded"}))
# GET with query param
candidates.append(("GET", f"{base}/main/getMatchShots/{match_id}", None, {}))
candidates.append(("GET", f"{base}/main/getMatchShots?id={match_id}", None, {}))
candidates.append(("GET", f"{base}/main/getMatchShots?match_id={match_id}", None, {}))
# maybe with league_id and season
league_id = 2
season = 2024
candidates.append(("POST", f"{base}/main/getMatchShots", {"id": match_id, "league_id": league_id, "season": season}, {"Content-Type": "application/json"}))

# If CSRF token found, add it as header
if csrf_token:
    headers['X-CSRF-TOKEN'] = csrf_token

for method, url, payload, content_type in candidates:
    print(f"\n--- Trying {method} {url} ---")
    req_headers = headers.copy()
    if content_type:
        req_headers.update(content_type)
    try:
        if method == "GET":
            resp = session.get(url, headers=req_headers, timeout=10)
        else:
            if content_type.get("Content-Type") == "application/json":
                resp = session.post(url, headers=req_headers, json=payload, timeout=10)
            else:
                resp = session.post(url, headers=req_headers, data=payload, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"Content-Type: {resp.headers.get('Content-Type')}")
            if 'json' in resp.headers.get('Content-Type', ''):
                try:
                    data = resp.json()
                    print(f"JSON keys: {data.keys() if isinstance(data, dict) else 'list'}")
                    if isinstance(data, dict) and 'h' in data and 'a' in data:
                        print(f"SUCCESS! Home shots: {len(data['h'])}, Away shots: {len(data['a'])}")
                        print("Sample home shot:", data['h'][0] if data['h'] else None)
                        break
                    else:
                        print("Unexpected structure:", json.dumps(data, indent=2)[:300])
                except Exception as e:
                    print(f"JSON decode error: {e}")
                    print("Response text:", resp.text[:300])
            else:
                print("Not JSON, maybe HTML")
                print(resp.text[:300])
        else:
            print(f"Response text: {resp.text[:200]}")
    except Exception as e:
        print(f"Request error: {e}")

print("\n--- All candidates tried ---")