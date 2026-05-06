import urllib.request
import urllib.error
import json
import sys

url = 'http://localhost:8000/api/matches'
try:
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    resp = urllib.request.urlopen(req)
    print('Status:', resp.status)
    body = resp.read()
    data = json.loads(body)
    print('Success! Retrieved', len(data), 'matches')
    print('First match:', json.dumps(data[0], indent=2))
except urllib.error.HTTPError as e:
    print('HTTP Error:', e.code, e.reason)
    body = e.read()
    print('Body length:', len(body))
    if len(body) < 1000:
        print('Body:', body.decode())
    else:
        print('Body truncated')
    sys.exit(1)
except Exception as e:
    print('Other error:', e)
    sys.exit(1)