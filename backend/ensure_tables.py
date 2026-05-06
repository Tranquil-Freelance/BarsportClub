import asyncio
import sys
sys.path.insert(0, '.')

from app.db.database import engine, Base
from app.db.models import Article, Match, Shot

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully.")
    # list tables
    async with engine.connect() as conn:
        result = await conn.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' ORDER BY table_name
        """)
        tables = await result.fetchall()
        print("Tables in database:")
        for row in tables:
            print(f" - {row.table_name}")

if __name__ == "__main__":
    asyncio.run(create_tables())