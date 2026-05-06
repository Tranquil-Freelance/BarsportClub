import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/xpalermostat"

async def fix_my_mistake():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        print("\n🔧 RIPARAZIONE NOMI SQUADRE IN CORSO...")
        
        # Ripristiniamo l'Atletico Madrid cercando chi gioca nella Liga (league_id = 3)
        query = text("""
            UPDATE team 
            SET name = 'Atletico Madrid' 
            WHERE name = 'Atalanta' 
            AND id IN (
                SELECT DISTINCT home_team_id 
                FROM matchcalendar 
                WHERE league_id = 3
            )
        """)
        await conn.execute(query)
        print("✅ Danno riparato! L'Atletico Madrid è tornato a Madrid e l'Atalanta a Bergamo.")

if __name__ == "__main__":
    asyncio.run(fix_my_mistake())