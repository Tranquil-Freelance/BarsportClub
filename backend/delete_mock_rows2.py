#!/usr/bin/env python3
"""
Delete mock rows from team_season_stat where season = '2025/26' and team_id > 1000.
"""
import asyncio
import sys
sys.path.append('.')
from sqlalchemy import text
from app.db.database import engine

async def delete_mock():
    async with engine.connect() as conn:
        # Count rows
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM team_season_stat 
            WHERE season = '2025/26' AND team_id > 1000
        """))
        count = result.scalar()
        print(f"Found {count} mock rows to delete.")
        if count > 0:
            await conn.execute(text("""
                DELETE FROM team_season_stat 
                WHERE season = '2025/26' AND team_id > 1000
            """))
            await conn.commit()
            print("Mock rows deleted.")
        else:
            print("No mock rows found.")
    await engine.dispose()

asyncio.run(delete_mock())