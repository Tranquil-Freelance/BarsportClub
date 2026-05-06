#!/usr/bin/env python3
"""
xPalermoStat – Robust Serie A Importer

Importa tutte le partite e gli shots della Serie A
dalla stagione corrente da Understat.

Caratteristiche:
- ignora duplicati
- continua se una partita fallisce
- evita di reinserire match esistenti
"""

import asyncio
import aiohttp

from understat import Understat
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.session import AsyncSessionLocal
from app.db.models import Match, Shot


LEAGUE = "serie_a"
SEASON = 2025


async def main():

    print("Connessione a Understat...")

    async with aiohttp.ClientSession() as session:

        understat = Understat(session)

        print("Scarico lista partite Serie A...")

        matches = await understat.get_league_results(LEAGUE, SEASON)

    print(f"Partite trovate: {len(matches)}")

    async with AsyncSessionLocal() as db:

        for match in matches:

            match_id = int(match["id"])

            # controlla se il match esiste
            result = await db.execute(
                select(Match).where(Match.id == match_id)
            )

            existing = result.scalars().first()

            if existing:
                print(f"Match già presente: {match_id}")
                continue

            print(f"Import match: {match_id}")

            try:

                db_match = Match(
                    id=match_id,
                    home_team=match["h"]["title"],
                    away_team=match["a"]["title"]
                )

                db.add(db_match)
                await db.flush()

                async with aiohttp.ClientSession() as session:

                    understat = Understat(session)

                    shots_data = await understat.get_match_shots(match_id)

                seen = set()

                # squadra casa
                for shot in shots_data["h"]:

                    key = (
                        match_id,
                        int(shot["minute"]),
                        shot["player"],
                        "h"
                    )

                    if key in seen:
                        continue

                    seen.add(key)

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

                # squadra trasferta
                for shot in shots_data["a"]:

                    key = (
                        match_id,
                        int(shot["minute"]),
                        shot["player"],
                        "a"
                    )

                    if key in seen:
                        continue

                    seen.add(key)

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

            except IntegrityError:

                print(f"Duplicato rilevato nel match {match_id}, ignorato")
                await db.rollback()

            except Exception as e:

                print(f"Errore nel match {match_id}: {e}")
                await db.rollback()

            await asyncio.sleep(1)

    print("Import completato.")


if __name__ == "__main__":
    asyncio.run(main())