import requests
try:
    resp = requests.get("http://localhost:8000/api/v1/scraper/status")
    print(f"Status: {resp.status_code}")
    print(resp.json())
except Exception as e:
    print(e)