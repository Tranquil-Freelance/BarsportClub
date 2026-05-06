import asyncio
import aiohttp
from understat import Understat

async def main():
    async with aiohttp.ClientSession() as session:
        us = Understat(session)
        matches = await us.get_league_results("serie_a", 2024)
        print(f"Found {len(matches)} matches")
        for match in matches[:10]:
            match_id = int(match["id"])
            home = match["h"]["title"]
            away = match["a"]["title"]
            print(f"Match ID: {match_id} - {home} vs {away}")
        if matches:
            first_id = int(matches[0]["id"])
            print(f"\nFirst match ID: {first_id}")
            # test shots
            shots = await us.get_match_shots(first_id)
            print(f"Shots data keys: {shots.keys() if isinstance(shots, dict) else 'not dict'}")
            if isinstance(shots, dict) and 'h' in shots and 'a' in shots:
                print(f"Home shots: {len(shots['h'])}, Away shots: {len(shots['a'])}")
            else:
                print("Shots structure unexpected")

if __name__ == "__main__":
    asyncio.run(main())