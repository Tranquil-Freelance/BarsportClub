import asyncio
from sqlalchemy import text
from app.db.database import engine
from app.db.models import Base

async def force_fix():
    print("🔨 Martello del Database: Inizio forzatura...")
    
    async with engine.begin() as conn:
        # 1. Creazione tabelle mancanti
        print("⏳ Creazione tabelle da models.py...")
        await conn.run_sync(Base.metadata.create_all)
        
        # 2. Verifica reale
        print("🔍 Verifica fisica delle tabelle esistenti nel database...")
        result = await conn.execute(text(
            "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public';"
        ))
        tables = [row[0] for row in result.fetchall()]
        
        print("\n📊 TABELLE TROVATE FISICAMENTE:")
        for t in tables:
            print(f" - {t}")
            
        if "player_stats" in tables:
            print("\n✅ TABELLA 'player_stats' RILEVATA! Adesso è sicuro procedere.")
        else:
            print("\n❌ ERRORE CRITICO: La tabella 'player_stats' non è stata creata.")
            print("Controlla di aver salvato models.py con la classe PlayerStat dentro!")

if __name__ == "__main__":
    asyncio.run(force_fix())