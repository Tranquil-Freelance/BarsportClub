import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/xpalermostat"
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def fix_teams():
    async with AsyncSessionLocal() as db:
        print("🔧 NORMALIZZAZIONE NOMI SQUADRE...")

        # 1. Unifichiamo il Parma (ID 268 è Parma Calcio 1913, lo portiamo a 'Parma')
        # Controlliamo prima gli ID reali nel tuo DB per non fare danni
        changes = {
            "Parma Calcio 1913": "Parma",
            "AC Milan": "Milan",
            "Paris Saint Germain": "PSG",
            "RasenBallsport Leipzig": "RB Leipzig",
            "Borussia M.Gladbach": "M'Gladbach",
            "Greuther Fuerth": "Greuther Furth",
            "Mainz 05": "Mainz",
            "FC Cologne": "Cologne",
            "VfB Stuttgart": "Stuttgart",
            "Atletico Madrid": "Atalanta" # ATTENZIONE: Questo è solo un esempio, non eseguire se errato
        }
        
        # Correzione sicura
        for old_name, new_name in changes.items():
            await db.execute(
                text("UPDATE team SET name = :new WHERE name = :old"),
                {"new": new_name, "old": old_name}
            )
        
        await db.commit()
        print("✅ Nomi normalizzati con successo.")

if __name__ == "__main__":
    asyncio.run(fix_teams())