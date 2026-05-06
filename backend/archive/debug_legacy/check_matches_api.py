import requests
import json

try:
    r = requests.get('http://localhost:8000/api/matches')
    print(f"Status: {r.status_code}")
    data = r.json()
    print(f"Total matches: {len(data)}")
    for i, m in enumerate(data[:10]):
        print(f"{i}: id={m.get('id')}, round={m.get('round')}, date={m.get('date')}, home={m.get('home_team')}, away={m.get('away_team')}")
except Exception as e:
    print(f"Error: {e}")