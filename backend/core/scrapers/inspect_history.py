#!/usr/bin/env python3
"""
Inspect a team's history from Understat to see what fields are present.
"""
import asyncio
import aiohttp
import json
import sys
from aiohttp import ClientTimeout

UNDERSTAT_API_URL = "https://understat.com/getLeagueData/Serie_A/2025"

async def fetch_teams_data(session):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "X-Requested-With": "XMLHttpRequest",
    }
    timeout = ClientTimeout(total=30)
    async with session.get(UNDERSTAT_API_URL, headers=headers, timeout=timeout) as response:
        response.raise_for_status()
        text = await response.text()
        data = json.loads(text)
        return data

async def main():
    async with aiohttp.ClientSession() as http_session:
        try:
            data = await fetch_teams_data(http_session)
        except Exception as e:
            print(f"Failed to fetch teams data: {e}")
            sys.exit(1)
    
    teams_data = data.get("teams", {})
    if not teams_data:
        print("No teams found")
        return
    
    # Take first team
    team_id_str, team_data = next(iter(teams_data.items()))
    print(f"Team ID: {team_id_str}, name: {team_data.get('title')}")
    history = team_data.get("history", [])
    if history:
        print(f"History length: {len(history)}")
        # Print keys of first match
        first_match = history[0]
        print("Keys:", list(first_match.keys()))
        # Print values
        for k, v in first_match.items():
            print(f"  {k}: {v}")
        # Check for xpts
        if 'xpts' in first_match:
            print("xpts present!")
            # Sum xpts across history
            total_xpts = sum(m.get('xpts', 0) for m in history)
            print(f"Total xpts: {total_xpts}")
        else:
            print("xpts not found")
            # Check for any x-related fields
            x_fields = [k for k in first_match.keys() if k.startswith('x')]
            print("x-fields:", x_fields)
    else:
        print("No history")

if __name__ == "__main__":
    asyncio.run(main())