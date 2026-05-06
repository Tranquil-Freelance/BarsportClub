"""Quick check: what does team_name look like in player_stats?"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:your_secure_password@localhost:5432/xpalermostat"

async def check():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        # Match info
        match_row = (await conn.execute(text("""
            SELECT id, home_team_id, away_team_id
            FROM matchcalendar WHERE id = 30466
        """))).fetchone()
        print(f"Match 30466: home_team_id={match_row[1]}, away_team_id={match_row[2]}")

        # Distinct team_name in player_stats for match 30466
        rows = (await conn.execute(text("""
            SELECT DISTINCT team_name, LEFT(team_type::text, 60) as team_type_sample
            FROM player_stats
            WHERE match_id = 30466
        """))).fetchall()
        print(f"\nDistinct team_name values:")
        for r in rows:
            print(f"  team_name={r[0]!r}  team_type_sample={r[1]!r}")

        # Can we cast team_name to int?
        rows2 = (await conn.execute(text("""
            SELECT player_name, team_name, team_name::int
            FROM player_stats
            WHERE match_id = 30466
            LIMIT 3
        """))).fetchall()
        print(f"\nteam_name::int samples:")
        for r in rows2:
            print(f"  {r[0]!r}: team_name={r[1]!r} -> int={r[2]}")

        # Try filtering by team_id
        home_id = match_row[1]
        rows3 = (await conn.execute(text("""
            SELECT player_name, position
            FROM player_stats
            WHERE match_id = 30466 AND team_name::int = :tid
            ORDER BY position
            LIMIT 5
        """), {"tid": home_id})).fetchall()
        print(f"\nPlayers for team {home_id} (home):")
        for r in rows3:
            print(f"  {r[0]!r} ({r[1]})")

    await engine.dispose()

asyncio.run(check())
