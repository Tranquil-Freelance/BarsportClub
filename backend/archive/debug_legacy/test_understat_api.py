import asyncio
import aiohttp
from understat import Understat

async def test():
    async with aiohttp.ClientSession() as session:
        us = Understat(session)
        try:
            shots = await us.get_match_shots(27362)
            print(f"Success: {len(shots.get('h', []))} home shots, {len(shots.get('a', []))} away shots")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())