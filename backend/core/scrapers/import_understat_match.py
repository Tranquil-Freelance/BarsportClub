import asyncio
import aiohttp
import uuid

from understat import Understat
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.football import Player, PlayerMatchStat, Team, MatchCalendar


TEAM_NAME = "Como"
MATCH_ID = 27735


async def main():

    # -------------------------
    # scarica dati da Understat
    # -------------------------

    async with aiohttp.ClientSession() as http_session:

        us = Understat(http_session)

        players_data = await us.get_match_players(MATCH_ID)

        matches = await us.get_league_results("serie_a", 2024)

    # trova la partita corretta
    match_data = None

    for m in matches:
        if int(m["id"]) == MATCH_ID:
            match_data = m
            break

    if not match_data:
        print("Partita non trovata su Understat")
        return

    # -------------------------
    # database
    # -------------------------

    async with AsyncSessionLocal() as db:

        # -------------------------
        # TEAM
        # -------------------------

        result = await db.execute(
            select(Team).where(Team.name == TEAM_NAME)
        )

        team = result.scalars().first()

        if not team:
            team = Team(name=TEAM_NAME)
            db.add(team)
            await db.flush()

        team_id = team.id

        # -------------------------
        # MATCH
        # -------------------------

        result = await db.execute(
            select(MatchCalendar).where(MatchCalendar.id == MATCH_ID)
        )

        db_match = result.scalars().first()

        if not db_match:

            db_match = MatchCalendar(
                id=MATCH_ID,
                home_team=match_data["h"]["title"],
                away_team=match_data["a"]["title"],
                home_goals=int(match_data["goals"]["h"]),
                away_goals=int(match_data["goals"]["a"])
            )

            db.add(db_match)
            await db.flush()

        # -------------------------
        # PLAYERS
        # -------------------------

        for player in players_data["h"].values():

            player_name = player["player"]

            result = await db.execute(
                select(Player).where(Player.name == player_name)
            )

            db_player = result.scalars().first()

            if not db_player:

                db_player = Player(
                    name=player_name,
                    current_team_id=team_id
                )

                db.add(db_player)
                await db.flush()

            # -------------------------
            # PLAYER MATCH STAT
            # -------------------------

            stat = PlayerMatchStat(

                id=uuid.uuid4(),

                player_id=db_player.id,
                match_id=MATCH_ID,

                minutes_played=int(player["time"]),
                goals=int(player["goals"]),
                assists=int(player["assists"]),

                shots=int(player["shots"]),
                key_passes=int(player["key_passes"]),

                xG=float(player["xG"]),
                xA=float(player["xA"]),

                position=player["position"],

                xGChain=float(player["xGChain"]),
                xGBuildup=float(player["xGBuildup"])
            )

            db.add(stat)

        await db.commit()

        print("Import completato.")


asyncio.run(main())