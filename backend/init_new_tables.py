import asyncio
from app.db.database import engine
from app.db.models import Base

async def init_tables():
    print("🔧 INIZIO: Allineamento del database in corso...")
    async with engine.begin() as conn:
        # Questo comando ordina a PostgreSQL di leggere models.py e creare le tabelle che non esistono ancora
        await conn.run_sync(Base.metadata.create_all)
    print("✅ SUCCESSO: Tabelle PlayerStat e TeamStat create fisicamente e pronte all'uso.")

if __name__ == "__main__":
    asyncio.run(init_tables())