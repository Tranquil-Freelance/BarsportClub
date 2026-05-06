import requests
import json
url = "https://understat.com/getLeagueData/Serie_A/2025"
resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
print(resp.status_code)
if resp.status_code == 200:
    data = resp.json()
    print(json.dumps(data, indent=2)[:1000])
else:
    print(resp.text[:500])