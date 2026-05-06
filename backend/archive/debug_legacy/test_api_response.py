#!/usr/bin/env python3
import aiohttp
import asyncio
import json

async def test():
    async with aiohttp.ClientSession() as session:
        headers = {'X-Requested-With': 'XMLHttpRequest'}
        async with session.get('https://understat.com/getLeagueData/Serie_A/2025', headers=headers) as resp:
            print(f'Status: {resp.status}')
            print(f'Content-Type: {resp.headers.get("content-type")}')
            text = await resp.text()
            print(f'First 500 chars:\n{text[:500]}')
            # Check for JSONP wrapper
            if text.startswith('callback('):
                print('JSONP wrapper detected')
                # extract json between parentheses
                import re
                match = re.search(r'callback\((.*)\)', text, re.DOTALL)
                if match:
                    text = match.group(1)
            try:
                data = json.loads(text)
                print('JSON parsed successfully')
                print('Keys:', data.keys())
                if 'teams' in data:
                    print(f'Number of teams: {len(data["teams"])}')
                    for team_id, team_data in list(data['teams'].items())[:2]:
                        print(f'  {team_id}: {team_data.get("title")}')
            except json.JSONDecodeError as e:
                print(f'JSON decode error: {e}')
                # try to see if there's a variable assignment like var teamsData = ...
                import re
                match = re.search(r'var teamsData\s*=\s*({.*?});', text, re.DOTALL)
                if match:
                    print('Found teamsData variable')
                    text = match.group(1)
                    try:
                        data = json.loads(text)
                        print('Parsed from variable')
                    except json.JSONDecodeError as e2:
                        print(f'Still error: {e2}')

if __name__ == '__main__':
    asyncio.run(test())