import requests
import json
import sys

match_id = 30116
url = f'https://understat.com/match/getMatchData/{match_id}'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': f'https://understat.com/match/{match_id}',
    'X-Requested-With': 'XMLHttpRequest',
}
print('Requesting:', url, file=sys.stderr)
try:
    resp = requests.get(url, headers=headers, timeout=10)
    print('Status:', resp.status_code, file=sys.stderr)
    print('Content-Type:', resp.headers.get('Content-Type'), file=sys.stderr)
    if resp.status_code == 200:
        data = resp.json()
        print('Keys:', list(data.keys()), file=sys.stderr)
        if 'shots' in data:
            shots = data['shots']
            print('Shots type:', type(shots), file=sys.stderr)
            if isinstance(shots, dict):
                print('Home shots count:', len(shots.get('h', [])), file=sys.stderr)
                print('Away shots count:', len(shots.get('a', [])), file=sys.stderr)
                # print first shot
                if shots.get('h'):
                    print('Example home shot:', shots['h'][0], file=sys.stderr)
                if shots.get('a'):
                    print('Example away shot:', shots['a'][0], file=sys.stderr)
        else:
            print('No shots key', file=sys.stderr)
            # print all keys
            for k in data.keys():
                print(k, file=sys.stderr)
    else:
        print('Response text:', resp.text[:200], file=sys.stderr)
except Exception as e:
    print('Error:', e, file=sys.stderr)