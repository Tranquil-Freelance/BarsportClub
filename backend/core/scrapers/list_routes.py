import asyncio
import aiohttp
import json

async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8000/openapi.json') as resp:
            data = await resp.json()
            paths = data.get('paths', {})
            for path, methods in paths.items():
                if 'standings' in path:
                    print(path, list(methods.keys()))

if __name__ == '__main__':
    asyncio.run(main())