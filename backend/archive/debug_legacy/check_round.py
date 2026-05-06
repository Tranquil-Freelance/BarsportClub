import requests
import json

try:
    r = requests.get('http://localhost:8000/api/matches?round=29')
    print(f"Status: {r.status_code}")
    data = r.json()
    print(f"Total matches for round 29: {len(data)}")
    for i, m in enumerate(data[:5]):
        print(f"{i}: id={m.get('id')}, round={m.get('round')}, date={m.get('date')}, home={m.get('home_team')}, away={m.get('away_team')}")
    # Also check a match with round null
    r2 = requests.get('http://localhost:8000/api/matches?round=1')
    data2 = r2.json()
    print(f"\nRound 1 matches: {len(data2)}")
    if data2:
        print(f"First match round: {data2[0].get('round')}")
except Exception as e:
    print(f"Error: {e}")