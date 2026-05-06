import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DB_URL = "postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat"

async def fix():
    engine = create_async_engine(DB_URL)
    async with engine.begin() as conn:
        # Eliminiamo il vincolo che causa il blocco
        print("🔨 Rimozione vincoli duplicati obsoleti...")
        await conn.execute(text("ALTER TABLE shots DROP CONSTRAINT IF EXISTS uq_shot_unique;"))
        await conn.execute(text("ALTER TABLE shots DROP CONSTRAINT IF EXISTS uq_shot_atomic;"))
        print("✅ Vincoli rimossi. Ora il database accetta anche 10 tiri nello stesso minuto.")

if __name__ == "__main__":
    asyncio.run(fix())