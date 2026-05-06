import requests
import json

url = "http://localhost:8000/api/v1/scraper/scrape-latest-round"
payload = {"league": "Serie A", "season": "2025"}
try:
    resp = requests.post(url, json=payload, timeout=2)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")