import requests
import json

match_id = 27362
url = "https://understat.com/main/getMatchShots"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": f"https://understat.com/match/{match_id}",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/json",
    "Origin": "https://understat.com",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}
payload = {"id": match_id}
print("Testing POST with JSON payload:", payload)
resp = requests.post(url, headers=headers, json=payload, timeout=10)
print(f"Status: {resp.status_code}")
print(f"Content-Type: {resp.headers.get('Content-Type')}")
if resp.status_code == 200:
    try:
        data = resp.json()
        print("Success! Response keys:", data.keys() if isinstance(data, dict) else type(data))
        if isinstance(data, dict) and 'h' in data and 'a' in data:
            print(f"Home shots: {len(data['h'])}, Away shots: {len(data['a'])}")
            print("Sample home shot:", data['h'][0] if data['h'] else None)
        else:
            print("Unexpected structure:", json.dumps(data, indent=2)[:500])
    except Exception as e:
        print("JSON decode error:", e)
        print("Response text:", resp.text[:500])
else:
    print("Response text:", resp.text[:500])