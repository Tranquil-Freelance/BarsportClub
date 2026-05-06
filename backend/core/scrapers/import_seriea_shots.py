import asyncio
import aiohttp

from understat import Understat
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.models import Match, Shot


LEAGUE = "serie_a"
SEASON = 2024


async def main():

    async with aiohttp.ClientSession() as session:

        us = Understat(session)

        print("Scarico partite Serie A...")

        matches = await us.get_league_results(LEAGUE, SEASON)

    async with AsyncSessionLocal() as db:

        for match in matches:

            match_id = int(match["id"])

            result = await db.execute(
                select(Match).where(Match.id == match_id)
            )

            existing_match = result.scalars().first()

            if existing_match:
                print("Match già presente:", match_id)
                continue

            print("Import match:", match_id)

            db_match = Match(
                id=match_id,
                home_team=match["h"]["title"],
                away_team=match["a"]["title"]
            )

            db.add(db_match)
            await db.flush()

            async with aiohttp.ClientSession() as session:

                us = Understat(session)

                shots_data = await us.get_match_shots(match_id)

            # shots casa
            for shot in shots_data["h"]:

                new_shot = Shot(
                    match_id=match_id,
                    minute=int(shot["minute"]),
                    player=shot["player"],
                    xG=float(shot["xG"]),
                    result=shot["result"],
                    team_type="h",
                    X=float(shot["X"]),
                    Y=float(shot["Y"])
                )

                db.add(new_shot)

            # shots trasferta
            for shot in shots_data["a"]:

                new_shot = Shot(
                    match_id=match_id,
                    minute=int(shot["minute"]),
                    player=shot["player"],
                    xG=float(shot["xG"]),
                    result=shot["result"],
                    team_type="a",
                    X=float(shot["X"]),
                    Y=float(shot["Y"])
                )

                db.add(new_shot)

        await db.commit()

        print("Import Serie A completato.")


asyncio.run(main())