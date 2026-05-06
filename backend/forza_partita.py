import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import AsyncSessionLocal
from app.scraper.sniper_protocol import sniper_strike

async def main():
    async with AsyncSessionLocal() as session:
        print("🎯 Avvio attacco mirato su Fiorentina - Inter (ID 30138)...")
        await sniper_strike(session, "30138", "Fiorentina vs Inter")
        await session.commit()
        print("✅ Operazione conclusa. Vai a controllare il grafico sul browser!")

if __name__ == "__main__":
    asyncio.run(main())