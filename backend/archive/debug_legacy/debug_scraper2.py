import asyncio
import aiohttp
import re

async def test(match_id):
    url = f'https://understat.com/match/{match_id}'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=15.0) as resp:
            print('Status:', resp.status)
            html = await resp.text()
            print('HTML length:', len(html))
            match = re.search(r'var\s+shotsData\s*=\s*JSON\.parse\s*\(\s*\'(.*?)\'\s*\)\s*;', html, re.DOTALL)
            if match:
                print('Found shotsData')
                print('Encoded length:', len(match.group(1)))
                # decode
                import json
                decoded = match.group(1).encode('utf-8').decode('unicode_escape')
                data = json.loads(decoded)
                print('Decoded shots count:', len(data) if isinstance(data, list) else 'dict')
            else:
                print('shotsData not found')
                # search for shotsData in html
                if 'shotsData' in html:
                    print('shotsData string present')
                else:
                    print('shotsData string absent')
                # print snippet around shotsData
                idx = html.find('shotsData')
                if idx != -1:
                    print('Context:', html[idx-200:idx+200])

if __name__ == '__main__':
    asyncio.run(test(30116))