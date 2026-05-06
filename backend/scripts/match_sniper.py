import asyncio
import aiohttp
import logging
import random
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from understat import Understat

# ─── CONFIGURAZIONE ───────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s - 🎯 SNIPER - %(message)s")
logger = logging.getLogger("MatchSniper")

DB_URL_ASYNC = "postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat"
engine = create_async_engine(DB_URL_ASYNC, pool_pre_ping=True)

LEAGUES = ['EPL', 'La_liga', 'Bundesliga', 'Serie_A', 'Ligue_1']
SEASON = "2025"

scheduler = AsyncIOScheduler()

# ─── LIVELLI DI ANTI-BAN (PROTOCOLLO MEMORIZZATO) ─────────────────────────────
async def apply_jitter():
    jitter = random.uniform(4.0, 9.0)
    logger.info(f"⏳ Livello 1: Jitter base. Attesa di {jitter:.2f} secondi.")
    await asyncio.sleep(jitter)

async def hibernate(target_name: str):
    logger.warning(f"🚨 Livello 2: Rate Limit Recovery. Ibernazione di 30 minuti attivata per {target_name}.")
    await asyncio.sleep(1800)
    logger.info("🟢 Ibernazione terminata. Ripresa operazioni.")


# ─── LOGICA DATABASE (UPSERT MANIACALE) ───────────────────────────────────────
async def save_match_data(match_id: str, match_data: dict):
    async with engine.begin() as conn:
        for team_type in ['h', 'a']:
            for player_id, p_data in match_data.get(team_type, {}).items():
                
                query = text("""
                    INSERT INTO master_europe_players (
                        player_id, match_id, player_name, team_name, season, position, 
                        goals, shots, xg, xa, xgchain, xgbuildup, time
                    ) VALUES (
                        :p_id, :m_id, :p_name, :t_name, :season, :pos, 
                        :goals, :shots, :xg, :xa, :xgchain, :xgbuildup, :time
                    )
                    ON CONFLICT (player_id, match_id) DO NOTHING;
                """)
                
                try:
                    await conn.execute(query, {
                        "p_id": p_data.get('player_id'),
                        "m_id": match_id,
                        "p_name": p_data.get('player'),
                        "t_name": p_data.get('team_id'), 
                        "season": SEASON,
                        "pos": p_data.get('position'),
                        "goals": int(p_data.get('goals', 0)),
                        "shots": int(p_data.get('shots', 0)),
                        "xg": float(p_data.get('xG', 0)),
                        "xa": float(p_data.get('xA', 0)),
                        "xgchain": float(p_data.get('xGChain', 0)),
                        "xgbuildup": float(p_data.get('xGBuildup', 0)),
                        "time": int(p_data.get('time', 0))
                    })
                except Exception as e:
                    logger.error(f"Errore DB per {p_data.get('player')}: {e}")
                    pass


# ─── IL CECCHINO: ESTRAZIONE SINGOLA PARTITA CON UNDERSTAT ────────────────────
async def sniper_strike(match_id: str, title: str):
    logger.info(f"Inizio operazione su: {title} (ID: {match_id})")
    
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        
        await apply_jitter()
        try:
            match_data = await understat.get_match_players(match_id)
            
            if not match_data:
                logger.info(f"Dati non ancora disponibili per {title}. Riprovo tra 10 minuti.")
                trigger_time = datetime.now() + timedelta(minutes=10)
                scheduler.add_job(sniper_strike, 'date', run_date=trigger_time, args=[match_id, title])
                return
            
            await save_match_data(match_id, match_data)
            logger.info(f"✅ Dati estratti e salvati con successo per: {title}")
            
        except aiohttp.ClientResponseError as e:
            if e.status in [403, 429]:
                await hibernate(title)
                trigger_time = datetime.now() + timedelta(seconds=10)
                scheduler.add_job(sniper_strike, 'date', run_date=trigger_time, args=[match_id, title])
            else:
                logger.error(f"Errore HTTP su {title}: {e}")
        except Exception as e:
            logger.error(f"Errore generico durante lo strike su {title}: {e}")
            trigger_time = datetime.now() + timedelta(minutes=10)
            scheduler.add_job(sniper_strike, 'date', run_date=trigger_time, args=[match_id, title])


# ─── IL SINCRONIZZATORE: PIANIFICAZIONE CALENDARIO CON UNDERSTAT ──────────────
async def sync_daily_calendar():
    logger.info("Sincronizzazione calendario in corso con libreria Understat...")
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    matches_scheduled = 0

    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        
        for league in LEAGUES:
            await apply_jitter()
            
            try:
                results = await understat.get_league_results(league, SEASON)
                fixtures = await understat.get_league_fixtures(league, SEASON)
                all_matches = results + fixtures
                
                for m in all_matches:
                    match_time_str = m.get('datetime')
                    
                    if match_time_str and (match_time_str.startswith(today_str) or match_time_str.startswith(yesterday_str)):
                        match_id = m.get('id')
                        title = f"{m.get('h', {}).get('title')} vs {m.get('a', {}).get('title')}"
                        
                        if m.get('isResult') == True or m in results:
                            logger.info(f"Recupero partita finita: {title}")
                            asyncio.create_task(sniper_strike(match_id, title))
                            continue
                            
                        if match_time_str.startswith(today_str):
                            start_time = datetime.strptime(match_time_str, "%Y-%m-%d %H:%M:%S")
                            trigger_time = start_time + timedelta(minutes=130)
                            
                            if trigger_time > datetime.now():
                                scheduler.add_job(sniper_strike, 'date', run_date=trigger_time, args=[match_id, title])
                                logger.info(f"Schedulato: {title} alle {trigger_time.strftime('%H:%M:%S')}")
                                matches_scheduled += 1

            except aiohttp.ClientResponseError as e:
                if e.status in [403, 429]:
                    await hibernate(f"Calendario {league}")
                else:
                    logger.error(f"Errore HTTP calendario {league}: {e}")
            except Exception as e:
                logger.error(f"Errore lettura calendario {league}: {e}")
                
    logger.info(f"Sincronizzazione completata. {matches_scheduled} partite future schedulate.")


# ─── AVVIO DEL DEMONE ─────────────────────────────────────────────────────────
async def main():
    logger.info("Avvio Demone Scout Sniper (Powered by Understat Library)...")
    scheduler.start()
    
    await sync_daily_calendar()
    
    scheduler.add_job(sync_daily_calendar, 'cron', hour=0, minute=5)
    
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Cecchino disattivato manualmente.")

if __name__ == "__main__":
    asyncio.run(main())