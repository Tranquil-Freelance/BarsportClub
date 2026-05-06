import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# URL del tuo database
DB_URL = "postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat"

async def patch_database():
    engine = create_async_engine(DB_URL)
    async with engine.begin() as conn:
        print("🛠️  Inizio chirurgia correttiva sulla tabella 'shots'...")
        
        # Aggiungiamo le colonne mancanti una per una
        # Usiamo IF NOT EXISTS per sicurezza
        commands = [
            "ALTER TABLE shots ADD COLUMN IF NOT EXISTS player_id BIGINT;",
            "ALTER TABLE shots ADD COLUMN IF NOT EXISTS situation VARCHAR;",
            'ALTER TABLE shots ADD COLUMN IF NOT EXISTS "shotType" VARCHAR;',
            'ALTER TABLE shots ADD COLUMN IF NOT EXISTS "lastAction" VARCHAR;',
            "ALTER TABLE shots ADD COLUMN IF NOT EXISTS assist VARCHAR;"
        ]
        
        for cmd in commands:
            try:
                await conn.execute(text(cmd))
                print(f"✅ Eseguito: {cmd}")
            except Exception as e:
                print(f"⚠️  Nota su {cmd[:20]}... : {e}")

        print("\n🚀 Database allineato al modello 'Aspiratutto'!")

if __name__ == "__main__":
    asyncio.run(patch_database())