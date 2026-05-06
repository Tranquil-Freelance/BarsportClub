import asyncio
import json
from understat import Understat
import aiohttp


LEAGUE = "serie_a"
SEASON = "2025"


async def main():

    async with aiohttp.ClientSession() as session:

        understat = Understat(session)

        print("Downloading Serie A matches...")

        matches = await understat.get_league_results(LEAGUE, SEASON)

        print("Matches found:", len(matches))

        print("Downloading players...")

        players = await understat.get_league_players(LEAGUE, SEASON)

        print("Players found:", len(players))

        all_shots = []

        print("Downloading shots for each match...")

        for match in matches:

            match_id = match["id"]

            try:

                shots = await understat.get_match_shots(match_id)

                for shot in shots:
                    shot["match_id"] = match_id
                    all_shots.append(shot)

            except Exception as e:

                print("Failed match:", match_id)

        print("Total shots downloaded:", len(all_shots))

        data = {
            "league": LEAGUE,
            "season": SEASON,
            "players": players,
            "matches": matches,
            "shots": all_shots
        }

        with open("serie_a_understat.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print("\nDownload complete")
        print("Saved to serie_a_understat.json")


asyncio.run(main())