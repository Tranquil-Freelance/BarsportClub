#!/usr/bin/env python3
"""
Populate database with 10 random Serie A matches (using duplicated shot data from match 27362).
"""
import asyncio
import sys
import random
sys.path.insert(0, '.')

from app.db.session import AsyncSessionLocal
from app.api.crud import save_match_shots

# Serie A team names (2024/25 season)
SERIE_A_TEAMS = [
    "Inter", "Juventus", "Milan", "Atalanta", "Napoli",
    "Roma", "Lazio", "Fiorentina", "Bologna", "Torino",
    "Genoa", "Monza", "Verona", "Lecce", "Empoli",
    "Cagliari", "Sassuolo", "Salernitana", "Udinese", "Como"
]

def generate_match_data(match_id: int, home_team: str, away_team: str):
    """
    Generate shot data similar to match 27362 but with slight variations.
    Returns dict with 'h' and 'a' lists.
    """
    # Base shot data from match_27362.json (simplified)
    base_shots = [
        {"minute": 12, "player": "Mateo Retegui", "xG": 0.45, "result": "Goal", "X": 0.852, "Y": 0.458},
        {"minute": 24, "player": "Ruslan Malinovskyi", "xG": 0.32, "result": "Saved", "X": 0.789, "Y": 0.603},
        {"minute": 37, "player": "Albert Gudmundsson", "xG": 0.18, "result": "Blocked", "X": 0.721, "Y": 0.305},
        {"minute": 55, "player": "Stefano Sabelli", "xG": 0.07, "result": "Missed", "X": 0.654, "Y": 0.412},
        {"minute": 78, "player": "Caleb Ekuban", "xG": 0.22, "result": "Saved", "X": 0.912, "Y": 0.521},
    ]
    # Add optional fields (some may be None)
    for shot in base_shots:
        shot["situation"] = random.choice(["OpenPlay", "SetPiece", "Corner", "DirectFreekick", "Penalty"])
        shot["shotType"] = random.choice(["LeftFoot", "RightFoot", "Head", "Other"])
        if random.random() < 0.3:
            shot["assist"] = random.choice(["Nicolo Barella", "Lautaro Martinez", "Federico Dimarco", None])
        else:
            shot["assist"] = None
    
    # Duplicate for away team with slight modifications
    away_shots = []
    for shot in base_shots:
        away_shot = shot.copy()
        away_shot["player"] = random.choice(["Lautaro Martinez", "Marcus Thuram", "Hakan Calhanoglu", "Federico Dimarco"])
        away_shot["xG"] = round(random.uniform(0.05, 0.8), 2)
        away_shot["X"] = round(random.uniform(0.1, 0.9), 3)
        away_shot["Y"] = round(random.uniform(0.1, 0.9), 3)
        away_shots.append(away_shot)
    
    return {
        "h": base_shots,
        "a": away_shots
    }

async def populate():
    async with AsyncSessionLocal() as session:
        # Ensure we have at least 10 distinct match IDs (starting from 27363)
        start_id = 27363
        for i in range(10):
            match_id = start_id + i
            home = random.choice(SERIE_A_TEAMS)
            away = random.choice([t for t in SERIE_A_TEAMS if t != home])
            shots_data = generate_match_data(match_id, home, away)
            print(f"Inserting match {match_id}: {home} vs {away} with {len(shots_data['h'])+len(shots_data['a'])} shots")
            try:
                await save_match_shots(session, match_id, home, away, shots_data)
                await session.commit()
                print(f"Match {match_id} saved.")
            except Exception as e:
                await session.rollback()
                print(f"Error saving match {match_id}: {e}")
                # If duplicate conflict, skip
                continue
    print("Population completed.")

if __name__ == '__main__':
    asyncio.run(populate())