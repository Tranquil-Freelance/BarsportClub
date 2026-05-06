import requests
import json

match_id = 27362
url = f"https://understat.com/main/getMatchShots/{match_id}"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": f"https://understat.com/match/{match_id}",
    "X-Requested-With": "XMLHttpRequest",
}
resp = requests.get(url, headers=headers, timeout=10)
print(f"Status: {resp.status_code}")
print(f"Content-Type: {resp.headers.get('Content-Type')}")
print(f"Response length: {len(resp.text)}")
if resp.status_code == 200:
    try:
        data = resp.json()
        print("JSON parsed successfully")
        print(f"Type: {type(data)}")
        if isinstance(data, dict):
            print(f"Keys: {list(data.keys())}")
            # maybe shots are under 'shots' or 'data'
            for key in data.keys():
                val = data[key]
                if isinstance(val, list):
                    print(f"  {key}: list length {len(val)}")
                    if len(val) > 0:
                        print(f"    sample item keys: {val[0].keys() if isinstance(val[0], dict) else 'not dict'}")
                elif isinstance(val, dict):
                    print(f"  {key}: dict keys {list(val.keys())}")
        elif isinstance(data, list):
            print(f"List length: {len(data)}")
            if len(data) > 0:
                print(f"First item keys: {data[0].keys() if isinstance(data[0], dict) else 'not dict'}")
        # print snippet
        print("\nSnippet:", json.dumps(data, indent=2)[:500])
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print("Response text:", resp.text[:200])
else:
    print("Response text:", resp.text[:200])