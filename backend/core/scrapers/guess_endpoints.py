import requests
import json

match_id = 27362
base = "https://understat.com"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": f"{base}/match/{match_id}",
}

candidates = [
    f"{base}/match/{match_id}/shotsData",
    f"{base}/match/{match_id}/shots",
    f"{base}/match/{match_id}/data",
    f"{base}/match/{match_id}/stats",
    f"{base}/match/{match_id}/playerStats",
    f"{base}/main/getMatchShots/{match_id}",
    f"{base}/main/getMatchStats/{match_id}",
    f"{base}/main/getMatchPlayerStats/{match_id}",
    f"{base}/api/match/{match_id}/shots",
    f"{base}/api/match/{match_id}/playerStats",
    f"{base}/api/match/{match_id}/data",
]

for url in candidates:
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        print(f"{url} -> {resp.status_code} {resp.reason}")
        if resp.status_code == 200:
            content_type = resp.headers.get('Content-Type', '')
            if 'json' in content_type:
                try:
                    data = resp.json()
                    print(f"   JSON keys: {data.keys() if isinstance(data, dict) else 'list'}")
                    # print snippet
                    print(f"   snippet: {json.dumps(data)[:200]}")
                except:
                    print("   Not JSON")
            else:
                print(f"   Content-Type: {content_type}")
                # maybe HTML
                if '<script' in resp.text[:200]:
                    print("   HTML")
    except Exception as e:
        print(f"{url} -> error: {e}")