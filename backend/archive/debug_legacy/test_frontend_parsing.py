#!/usr/bin/env python3
"""
Test that the backend response matches the frontend parsing logic.
"""
import sys
sys.path.insert(0, '.')

import asyncio
from app.db.session import AsyncSessionLocal
from app.api.crud import get_match_shots

async def test():
    async with AsyncSessionLocal() as session:
        # Test match 27362
        data = await get_match_shots(session, 27362)
        print("Response keys:", data.keys())
        print("Match:", data['match'])
        print("Shots keys:", data['shots'].keys())
        print("Home shots count:", len(data['shots']['h']))
        print("Away shots count:", len(data['shots']['a']))
        # Check each shot has required fields
        for team in ('h', 'a'):
            for shot in data['shots'][team]:
                assert 'minute' in shot
                assert 'player' in shot
                assert 'xG' in shot
                assert 'result' in shot
                assert 'X' in shot
                assert 'Y' in shot
                assert 'situation' in shot  # may be None
                assert 'shotType' in shot
                assert 'assist' in shot
        print("All required fields present.")
        # Simulate frontend processing
        processed = []
        if isinstance(data, list):
            processed = data
        elif data.get('h') and data.get('a'):
            home_shots = [{'team_type': 'h', **s} for s in data['h']]
            away_shots = [{'team_type': 'a', **s} for s in data['a']]
            processed = home_shots + away_shots
        elif data.get('shots'):
            home_shots = [{'team_type': 'h', **s} for s in data['shots']['h']]
            away_shots = [{'team_type': 'a', **s} for s in data['shots']['a']]
            processed = home_shots + away_shots
        else:
            raise ValueError("Unknown format")
        print(f"Processed shots count: {len(processed)}")
        # Ensure mapping works
        for s in processed:
            s['minute'] = int(s['minute']) if isinstance(s['minute'], str) else s['minute']
            s['X'] = float(s['X']) if isinstance(s['X'], str) else s['X']
            s['Y'] = float(s['Y']) if isinstance(s['Y'], str) else s['Y']
            s['xG'] = float(s['xG']) if isinstance(s['xG'], str) else s['xG']
        print("Frontend simulation passed.")

if __name__ == '__main__':
    asyncio.run(test())