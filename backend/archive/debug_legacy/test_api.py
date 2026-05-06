#!/usr/bin/env python3
import requests
import json

url = 'https://understat.com/api/league/Serie_A/2024'
headers = {'User-Agent': 'Mozilla/5.0'}
try:
    r = requests.get(url, headers=headers)
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        print(r.text[:500])
        try:
            data = r.json()
            print(json.dumps(data, indent=2)[:1000])
        except:
            pass
except Exception as e:
    print(e)

# also try team endpoint
url2 = 'https://understat.com/api/team/Como/2024'
try:
    r = requests.get(url2, headers=headers)
    print(f'Team API status: {r.status_code}')
    print(r.text[:500])
except Exception as e:
    print(e)