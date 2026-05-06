#!/usr/bin/env python3
"""
Insert a test match with sample shot data for frontend development.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.db.session import AsyncSessionLocal
from app.api.crud import save_match_shots

async def main():
    async with AsyncSessionLocal() as db:
        match_id = 99999
        home_team = "Palermo"
        away_team = "Como"
        shots_data = {
            "h": [
                {
                    "minute": 12,
                    "player": "Matteo Brunori",
                    "xG": 0.45,
                    "result": "Goal",
                    "X": 85.2,
                    "Y": 45.8,
                },
                {
                    "minute": 34,
                    "player": "Roberto Floriano",
                    "xG": 0.12,
                    "result": "Saved",
                    "X": 78.9,
                    "Y": 60.3,
                },
                {
                    "minute": 67,
                    "player": "Jacopo Segre",
                    "xG": 0.08,
                    "result": "Blocked",
                    "X": 72.1,
                    "Y": 30.5,
                },
            ],
            "a": [
                {
                    "minute": 23,
                    "player": "Patrick Cutrone",
                    "xG": 0.32,
                    "result": "Saved",
                    "X": 15.7,
                    "Y": 55.0,
                },
                {
                    "minute": 55,
                    "player": "Luis Malagon",
                    "xG": 0.05,
                    "result": "Missed",
                    "X": 22.4,
                    "Y": 40.2,
                },
                {
                    "minute": 89,
                    "player": "Gabriele Gori",
                    "xG": 0.78,
                    "result": "Goal",
                    "X": 10.5,
                    "Y": 48.9,
                },
            ]
        }
        try:
            await save_match_shots(db, match_id, home_team, away_team, shots_data)
            print(f"Test match {match_id} inserted successfully.")
            print(f"Home shots: {len(shots_data['h'])}, Away shots: {len(shots_data['a'])}")
        except Exception as e:
            print(f"Error inserting test match: {e}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())