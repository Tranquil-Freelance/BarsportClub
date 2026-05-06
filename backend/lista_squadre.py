import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/xpalermostat"
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def check_teams():
    async with AsyncSessionLocal() as db:
        print("\n🔍 ELENCO SQUADRE NEL DATABASE (Per controllo icone):")
        print("-" * 40)
        res = await db.execute(text("SELECT DISTINCT name FROM team ORDER BY name ASC"))
        teams = res.fetchall()
        for t in teams:
            print(f"📍 {t[0]}")
        print("-" * 40)
        print(f"Totale squadre censite: {len(teams)}")

if __name__ == "__main__":
    asyncio.run(check_teams())