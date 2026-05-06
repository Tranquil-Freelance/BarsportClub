import sys
sys.path.insert(0, 'backend')
from app.db.database import engine
from sqlalchemy import inspect

async def list_tables():
    async with engine.connect() as conn:
        inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
        tables = inspector.get_table_names()
        print("Tables:", tables)

import asyncio
asyncio.run(list_tables())