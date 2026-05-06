import asyncio
import aiohttp
import re
import sys

async def test_match(match_id):
    url = f'https://understat.com/match/{match_id}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=15.0) as response:
            print(f'HTTP status: {response.status}')
            if response.status != 200:
                print('Page not found')
                return
            html = await response.text()
            print(f'HTML length: {len(html)}')
            # Use the same regex as in analytics.py
            match = re.search(r'var\s+shotsData\s*=\s*JSON\.parse\s*\(\s*\'(.*?)\'\s*\)\s*;', html, re.DOTALL)
            if match:
                print('SUCCESS: shotsData found')
                encoded = match.group(1)
                print(f'Encoded length: {len(encoded)}')
                # decode
                decoded = encoded.encode('utf-8').decode('unicode_escape')
                import json
                data = json.loads(decoded)
                print(f'Decoded shots count: {len(data) if isinstance(data, list) else "dict"}')
                return True
            else:
                print('FAIL: shotsData not found with regex')
                # search for shotsData substring
                if 'shotsData' in html:
                    print('INFO: shotsData substring present, regex may be mismatched')
                    # find context
                    idx = html.find('shotsData')
                    snippet = html[max(0, idx-200):min(len(html), idx+200)]
                    print('Snippet:', snippet.replace('\n', ' '))
                else:
                    print('INFO: shotsData substring absent entirely')
                return False

if __name__ == '__main__':
    match_id = int(sys.argv[1]) if len(sys.argv) > 1 else 30116
    asyncio.run(test_match(match_id))