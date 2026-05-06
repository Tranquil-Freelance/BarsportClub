import asyncio
import aiohttp
from understat import Understat

async def test():
    match_id = 27362
    async with aiohttp.ClientSession() as session:
        us = Understat(session)
        try:
            shots_data = await us.get_match_shots(match_id)
            print(f"Success: {shots_data}")
        except Exception as e:
            print(f"Exception type: {type(e)}")
            print(f"Exception str: {str(e)}")
            print(f"Exception repr: {repr(e)}")
            import traceback
            traceback.print_exc()
            # check if 'not found' in error
            if "not found" in str(e).lower() or "404" in str(e):
                print("Contains 'not found' or '404'")
            else:
                print("Does not contain")

if __name__ == "__main__":
    asyncio.run(test())