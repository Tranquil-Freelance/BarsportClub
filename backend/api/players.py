from fastapi import APIRouter
from sqlalchemy import create_engine, text

router = APIRouter()

DB_URL = "postgresql://postgres:password@localhost:5432/xpalermostat"
engine = create_engine(DB_URL)


@router.get("/players")
def get_players():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT player_id, player_name
            FROM player_registry
            ORDER BY player_name
            LIMIT 100
        """))

        players = [
            {
                "player_id": row[0],
                "player_name": row[1]
            }
            for row in result
        ]

    return players