"""
🚀 TRIVELLA DI PRECISIONE: BUNDESLIGA 2024-2025
Versione STABILE (gestisce tutti i formati Understat)
"""

import asyncio
import aiohttp
import random
import logging
import socket
from understat import Understat
from sqlalchemy import create_engine, text
import sys

# ─── LOG ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# ─── DATABASE ───────────────────────────────────────
DB_URL = "postgresql://postgres:password@localhost:5432/xpalermostat"
engine = create_engine(DB_URL)

LEAGUE = "Bundesliga"
SEASONS = [2024, 2025]

# ─── ANTI-BAN ───────────────────────────────────────
async def apply_jitter():
    await asyncio.sleep(random.uniform(2.5, 5.0))

async def trigger_hibernation():
    logging.warning("🔴 BAN DETECTED → pausa 30 min")
    await asyncio.sleep(1800)

async def safe_fetch(method, *args):
    retries = 0
    while retries < 5:
        try:
            await apply_jitter()
            return await method(*args)
        except aiohttp.ClientResponseError as e:
            if e.status == 429:
                await trigger_hibernation()
                retries += 1
            else:
                logging.error(f"Errore HTTP {e.status}")
                retries += 1
                await asyncio.sleep(10)
        except Exception as e:
            logging.error(f"Errore: {e}")
            retries += 1
            await asyncio.sleep(10)
    return None

# ─── CORE ───────────────────────────────────────────
async def process_season(session, season):
    understat = Understat(session)

    logging.info(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logging.info(f"🇩🇪 BUNDESLIGA {season}")

    matches = await safe_fetch(understat.get_league_results, LEAGUE, season)

    if not matches:
        logging.error(f"❌ Nessuna partita trovata per {season}")
        return

    print(f"DEBUG: stagione {season}, partite ricevute: {len(matches)}")

    with engine.connect() as conn:
        for idx, m in enumerate(matches, 1):
            match_id = str(m.get("id"))
            h_team = m.get("h", {}).get("title")
            a_team = m.get("a", {}).get("title")

            logging.info(f"[{idx}/{len(matches)}] {h_team} vs {a_team}")

            match_players = await safe_fetch(understat.get_match_players, match_id)

            if not match_players:
                continue

            for side in ['h', 'a']:
                current_team = h_team if side == 'h' else a_team

                raw_players = match_players.get(side, [])

                # 🧠 FIX UNIVERSALE: gestisce dict o list
                if isinstance(raw_players, dict):
                    players = raw_players.values()
                else:
                    players = raw_players

                for p_data in players:
                    # 🛡️ PROTEZIONE DATI SPORCHI
                    if not isinstance(p_data, dict):
                        continue

                    p_id = p_data.get("id")

                    query = text("""
                        INSERT INTO bundesliga_match_players 
                        (match_id, player_id, player_name, team_name, season, position, time, goals, assists, shots, key_passes, xg, xa, npxg, xgchain, xgbuildup)
                        VALUES 
                        (:m_id, :p_id, :name, :team, :sea, :pos, :time, :g, :a, :shots, :kp, :xg, :xa, :npxg, :xgchain, :xgbuildup)
                        ON CONFLICT (match_id, player_id) DO NOTHING;
                    """)

                    try:
                        conn.execute(query, {
                            "m_id": match_id,
                            "p_id": p_id,
                            "name": p_data.get("player"),
                            "team": current_team,
                            "sea": str(season),
                            "pos": p_data.get("position"),
                            "time": int(p_data.get("time", 0)),
                            "g": int(p_data.get("goals", 0)),
                            "a": int(p_data.get("assists", 0)),
                            "shots": int(p_data.get("shots", 0)),
                            "kp": int(p_data.get("key_passes", 0)),
                            "xg": float(p_data.get("xG", 0.0)),
                            "xa": float(p_data.get("xA", 0.0)),
                            "npxg": float(p_data.get("npxG", 0.0)),
                            "xgchain": float(p_data.get("xGChain", 0.0)),
                            "xgbuildup": float(p_data.get("xGBuildup", 0.0))
                        })
                    except Exception:
                        pass

            conn.commit()

# ─── MAIN ───────────────────────────────────────────
async def main():
    connector = aiohttp.TCPConnector(family=socket.AF_INET, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        for season in SEASONS:
            await process_season(session, season)

    logging.info("\n🎯 COMPLETATO: Bundesliga aggiornata")

if __name__ == "__main__":
    asyncio.run(main())