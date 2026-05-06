import asyncio
import aiohttp
from understat import Understat

async def main():
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        print("Testing get_league_results for Serie_A 2024")
        try:
            data = await understat.get_league_results('serie_a', 2024)
            print(f"Results: {len(data)} matches")
            if data:
                print(data[0])
        except Exception as e:
            print(f"Error in results: {e}")
        
        print("\nTesting get_league_fixtures for Serie_A 2025")
        try:
            data = await understat.get_league_fixtures('serie_a', 2025)
            print(f"Fixtures: {len(data)} matches")
            if data:
                print(data[0])
        except Exception as e:
            print(f"Error in fixtures: {e}")
        
        print("\nTesting get_league_fixtures for Serie_A 2024")
        try:
            data = await understat.get_league_fixtures('serie_a', 2024)
            print(f"Fixtures: {len(data)} matches")
            if data:
                print(data[0])
        except Exception as e:
            print(f"Error in fixtures: {e}")

if __name__ == "__main__":
    asyncio.run(main())