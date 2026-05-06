"""
Background Task Scheduler — Phase 9
=====================================
Integrates APScheduler directly into the FastAPI application lifecycle
to automate two critical operations:

1. **Daily Settlement** (02:00 AM)
   Fetches matches completed in the last 48 hours, retrieves actual scores,
   and calls :func:`settle_match_bets` for each match with at least one OPEN bet.

2. **Weekly ML Retraining** (Monday 04:00 AM)
   Runs the training pipeline defined in ``scripts/train_ai_model.py`` to keep
   the AI correction model current.

All jobs use the shared :data:`app.db.database.engine` for database access and
log through the standard ``logging`` facility.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import text

from app.db.database import engine
from app.services.settlement_service import settle_match_bets

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger("barsport.scheduler")

# ---------------------------------------------------------------------------
# Scheduler instance
# ---------------------------------------------------------------------------

scheduler = AsyncIOScheduler(timezone="Europe/Rome")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DAILY_SETTLEMENT_HOUR = 2
DAILY_SETTLEMENT_MINUTE = 0

WEEKLY_RETRAIN_DAY = "mon"
WEEKLY_RETRAIN_HOUR = 4
WEEKLY_RETRAIN_MINUTE = 0

# ── Phase 10: Data Ingestion ──────────────────────────────────────────────

DATA_INGESTION_INTERVAL_HOURS = 6
"""Run the Understat scraper every 6 hours."""

DATA_INGESTION_TIMEOUT = 3600
"""Max wall-clock time (seconds) allowed for a single scraper run."""

MATCH_LOOKBACK_HOURS = 48
"""How far back in time to look for completed matches that need settlement."""

# ---------------------------------------------------------------------------
# Task 1 — Daily Settlement
# ---------------------------------------------------------------------------


async def daily_settlement() -> None:
    """
    Background job that runs every night at 02:00 AM.

    Workflow
    --------
    1. Query all matches completed in the last ``MATCH_LOOKBACK_HOURS`` hours
       that have actual scores (``home_goals`` and ``away_goals`` are not NULL).
    2. For each such match, query whether any bets exist with ``status = 'OPEN'``.
    3. If open bets exist, call :func:`settle_match_bets` with the actual score.
    4. Log a summary of how many matches and bets were settled.
    """
    logger.info(
        "[DailySettlement] Starting — looking back %d hours",
        MATCH_LOOKBACK_HOURS,
    )

    cutoff = datetime.now(timezone.utc) - timedelta(hours=MATCH_LOOKBACK_HOURS)
    settled_count = 0
    match_count = 0

    try:
        async with engine.connect() as conn:
            # ── 1. Fetch completed matches with actual scores ──────────────
            #     AND that have at least one OPEN bet (i.e. not yet settled).
            matches_sql = text("""
                SELECT DISTINCT m.id, m.home_goals, m.away_goals
                FROM matchcalendar m
                INNER JOIN bets b ON b.match_id = m.id
                WHERE
                    m.is_completed = TRUE
                    AND m.home_goals IS NOT NULL
                    AND m.away_goals IS NOT NULL
                    AND m.match_datetime >= :cutoff
                    AND b.status = 'OPEN'
                ORDER BY m.id ASC
            """)

            rows = (await conn.execute(matches_sql, {"cutoff": cutoff})).fetchall()

            if not rows:
                logger.info("[DailySettlement] No matches requiring settlement found.")
                return

            logger.info(
                "[DailySettlement] Found %d match(es) with open bets to settle.",
                len(rows),
            )

            # ── 2. Settle each match ─────────────────────────────────────
            for row in rows:
                match_id: int = row[0]
                home_goals: int = row[1]
                away_goals: int = row[2]

                try:
                    # settle_match_bets expects an AsyncSession; we open one
                    # via the engine's Session class.
                    from sqlalchemy.ext.asyncio import AsyncSession
                    from sqlalchemy.orm import sessionmaker

                    async_session_factory = sessionmaker(
                        engine,
                        class_=AsyncSession,
                        expire_on_commit=False,
                    )

                    async with async_session_factory() as session:
                        n = await settle_match_bets(
                            session=session,
                            match_id=match_id,
                            home_goals=home_goals,
                            away_goals=away_goals,
                        )
                        settled_count += n
                        match_count += 1

                        logger.info(
                            "[DailySettlement] Match %d (%d–%d): settled %d bet(s).",
                            match_id,
                            home_goals,
                            away_goals,
                            n,
                        )

                except Exception as exc:
                    logger.exception(
                        "[DailySettlement] Failed to settle match_id=%s: %s",
                        match_id,
                        exc,
                    )
                    # Continue with next match — don't let one failure block
                    # the entire settlement run.

    except Exception as exc:
        logger.exception(
            "[DailySettlement] Fatal error during settlement cycle: %s",
            exc,
        )
        return

    logger.info(
        "[DailySettlement] Complete — %d match(es) processed, %d bet(s) settled.",
        match_count,
        settled_count,
    )


# ---------------------------------------------------------------------------
# Task 2 — Weekly ML Retraining
# ---------------------------------------------------------------------------


async def weekly_ml_retrain() -> None:
    """
    Background job that runs every Monday at 04:00 AM.

    Executes the ``train_ai_model.py`` script as a subprocess so that the
    training pipeline runs in an isolated Python process with its own memory
    space (preventing any interference with the live API server).

    The subprocess inherits the same environment variables and Python
    interpreter from the parent process.
    """
    logger.info("[WeeklyML] Starting ML retraining pipeline...")

    # Resolve path to train_ai_model.py relative to this file.
    # backend/app/core/scheduler.py → backend/scripts/train_ai_model.py
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    script_path = os.path.join(script_dir, "scripts", "train_ai_model.py")

    if not os.path.isfile(script_path):
        logger.error(
            "[WeeklyML] train_ai_model.py not found at %s. Aborting.",
            script_path,
        )
        return

    python_exe = sys.executable

    try:
        # Run as subprocess and capture output for logging.
        process = await asyncio_subprocess_run(
            [python_exe, script_path],
            cwd=script_dir,
            timeout=600,  # 10 minute timeout — training should not exceed this.
        )

        stdout = process.stdout or ""
        stderr = process.stderr or ""

        if process.returncode == 0:
            logger.info(
                "[WeeklyML] Training completed successfully (exit code 0)."
            )
            # Log the last few lines of stdout for visibility.
            for line in stdout.strip().splitlines()[-5:]:
                logger.info("[WeeklyML] %s", line.strip())
        else:
            logger.error(
                "[WeeklyML] Training failed with exit code %d.",
                process.returncode,
            )
            for line in stderr.strip().splitlines()[-10:]:
                logger.error("[WeeklyML] %s", line.strip())

    except TimeoutError:
        logger.error("[WeeklyML] Training process timed out after 600 seconds.")
    except Exception as exc:
        logger.exception("[WeeklyML] Unexpected error running training: %s", exc)


# ---------------------------------------------------------------------------
# Task 3 — Data Ingestion (every 6 hours)
# ---------------------------------------------------------------------------


async def data_ingestion() -> None:
    """
    Background job that runs every 6 hours.

    Spawns ``scripts/understat_scraper.py`` as an isolated subprocess so
    that DrissionPage (Chromium browser) does **not** block the FastAPI
    async event loop.  The subprocess inherits environment variables so
    database credentials are automatically available.

    All stdout and stderr are captured and forwarded to the application
    logger, enabling the Risk Manager to monitor scraper health.
    """
    logger.info("[DataIngestion] Starting Understat scraper pipeline...")

    # Resolve path: backend/app/core/scheduler.py → backend/scripts/understat_scraper.py
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    script_path = os.path.join(script_dir, "scripts", "understat_scraper.py")

    if not os.path.isfile(script_path):
        logger.error(
            "[DataIngestion] understat_scraper.py not found at %s. Aborting.",
            script_path,
        )
        return

    python_exe = sys.executable

    try:
        process = await asyncio_subprocess_run(
            [python_exe, script_path],
            cwd=script_dir,
            timeout=DATA_INGESTION_TIMEOUT,
        )

        stdout = process.stdout or ""
        stderr = process.stderr or ""

        if process.returncode == 0:
            logger.info(
                "[DataIngestion] Scraper completed successfully (exit code 0)."
            )
            # Forward the last lines of stdout for visibility.
            for line in stdout.strip().splitlines()[-10:]:
                logger.info("[DataIngestion] %s", line.strip())
        else:
            logger.error(
                "[DataIngestion] Scraper failed with exit code %d.",
                process.returncode,
            )
            for line in stderr.strip().splitlines()[-20:]:
                logger.error("[DataIngestion] %s", line.strip())

    except TimeoutError:
        logger.error(
            "[DataIngestion] Scraper timed out after %d seconds.",
            DATA_INGESTION_TIMEOUT,
        )
    except Exception as exc:
        logger.exception(
            "[DataIngestion] Unexpected error running scraper: %s", exc
        )


async def asyncio_subprocess_run(
    cmd: list[str],
    cwd: str,
    timeout: int,
):
    """
    Run a subprocess asynchronously with timeout.

    This is a small helper that wraps ``asyncio.create_subprocess_exec``
    with a timeout guard, returning an object with ``returncode``,
    ``stdout``, and ``stderr`` attributes.
    """
    import asyncio

    process = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=timeout
        )
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        raise TimeoutError(
            f"Subprocess timed out after {timeout}s: {' '.join(cmd)}"
        )

    # Attach return code and decoded output.
    process.stdout = stdout.decode("utf-8", errors="replace") if stdout else ""
    process.stderr = stderr.decode("utf-8", errors="replace") if stderr else ""
    return process


# ---------------------------------------------------------------------------
# Scheduler lifecycle
# ---------------------------------------------------------------------------


def start_scheduler() -> None:
    """
    Register all background jobs and start the scheduler.

    Safe to call multiple times — subsequent calls are no-ops if the
    scheduler is already running.
    """
    if scheduler.running:
        logger.info("[Scheduler] Already running — skipping start.")
        return

    # ── Task 1: Daily settlement at 02:00 AM Europe/Rome ─────────────────
    scheduler.add_job(
        daily_settlement,
        CronTrigger(
            hour=DAILY_SETTLEMENT_HOUR,
            minute=DAILY_SETTLEMENT_MINUTE,
            timezone="Europe/Rome",
        ),
        id="daily_settlement",
        replace_existing=True,
        name="DailyBetSettlement",
        misfire_grace_time=3600,  # Allow up to 1h delay
    )
    logger.info(
        "[Scheduler] Registered 'daily_settlement' — %02d:%02d daily.",
        DAILY_SETTLEMENT_HOUR,
        DAILY_SETTLEMENT_MINUTE,
    )

    # ── Task 2: Weekly ML retraining on Monday at 04:00 AM ──────────────
    scheduler.add_job(
        weekly_ml_retrain,
        CronTrigger(
            day_of_week=WEEKLY_RETRAIN_DAY,
            hour=WEEKLY_RETRAIN_HOUR,
            minute=WEEKLY_RETRAIN_MINUTE,
            timezone="Europe/Rome",
        ),
        id="weekly_ml_retrain",
        replace_existing=True,
        name="WeeklyMLRetrain",
        misfire_grace_time=7200,  # Allow up to 2h delay
    )
    logger.info(
        "[Scheduler] Registered 'weekly_ml_retrain' — %s %02d:%02d weekly.",
        WEEKLY_RETRAIN_DAY.capitalize(),
        WEEKLY_RETRAIN_HOUR,
        WEEKLY_RETRAIN_MINUTE,
    )

    # ── Task 3: Data ingestion every 6 hours ───────────────────────────
    scheduler.add_job(
        data_ingestion,
        IntervalTrigger(
            hours=DATA_INGESTION_INTERVAL_HOURS,
            timezone="Europe/Rome",
        ),
        id="data_ingestion",
        replace_existing=True,
        name="DataIngestion",
        misfire_grace_time=1800,  # Allow up to 30 min delay
    )
    logger.info(
        "[Scheduler] Registered 'data_ingestion' — every %d hours.",
        DATA_INGESTION_INTERVAL_HOURS,
    )

    scheduler.start()
    logger.info("[Scheduler] Started successfully.")


def stop_scheduler() -> None:
    """
    Shut down the scheduler gracefully.

    Waits for any currently running job to finish (up to the job's own
    timeout) before shutting down.
    """
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("[Scheduler] Shut down gracefully.")
    else:
        logger.info("[Scheduler] Not running — nothing to shut down.")


def get_scheduler() -> AsyncIOScheduler:
    """Return the global scheduler instance (for introspection)."""
    return scheduler
