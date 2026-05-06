import urllib.request
import urllib.error
import json

try:
    req = urllib.request.Request('http://localhost:8000/api/matches', headers={'Accept': 'application/json'})
    resp = urllib.request.urlopen(req)
    print('Status:', resp.status)
    data = json.load(resp)
    print('First match:', data[0] if data else 'empty')
except urllib.error.HTTPError as e:
    print('HTTP Error:', e.code, e.reason)
    print('Body:', e.read().decode()[:500])
except Exception as e:
    print('Other error:', e)