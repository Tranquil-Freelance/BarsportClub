import requests
import sys

match_id = 27362
url = 'https://understat.com/match/shotsData'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Referer': f'https://understat.com/match/{match_id}',
}
params = {'match_id': match_id}
print(f'Testing GET {url} with params {params}')
resp = requests.get(url, headers=headers, params=params, timeout=10)
print('Status:', resp.status_code)
print('Content-Type:', resp.headers.get('Content-Type'))
if resp.status_code == 200:
    try:
        data = resp.json()
        print('JSON keys:', data.keys() if isinstance(data, dict) else type(data))
        # print sample
        if isinstance(data, dict) and 'h' in data and 'a' in data:
            print(f"Home shots: {len(data['h'])}")
            print(f"Away shots: {len(data['a'])}")
    except Exception as e:
        print('JSON decode error:', e)
        print('Response text (first 1000):', resp.text[:1000])
else:
    print('Response text (first 1000):', resp.text[:1000])