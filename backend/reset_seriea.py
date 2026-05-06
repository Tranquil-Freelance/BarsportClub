import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def clean():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/xpalermostat')
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM matchcalendar WHERE league_id = 1"))
        print("✅ SERIE A PULITA!")

if __name__ == "__main__":
    asyncio.run(clean())