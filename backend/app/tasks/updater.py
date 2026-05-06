import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.db.database import get_db
from app.db.models import Match

# Configurazione Log maniacale
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("xComoStat-Updater")

# Creiamo lo scheduler globale
scheduler = AsyncIOScheduler(timezone="Europe/Rome")

async def run_weekly_update():
    """
    Task di aggiornamento automatico.
    Gira ogni lunedì alle 03:00.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"--- [START] Task di aggiornamento automatico alle {now} ---")
    
    try:
        async for db in get_db():
            stmt = select(Match).order_by(Match.id.desc()).limit(1)
            result = await db.execute(stmt)
            last_match = result.scalar_one_or_none()
            
            if last_match:
                logger.info(f"[Updater] Verifica DB: Ultimo match trovato -> {last_match.home_team} vs {last_match.away_team}")
            else:
                logger.warning("[Updater] Nessun match trovato nel database durante l'aggiornamento.")
            
            break
                
        logger.info(f"--- [SUCCESS] Aggiornamento completato alle {now} ---")
        
    except Exception as e:
        logger.error(f"--- [ERROR] Fallimento aggiornamento: {str(e)} ---")

def start_scheduler():
    """Avvia lo scheduler se non è già attivo."""
    if not scheduler.running:
        # IMPOSTAZIONE PRODUZIONE: Ogni lunedì alle 03:00
        scheduler.add_job(
            run_weekly_update,
            CronTrigger(day_of_week='mon', hour=3, minute=0),
            id="weekly_match_update",
            replace_existing=True
        )
        scheduler.start()
        logger.info("[Updater] Scheduler avviato con successo (Cron: Lunedì 03:00).")

def shutdown_scheduler():
    """Spegne lo scheduler in modo pulito."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("[Updater] Scheduler spento correttamente.")

def get_scheduler():
    """Restituisce l'istanza dello scheduler."""
    return scheduler