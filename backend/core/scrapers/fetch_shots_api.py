import requests
import json

match_id = 30116
url = f"https://understat.com/main/getMatchPlayerStats/{match_id}"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": f"https://understat.com/match/{match_id}",
    "X-Requested-With": "XMLHttpRequest",
}
try:
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Content-Type: {resp.headers.get('Content-Type')}")
    if resp.status_code == 200:
        try:
            data = resp.json()
            print("JSON parsed successfully")
            print(f"Type: {type(data)}")
            if isinstance(data, dict):
                print(f"Keys: {list(data.keys())}")
                # maybe shots are under 'shots' or 'data'
                if 'shots' in data:
                    print(f"Shots keys: {data['shots'].keys() if isinstance(data['shots'], dict) else 'list'}")
                if 'data' in data:
                    print(f"Data type: {type(data['data'])}")
            # print first 500 chars of raw response
            print("Raw response snippet:", json.dumps(data, indent=2)[:500])
        except json.JSONDecodeError:
            print("Response is not JSON")
            print("Text snippet:", resp.text[:500])
    else:
        print("Response text:", resp.text[:200])
except Exception as e:
    print(f"Error: {e}")