import asyncio
from sqlalchemy import text
from app.db.database import AsyncSessionLocal

async def find_id():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT id, home_team, away_team FROM matches LIMIT 1"))
        match = res.fetchone()
        if match:
            print(f"[OK] ID VALIDO TROVATO: {match[0]} ({match[1]} vs {match[2]})")
        else:
            print("[ERROR] Nessuna partita trovata nel database")

asyncio.run(find_id())