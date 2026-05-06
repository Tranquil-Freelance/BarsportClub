#!/usr/bin/env python3
"""
Test the scraper endpoint by triggering a scrape for a known match.
"""
import asyncio
import sys
import aiohttp
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    match_id = 29955  # Example match ID from earlier debug
    url = f"http://localhost:8000/api/scraper/match/{match_id}"
    data = {}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=data) as resp:
                print(f"Status: {resp.status}")
                if resp.status == 202:
                    result = await resp.json()
                    print(f"Response: {result}")
                    print("Scraping triggered successfully.")
                else:
                    text = await resp.text()
                    print(f"Error response: {text}")
        except Exception as e:
            print(f"Request failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())