import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("DB_Evolution")

DB_URL_ASYNC = "postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat"

async def evolve_database():
    engine = create_async_engine(DB_URL_ASYNC, isolation_level="AUTOCOMMIT")
    logger.info("Inizio evoluzione: da Vista Materializzata a Tabella Reale...")
    
    async with engine.connect() as conn:
        try:
            logger.info("1. Rinomino la vecchia vista...")
            await conn.execute(text("ALTER MATERIALIZED VIEW IF EXISTS master_europe_players RENAME TO master_europe_players_old;"))
            
            logger.info("2. Creo la nuova tabella fisica estraendo dati univoci...")
            await conn.execute(text("""
                CREATE TABLE master_europe_players AS 
                SELECT DISTINCT ON (player_id, match_id) * FROM master_europe_players_old;
            """))
            
            logger.info("3. Applico il vincolo UNIQUE...")
            await conn.execute(text("""
                ALTER TABLE master_europe_players 
                ADD CONSTRAINT unique_player_match UNIQUE (player_id, match_id);
            """))
            
            logger.info("4. Elimino la vecchia vista...")
            await conn.execute(text("DROP MATERIALIZED VIEW master_europe_players_old;"))
            
            logger.info("✅ EVOLUZIONE COMPLETATA.")
            
        except Exception as e:
            logger.error(f"Errore durante l'evoluzione: {e}")
            # Tentativo di rollback: ripristina la vista originale se possibile
            logger.warning("Tentativo di ripristino della vista originale...")
            try:
                await conn.execute(text("DROP TABLE IF EXISTS master_europe_players;"))
                await conn.execute(text("ALTER MATERIALIZED VIEW IF EXISTS master_europe_players_old RENAME TO master_europe_players;"))
                logger.info("Ripristino effettuato.")
            except Exception as rollback_err:
                logger.error(f"Errore nel ripristino: {rollback_err}")
            raise

if __name__ == "__main__":
    asyncio.run(evolve_database())