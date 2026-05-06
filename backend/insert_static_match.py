#!/usr/bin/env python3
"""
Insert static match data for match 27362 (Genoa vs Inter) into the database.
"""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import AsyncSessionLocal
from app.api.crud import save_match_shots

async def main():
    match_id = 27362
    home_team = "Genoa"
    away_team = "Inter"
    
    # Load shots data from static JSON
    json_path = os.path.join(os.path.dirname(__file__), "match_27362.json")
    with open(json_path, "r", encoding="utf-8") as f:
        shots_data = json.load(f)
    
    if "h" not in shots_data or "a" not in shots_data:
        print("ERROR: JSON must contain 'h' and 'a' keys")
        sys.exit(1)
    
    print(f"Inserting match {match_id} ({home_team} vs {away_team})...")
    print(f"Home shots: {len(shots_data['h'])}")
    print(f"Away shots: {len(shots_data['a'])}")
    
    async with AsyncSessionLocal() as session:
        try:
            await save_match_shots(session, match_id, home_team, away_team, shots_data)
            await session.commit()
            print("Successfully inserted static match data.")
        except Exception as e:
            await session.rollback()
            print(f"Error inserting data: {e}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())