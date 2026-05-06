import requests
import json

match_id = 27362
base = "https://understat.com"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": f"{base}/match/{match_id}",
    "X-Requested-With": "XMLHttpRequest",
}

candidates = [
    ("GET", f"{base}/main/getMatchShots/{match_id}"),
    ("GET", f"{base}/main/getMatchShots/{match_id}/"),
    ("GET", f"{base}/main/getMatchShots?id={match_id}"),
    ("POST", f"{base}/main/getMatchShots"),
    ("POST", f"{base}/main/getMatchShots/{match_id}"),
]

for method, url in candidates:
    print(f"\nTrying {method} {url}")
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=10)
        else:
            resp = requests.post(url, headers=headers, data={"match_id": match_id}, timeout=10)
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            content_type = resp.headers.get('Content-Type', '')
            print(f"  Content-Type: {content_type}")
            if 'json' in content_type:
                try:
                    data = resp.json()
                    print(f"  JSON keys: {data.keys() if isinstance(data, dict) else 'list'}")
                    if isinstance(data, dict) and 'h' in data and 'a' in data:
                        print(f"  SUCCESS! Found shots data: home {len(data['h'])} away {len(data['a'])}")
                        # print snippet
                        print(f"  Sample home shot: {data['h'][0] if data['h'] else 'none'}")
                        break
                except json.JSONDecodeError:
                    print("  Not JSON")
            else:
                print("  Not JSON, maybe HTML")
                print(resp.text[:200])
        else:
            print(f"  Response text: {resp.text[:200]}")
    except Exception as e:
        print(f"  Error: {e}")

# Also try with additional headers like Origin
print("\n--- Trying with Origin header ---")
headers_with_origin = headers.copy()
headers_with_origin['Origin'] = 'https://understat.com'
resp = requests.get(f"{base}/main/getMatchShots/{match_id}", headers=headers_with_origin, timeout=10)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    try:
        data = resp.json()
        print(f"JSON keys: {data.keys()}")
    except:
        print(resp.text[:200])