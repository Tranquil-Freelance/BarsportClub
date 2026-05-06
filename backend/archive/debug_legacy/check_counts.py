import sys
sys.path.insert(0, '.')
from app.db.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    shots = conn.execute(text("SELECT COUNT(*) FROM shots")).scalar()
    matches = conn.execute(text("SELECT COUNT(*) FROM matches")).scalar()
    print(f"Shots: {shots}")
    print(f"Matches: {matches}")