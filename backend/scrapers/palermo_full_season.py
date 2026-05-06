#!/usr/bin/env python3
"""
THE REAL DEAL – Como Serie A (Understat Certified).
FIX: reset_index() to solve KeyError and properly map Understat MultiIndex.
"""
import asyncio
import logging
import pandas as pd
import soccerdata as sd
import uuid
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.football import League, Team, MatchCalendar, Player, PlayerMatchStat

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

LEAGUE_NAME = "Serie A"
UNDERSTAT_LEAGUE = "ITA-Serie A"
TEAM_NAME = "Como"
SEASON = "2024"

async def main():
    logger.info(f"AVVIO ESTRAZIONE DATI REALI: {TEAM_NAME}")
    
    async with AsyncSessionLocal() as session:
        # 1. Recupero/Creazione League
        res_l = await session.execute(select(League).where(League.name == LEAGUE_NAME))
        league = res_l.scalars().first()
        if not league:
            league = League(name=LEAGUE_NAME, understat_slug=UNDERSTAT_LEAGUE)
            session.add(league)
            await session.commit()
            await session.refresh(league)

        # 2. Inizializzazione Understat
        us = sd.Understat(leagues=UNDERSTAT_LEAGUE, seasons=SEASON)
        df_schedule = us.read_schedule().reset_index()

        # 3. Gestione Team
        res_t = await session.execute(select(Team).where(Team.name == TEAM_NAME))
        team_obj = res_t.scalars().first()
        if not team_obj:
            team_obj = Team(name=TEAM_NAME, league_id=league.id)
            session.add(team_obj)
            await session.commit()
            await session.refresh(team_obj)

        # 4. Filtro per l'ultimo match completato
        df_como = df_schedule[(df_schedule['home_team'] == TEAM_NAME) | (df_schedule['away_team'] == TEAM_NAME)].copy()
        df_como['is_completed'] = df_como['home_goals'].notna()
        completed = df_como[df_como['is_completed']]
        
        if completed.empty:
            logger.warning("Nessun match completato trovato.")
            return

        last_match = completed.iloc[-1]
        # Troviamo l'ID del match (match_id)
        real_id = last_match['match_id'] if 'match_id' in last_match else last_match.name
        
        logger.info(f"Scaricamento statistiche REALI per il match ID: {real_id}")
        
        # ESTRAZIONE STATS E RESET INDEX (Fondamentale per evitare KeyError)
        df_stats = us.read_player_match_stats(match_id=int(real_id)).reset_index()
        
        if df_stats.empty:
            logger.error("Dati non ricevuti da Understat.")
            return

        # 5. Pulizia e Inserimento
        await session.execute(delete(PlayerMatchStat))
        await session.commit()

        # Identifichiamo le colonne corrette (Understat a volte usa 'time' invece di 'minutes')
        time_col = 'time' if 'time' in df_stats.columns else 'minutes'

        for idx, row in df_stats.iterrows():
            if row['team'] != TEAM_NAME: continue
            
            p_name = row['player']
            
            # Recupero/Creazione Player
            res_p = await session.execute(select(Player).where(Player.name == p_name))
            db_player = res_p.scalars().first()
            if not db_player:
                db_player = Player(name=p_name, current_team_id=team_obj.id)
                session.add(db_player)
                await session.flush()

            # DATI REALI AL 100%
            new_stat = PlayerMatchStat(
                id=str(uuid.uuid4()),
                player_id=db_player.id,
                match_id=1, # Per la demo colleghiamo tutto a un match ID placeholder
                minutes_played=int(row[time_col]),
                goals=int(row['goals']),
                assists=int(row['assists']),
                shots=int(row['shots']),
                key_passes=int(row['key_passes']),
                xG=float(row['xG']),
                xA=float(row['xA']),
                position=row['position'],
                xGChain=float(row['xGChain']) if 'xGChain' in row else 0.0,
                xGBuildup=float(row['xGBuildup']) if 'xGBuildup' in row else 0.0
            )
            session.add(new_stat)

        await session.commit()
        logger.info(f"✅ SUCCESS: Caricati dati REALI di Understat per {TEAM_NAME}.")

if __name__ == "__main__":
    asyncio.run(main())