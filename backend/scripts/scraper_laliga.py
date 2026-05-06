"""
🚀 ESTRATTORE LA LIGA - METODO "PARTITA PER PARTITA"
Identico a Premier e Serie A. 
Lento (circa 2.5 ore), profondo, a prova di ban.
"""
import asyncio
import aiohttp
import random
import logging
import socket
from understat import Understat
from sqlalchemy import create_engine, text
import sys

# Log professionale per monitorare l'avanzamento
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s', 
    stream=sys.stdout
)

# ─── CONFIGURAZIONE DATABASE ──────────────────────────────────────────
DB_URL = "postgresql://postgres:password@localhost:5432/xpalermostat"
engine = create_engine(DB_URL)

LEAGUE = "La_liga"
SEASONS = [2021, 2022, 2023, 2024, 2025]

# ─── SISTEMI DI SICUREZZA ─────────────────────────────────────────────
async def apply_jitter():
    # Simula il tempo di lettura di un umano tra una pagina e l'altra
    wait_time = random.uniform(2.5, 5.0)
    await asyncio.sleep(wait_time)

async def trigger_hibernation():
    logging.warning("🔴 [ALLARME BAN] Errore 429 rilevato. Ibernazione di 30 minuti per resettare l'IP.")
    await asyncio.sleep(1800)

# ─── DATABASE (Tabella La Liga) ───────────────────────────────────────
def initialize_database():
    query = text("""
        CREATE TABLE IF NOT EXISTS laliga_match_players (
            id SERIAL PRIMARY KEY,
            match_id VARCHAR(50),
            player_id VARCHAR(50),
            player_name VARCHAR(150),
            team_name VARCHAR(100),
            season VARCHAR(10),
            position VARCHAR(20),
            time INTEGER,
            goals INTEGER,
            assists INTEGER,
            shots INTEGER,
            key_passes INTEGER,
            xg FLOAT,
            xa FLOAT,
            npxg FLOAT,
            xgchain FLOAT,
            xgbuildup FLOAT,
            UNIQUE(match_id, player_id)
        );
    """)
    with engine.connect() as conn:
        conn.execute(query)
        conn.commit()
    logging.info("✅ Database La Liga inizializzato correttamente.")

# ─── MOTORE DI ESTRAZIONE ──────────────────────────────────────────────
async def safe_fetch(understat_method, *args):
    retries = 0
    while retries < 5:
        try:
            await apply_jitter()
            return await understat_method(*args)
        except aiohttp.ClientResponseError as e:
            if e.status == 429:
                await trigger_hibernation()
                retries += 1
            else:
                logging.error(f"❌ Errore HTTP {e.status}. Riprovo...")
                retries += 1
                await asyncio.sleep(10)
        except Exception as e:
            logging.error(f"❌ Connessione fallita: {e}. Riprovo...")
            retries += 1
            await asyncio.sleep(10)
    return None

async def process_season(session, season):
    understat = Understat(session)
    logging.info(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logging.info(f"🇪🇸 INIZIO STAGIONE LA LIGA: {season}")
    
    # 1. Recupero calendario
    matches = await safe_fetch(understat.get_league_results, LEAGUE, season)
    if not matches:
        logging.error(f"⚠️ Impossibile recuperare partite per stagione {season}")
        return

    played_matches = [m for m in matches if m.get("isResult")]
    logging.info(f"🔍 Trovate {len(played_matches)} partite giocate. Avvio scansione...")

    with engine.connect() as conn:
        for idx, m in enumerate(played_matches, 1):
            match_id = str(m.get("id"))
            h_team = m.get("h",{}).get("title")
            a_team = m.get("a",{}).get("title")
            
            # 2. Entra nel match per estrarre i dati dei giocatori
            logging.info(f"  [{idx}/{len(played_matches)}] Match ID {match_id}: {h_team} vs {a_team}")
            match_players = await safe_fetch(understat.get_match_players, match_id)
            
            if match_players:
                for side in ['h', 'a']:
                    current_team = h_team if side == 'h' else a_team
                    for p_id, p_data in match_players.get(side, {}).items():
                        query = text("""
                            INSERT INTO laliga_match_players 
                            (match_id, player_id, player_name, team_name, season, position, time, goals, assists, shots, key_passes, xg, xa, npxg, xgchain, xgbuildup)
                            VALUES 
                            (:m_id, :p_id, :name, :team, :sea, :pos, :time, :g, :a, :shots, :kp, :xg, :xa, :npxg, :xgchain, :xgbuildup)
                            ON CONFLICT (match_id, player_id) DO NOTHING;
                        """)
                        try:
                            conn.execute(query, {
                                "m_id": match_id, "p_id": p_id, "name": p_data.get("player"),
                                "team": current_team, "sea": str(season),
                                "pos": p_data.get("position"), "time": int(p_data.get("time", 0)),
                                "g": int(p_data.get("goals", 0)), "a": int(p_data.get("assists", 0)),
                                "shots": int(p_data.get("shots", 0)), "kp": int(p_data.get("key_passes", 0)),
                                "xg": float(p_data.get("xG", 0.0)), "xa": float(p_data.get("xA", 0.0)),
                                "npxg": float(p_data.get("npxG", 0.0)),
                                "xgchain": float(p_data.get("xGChain", 0.0)), "xgbuildup": float(p_data.get("xGBuildup", 0.0))
                            })
                        except Exception:
                            pass
                conn.commit()

async def main():
    initialize_database()
    connector = aiohttp.TCPConnector(family=socket.AF_INET, ssl=False, force_close=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        for season in SEASONS:
            await process_season(session, season)
    logging.info("\n🎯 LA LIGA COMPLETATA. DATABASE AGGIORNATO.")

if __name__ == "__main__":
    asyncio.run(main())