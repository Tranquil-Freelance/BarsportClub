import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("DB_Check")

DB_URL_ASYNC = "postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat"

async def check_master_europe_players():
    engine = create_async_engine(DB_URL_ASYNC, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        # Controlla se è una vista materializzata
        result = await conn.execute(text("""
            SELECT schemaname, matviewname AS objectname, 'materialized view' AS objecttype
            FROM pg_catalog.pg_matviews
            WHERE schemaname = 'public' AND matviewname = 'master_europe_players'
            UNION ALL
            SELECT schemaname, tablename AS objectname, 'table' AS objecttype
            FROM pg_catalog.pg_tables
            WHERE schemaname = 'public' AND tablename = 'master_europe_players'
        """))
        row = result.fetchone()
        if row:
            logger.info(f"Trovato: {row.objectname} ({row.objecttype})")
        else:
            logger.info("Nessuna tabella o vista materializzata con nome master_europe_players.")
        
        # Conta le righe
        result = await conn.execute(text("SELECT COUNT(*) FROM master_europe_players"))
        count = result.scalar()
        logger.info(f"Numero di righe: {count}")

if __name__ == "__main__":
    asyncio.run(check_master_europe_players())