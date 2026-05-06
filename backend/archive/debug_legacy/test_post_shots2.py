import requests
match_id = 27362
url = 'https://understat.com/match/shotsData'
headers = {
    'User-Agent': 'Mozilla/5.0',
    'X-Requested-With': 'XMLHttpRequest',
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Referer': f'https://understat.com/match/{match_id}',
}
payload = {'id': match_id}
print('POST', url)
resp = requests.post(url, headers=headers, json=payload, timeout=10)
print('Status:', resp.status_code)
print('Content-Type:', resp.headers.get('Content-Type'))
if resp.status_code == 200:
    try:
        data = resp.json()
        print('JSON keys:', data.keys() if isinstance(data, dict) else type(data))
        if isinstance(data, dict) and 'h' in data and 'a' in data:
            print(f"Home shots: {len(data['h'])}")
            print(f"Away shots: {len(data['a'])}")
    except Exception as e:
        print('JSON decode error:', e)
        print('Response text (first 500):', resp.text[:500])
else:
    print('Response text (first 500):', resp.text[:500])