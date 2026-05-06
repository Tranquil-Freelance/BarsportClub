import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DB_URL = "postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat"

async def tabula_rasa():
    engine = create_async_engine(DB_URL)
    async with engine.begin() as conn:
        print("🔨 Distruzione vincoli in corso...")
        # Eliminiamo tutti i possibili nomi che abbiamo dato a quel vincolo
        await conn.execute(text("ALTER TABLE shots DROP CONSTRAINT IF EXISTS uq_shot_unique CASCADE;"))
        await conn.execute(text("ALTER TABLE shots DROP CONSTRAINT IF EXISTS uq_shot_atomic CASCADE;"))
        await conn.execute(text("ALTER TABLE shots DROP CONSTRAINT IF EXISTS uq_player_stat_unique CASCADE;"))
        print("✅ Database ripulito. Ora è un campo libero.")

if __name__ == "__main__":
    asyncio.run(tabula_rasa())