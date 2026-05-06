import asyncio
import aiohttp
import logging
import random
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from understat import Understat

from app.scraper.sync_calendar import sync_league_calendar
from app.services.db_ingestion import upsert_shots, upsert_player_match_stats

logger = logging.getLogger(__name__)

# ─── CONFIGURAZIONE ───────────────────────────────────────────────────────────
LEAGUES = ['EPL', 'La_liga', 'Bundesliga', 'Serie_A', 'Ligue_1']
SEASON = "2025"

LEAGUE_ID_MAP = {
    'Serie_A': 1,
    'EPL': 2,
    'La_liga': 3,
    'Bundesliga': 4,
    'Ligue_1': 5,
}

async def apply_jitter():
    jitter = random.uniform(4.0, 9.0)
    logger.info(f"⏳ Jitter: attesa di {jitter:.2f}s per evitare ban.")
    await asyncio.sleep(jitter)

# ─── IL CECCHINO: ESTRAZIONE TOTALE ───────────────────────────────────────────
async def sniper_strike(session: AsyncSession, match_id: str, title: str):
    """
    Entra nella partita, scarica TUTTO (tiri e giocatori) e salva.
    """
    logger.info(f"🎯 Bersaglio acquisito: {title} (ID: {match_id})")

    async with aiohttp.ClientSession() as http_session:
        understat = Understat(http_session)
        await apply_jitter()
        
        try:
            # 1. Scarica i tiri (per la Timing Chart)
            shots_raw = await understat.get_match_shots(match_id)
            
            # 2. Scarica i giocatori (per le stats avanzate)
            players_raw = await understat.get_match_players(match_id)

            # --- Salvataggio Tiri ---
            if shots_raw:
                # Uniamo tiri casa (h) e trasferta (a)
                home_shots = shots_raw.get('h', [])
                away_shots = shots_raw.get('a', [])
                combined_shots = home_shots + away_shots
                
                if combined_shots:
                    df_shots = pd.DataFrame(combined_shots)
                    df_shots['match_id'] = match_id
                    await upsert_shots(session, df_shots)
                    logger.info(f"✅ Tiri salvati per {title}")

            # --- Salvataggio Statistiche Giocatori ---
            if players_raw:
                # Trasformiamo il dizionario Understat in una lista piatta per il DataFrame
                player_list = []
                for team_type in ['h', 'a']:
                    for p_id, p_data in players_raw.get(team_type, {}).items():
                        p_data['player_id'] = p_id
                        p_data['match_id'] = match_id
                        p_data['team_type'] = team_type
                        player_list.append(p_data)
                
                if player_list:
                    df_players = pd.DataFrame(player_list)
                    await upsert_player_match_stats(session, df_players)
                    logger.info(f"✅ Stats giocatori salvate per {title}")

        except Exception as e:
            logger.error(f"❌ Errore durante lo strike su {title}: {e}")
            raise

# ─── FUNZIONE DI SINCRONIZZAZIONE GENERALE ────────────────────────────────────
async def sync_and_scrape_finished_matches(session: AsyncSession) -> None:
    """Sincronizza il calendario e scarica i dettagli delle partite recenti."""
    for league_slug in LEAGUES:
        league_id = LEAGUE_ID_MAP.get(league_slug)
        await sync_league_calendar(session, league_slug, int(SEASON), league_id)
        await apply_jitter()

    # Qui potresti aggiungere la logica per cercare i match non ancora 'is_scraped'
    # ma per ora ci concentriamo sul far funzionare il comando manuale.
    logger.info("Sync calendario completato.")

async def run_sniper_protocol() -> None:
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        await sync_and_scrape_finished_matches(session)
        await session.commit()