#!/usr/bin/env python3
"""
Truncate matches and shots tables.
"""
import asyncio
import asyncpg

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/xpalermostat_db"

async def truncate_tables():
    # Parse URL for asyncpg
    # asyncpg expects postgresql://user:password@host:port/database
    # our URL uses postgresql+asyncpg, remove the +asyncpg
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/xpalermostat_db")
    try:
        # Truncate matches and shots (CASCADE to handle foreign keys)
        await conn.execute("TRUNCATE TABLE matches, shots CASCADE;")
        print("Tables matches and shots truncated successfully.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(truncate_tables())