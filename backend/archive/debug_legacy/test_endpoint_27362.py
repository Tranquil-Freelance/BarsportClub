#!/usr/bin/env python3
"""
Test that the endpoint /match/27362/shots returns valid data.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_match_shots():
    response = client.get("/match/27362/shots")
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
        sys.exit(1)
    data = response.json()
    print("Response keys:", data.keys() if isinstance(data, dict) else "list")
    # Check structure
    if "match" in data and "shots" in data:
        shots = data["shots"]
        print(f"Home shots: {len(shots.get('h', []))}")
        print(f"Away shots: {len(shots.get('a', []))}")
        print("Success: endpoint returns expected structure.")
    else:
        # maybe the endpoint returns raw shots list
        if isinstance(data, list):
            print(f"Returned list of {len(data)} shots")
        else:
            print("Unexpected response format:", data)
    # Also test the alternative endpoint
    response2 = client.get("/api/matches/27362/shots")
    print(f"Alternative endpoint status: {response2.status_code}")
    if response2.status_code == 200:
        print("Alternative endpoint works.")

if __name__ == "__main__":
    test_match_shots()