import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv('../.env')

async def main():
    conn = await asyncpg.connect(
        host=os.getenv('POSTGRES_SERVER', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'your_secure_password'),
        database=os.getenv('POSTGRES_DB', 'xpalermostat')
    )
    # list tables in public schema
    rows = await conn.fetch("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' ORDER BY table_name
    """)
    print("Tables in database:")
    for row in rows:
        print(f" - {row['table_name']}")
    await conn.close()

asyncio.run(main())