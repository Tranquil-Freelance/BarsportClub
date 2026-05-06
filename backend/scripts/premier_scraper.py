"""
🚀 EXTRATTORE PREMIER LEAGUE - METODO "PARTITA PER PARTITA" (Come ieri)
Lento (ore di esecuzione) ma 100% a prova di Ban e Crash di Rete.
"""
import asyncio
import aiohttp
import random
import logging
import socket
from understat import Understat
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import sys

logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)

# SOSTITUISCI CON LE TUE CREDENZIALI
DB_URL = "postgresql://postgres:password@localhost:5432/xpalermostat"
engine = create_engine(DB_URL)

LEAGUE = "epl"
SEASONS = [2021, 2022, 2023, 2024, 2025]

# ─── SISTEMI DI SICUREZZA ─────────────────────────────────────────────
async def apply_jitter():
    wait_time = random.uniform(2.1, 4.5)
    await asyncio.sleep(wait_time)

async def trigger_hibernation():
    logging.warning("🔴 [ALLARME BAN] Errore 429. Ibernazione profonda (30 min).")
    await asyncio.sleep(1800)

# ─── DATABASE (Tabella Giocatori PER PARTITA) ─────────────────────────
def initialize_database():
    query = text("""
        CREATE TABLE IF NOT EXISTS premier_match_players (
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
    logging.info("✅ Database inizializzato (Metodo Partita per Partita).")

# ─── ESTRATTORE ────────────────────────────────────────────────────────
async def safe_fetch(understat_method, *args):
    retries = 0
    while retries < 4:
        try:
            await apply_jitter()
            return await understat_method(*args)
        except aiohttp.ClientResponseError as e:
            if e.status == 429:
                await trigger_hibernation()
                retries += 1
            else:
                retries += 1
                await asyncio.sleep(5)
        except Exception:
            retries += 1
            await asyncio.sleep(5)
    return None

async def process_season(session, season):
    understat = Understat(session)
    logging.info(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logging.info(f"🏆 INIZIO STAGIONE {season}")
    
    # 1. Prende solo l'elenco delle partite
    matches = await safe_fetch(understat.get_league_results, LEAGUE, season)
    if not matches:
        return

    with engine.connect() as conn:
        for m in matches:
            if not m.get("isResult"): continue
            
            match_id = str(m.get("id"))
            h_team = m.get("h",{}).get("title")
            a_team = m.get("a",{}).get("title")
            
            # 2. ENTRA NELLA SINGOLA PARTITA (È qui che passiamo le ore)
            logging.info(f"   ⚽ Estrazione Match ID {match_id}: {h_team} vs {a_team}...")
            match_players = await safe_fetch(understat.get_match_players, match_id)
            
            if match_players:
                # Understat restituisce 'h' (home) e 'a' (away) con i dizionari dei giocatori
                for side in ['h', 'a']:
                    for p_id, p_data in match_players.get(side, {}).items():
                        query = text("""
                            INSERT INTO premier_match_players 
                            (match_id, player_id, player_name, team_name, season, position, time, goals, assists, shots, key_passes, xg, xa, npxg, xgchain, xgbuildup)
                            VALUES 
                            (:m_id, :p_id, :name, :team, :sea, :pos, :time, :g, :a, :shots, :kp, :xg, :xa, :npxg, :xgchain, :xgbuildup)
                            ON CONFLICT (match_id, player_id) DO NOTHING;
                        """)
                        try:
                            conn.execute(query, {
                                "m_id": match_id, "p_id": p_id, "name": p_data.get("player"),
                                "team": h_team if side == 'h' else a_team, "sea": str(season),
                                "pos": p_data.get("position"), "time": int(p_data.get("time", 0)),
                                "g": int(p_data.get("goals", 0)), "a": int(p_data.get("assists", 0)),
                                "shots": int(p_data.get("shots", 0)), "kp": int(p_data.get("key_passes", 0)),
                                "xg": float(p_data.get("xG", 0.0)), "xa": float(p_data.get("xA", 0.0)),
                                "npxg": float(p_data.get("npxG", 0.0)),
                                "xgchain": float(p_data.get("xGChain", 0.0)), "xgbuildup": float(p_data.get("xGBuildup", 0.0))
                            })
                        except Exception: pass
                conn.commit()

async def main():
    initialize_database()
    connector = aiohttp.TCPConnector(family=socket.AF_INET, ssl=False, force_close=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        for season in SEASONS:
            await process_season(session, season)
    logging.info("\n🎯 ESTRAZIONE LENTA (PARTITA PER PARTITA) COMPLETATA.")

if __name__ == "__main__":
    asyncio.run(main())