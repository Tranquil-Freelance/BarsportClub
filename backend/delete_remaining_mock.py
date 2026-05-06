#!/usr/bin/env python3
"""
Delete remaining mock rows from team_season_stat where season = '2025/26' and team_id not in real IDs.
"""
import asyncio
import sys
sys.path.append('.')
from sqlalchemy import text
from app.db.database import engine

REAL_TEAM_IDS = [94, 95, 96, 97, 98, 99, 101, 104, 105, 106, 107, 110, 111, 113, 116, 230, 243, 272, 286, 291]

async def delete_mock():
    async with engine.connect() as conn:
        # Build placeholder string
        ids_tuple = tuple(REAL_TEAM_IDS)
        # First count
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM team_season_stat 
            WHERE season = '2025/26' AND team_id NOT IN :ids
        """), {'ids': ids_tuple})
        count = result.scalar()
        print(f"Found {count} remaining mock rows to delete.")
        if count > 0:
            await conn.execute(text("""
                DELETE FROM team_season_stat 
                WHERE season = '2025/26' AND team_id NOT IN :ids
            """), {'ids': ids_tuple})
            await conn.commit()
            print("Remaining mock rows deleted.")
        else:
            print("No remaining mock rows.")
    await engine.dispose()

asyncio.run(delete_mock())