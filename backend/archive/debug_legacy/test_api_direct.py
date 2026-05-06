import requests
import json

url = "https://understat.com/main/getMatchShots"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/json",
    "Referer": "https://understat.com/match/30116",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}
payload = {"id": 30116}

try:
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Response text: {resp.text[:500]}")
    data = resp.json()
    print(f"Keys: {data.keys()}")
    if 'h' in data and 'a' in data:
        print(f"Home shots: {len(data['h'])}")
        print(f"Away shots: {len(data['a'])}")
except Exception as e:
    print(f"Error: {e}")