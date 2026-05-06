import json
import logging
import logging.handlers
import os
import random
import time
from datetime import datetime, timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import text

from prova2 import (
    DB_URI,
    HIBERNATION_PERIOD,
    JITTER_MIN,
    JITTER_MAX,
    SEASON,
    TARGET_LEAGUES,
    engine,
    make_page,
    scrape_single_match,
)

MATCH_DURATION_MINUTES = 105   # 90 min partita + 15 min recupero medio
SCRAPE_DELAY_MINUTES = 10      # attesa dopo fine prevista prima del 1° tentativo
MAX_ATTEMPTS = 3
RETRY_INTERVAL_MINUTES = 10
LOG_PATH = "/var/log/barsport/scheduler.log"


def setup_logging():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        LOG_PATH, maxBytes=10 * 1024 * 1024, backupCount=3
    )
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=[handler, logging.StreamHandler()],
    )


scheduler = BlockingScheduler(timezone="UTC")


def poll_understat():
    """
    Job fisso ogni 15 minuti.
    Controlla tutte le leghe su understat, trova partite con isResult=True
    non ancora scrapat e le schedula.
    """
    logging.info("=== POLL understat avviato ===")
    page = make_page()
    try:
        for league in TARGET_LEAGUES:
            try:
                time.sleep(random.uniform(JITTER_MIN, JITTER_MAX))
                url = f"https://understat.com/league/{league}/{SEASON}"
                page.get(url)

                if "too many requests" in page.html.lower() or "429 Too Many Requests" in page.html:
                    logging.warning(f"{league}: BAN rilevato, attendo 30 min.")
                    time.sleep(HIBERNATION_PERIOD)
                    page.get(url)

                page.scroll.down(1000)
                time.sleep(2)

                raw = page.run_js("""
                    if(typeof window.datesData !== 'undefined'){
                        return JSON.stringify(window.datesData);
                    }
                    return null;
                """)

                if not raw:
                    logging.warning(f"{league}: datesData non trovato, skip.")
                    continue

                dates_list = json.loads(raw)
                played = [m for m in dates_list if m.get('isResult') is True]

                with engine.connect() as conn:
                    for m in played:
                        m_id = int(m['id'])
                        row = conn.execute(
                            text("SELECT is_scraped FROM matchcalendar WHERE id = :id"),
                            {"id": m_id},
                        ).fetchone()

                        if row and row[0]:
                            continue

                        kickoff_str = m.get('datetime', '')
                        if not kickoff_str:
                            continue

                        kickoff = datetime.strptime(kickoff_str, '%Y-%m-%d %H:%M:%S')
                        expected_end = kickoff + timedelta(minutes=MATCH_DURATION_MINUTES)
                        first_scrape_time = expected_end + timedelta(minutes=SCRAPE_DELAY_MINUTES)

                        now = datetime.utcnow()
                        job_id = f"scrape_{m_id}_1"

                        if scheduler.get_job(job_id):
                            continue

                        if now >= first_scrape_time:
                            logging.info(f"Match {m_id}: in ritardo, scrape immediato.")
                            _schedule_scrape(m_id, 1, run_date=datetime.utcnow() + timedelta(seconds=5))
                        else:
                            logging.info(f"Match {m_id}: scrape schedulato per {first_scrape_time} UTC")
                            _schedule_scrape(m_id, 1, run_date=first_scrape_time)

            except Exception as e:
                logging.error(f"{league}: errore durante il poll: {e}")
                continue
    finally:
        page.quit()
    logging.info("=== POLL understat completato ===")


def _schedule_scrape(match_id: int, attempt: int, run_date: datetime):
    job_id = f"scrape_{match_id}_{attempt}"
    scheduler.add_job(
        scrape_match_with_retry,
        trigger=DateTrigger(run_date=run_date),
        args=[match_id, attempt],
        id=job_id,
        replace_existing=True,
    )


def scrape_match_with_retry(match_id: int, attempt: int):
    """
    Job dinamico. Tenta lo scrape di un singolo match.
    Se i dati non sono ancora disponibili, schedula un retry (max 3 tentativi).
    """
    logging.info(f"Match {match_id}: tentativo {attempt}/{MAX_ATTEMPTS}")
    page = make_page()
    try:
        success = scrape_single_match(page, match_id)
    except Exception as e:
        logging.error(f"Match {match_id}: eccezione durante scrape: {e}")
        success = False
    finally:
        page.quit()

    if not success and attempt < MAX_ATTEMPTS:
        retry_time = datetime.utcnow() + timedelta(minutes=RETRY_INTERVAL_MINUTES)
        logging.info(
            f"Match {match_id}: dati non pronti, retry {attempt + 1} alle {retry_time} UTC"
        )
        _schedule_scrape(match_id, attempt + 1, run_date=retry_time)
    elif not success:
        logging.warning(
            f"Match {match_id}: dati non disponibili dopo {MAX_ATTEMPTS} tentativi. Skip."
        )


if __name__ == "__main__":
    setup_logging()
    logging.info("Barsport Scheduler avviato")

    scheduler.add_job(
        poll_understat,
        trigger=IntervalTrigger(minutes=15),
        id="poll_understat",
        next_run_time=datetime.utcnow(),  # esegui subito al primo avvio
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Scheduler fermato.")
