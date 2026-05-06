#!/usr/bin/env python3
import asyncio
import aiohttp
import re
import json
from aiohttp import ClientTimeout

async def main():
    url = "https://understat.com/league/Serie_A/2025"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    timeout = ClientTimeout(total=30)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=timeout) as resp:
            html = await resp.text()
            print(f"HTML length: {len(html)}")
            # Find all var assignments with JSON.parse
            pattern = re.compile(r'var\s+(\w+)\s*=\s*JSON\.parse\s*\(\s*\'(.*?)\'\s*\)', re.DOTALL)
            matches = pattern.findall(html)
            print(f"Found {len(matches)} variables")
            for var_name, encoded in matches[:20]:
                print(f"{var_name}: length {len(encoded)}")
                try:
                    decoded = encoded.encode('utf-8').decode('unicode_escape')
                    data = json.loads(decoded)
                    print(f"  type: {type(data)}")
                    if isinstance(data, list):
                        print(f"  list length: {len(data)}")
                    elif isinstance(data, dict):
                        print(f"  dict keys: {list(data.keys())[:5]}")
                except:
                    print("  decode error")
            # Also search for teamsData string
            if 'teamsData' in html:
                print("teamsData found as substring")
            else:
                print("teamsData NOT in html")
            # Write a snippet of HTML to file for inspection
            with open('debug_output.html', 'w', encoding='utf-8') as f:
                f.write(html[:20000])

if __name__ == '__main__':
    asyncio.run(main())