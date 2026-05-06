"""
SoccerData‑based shot extraction engine for xPalermoStat.

This module provides a function to fetch shot‑level data for a given Understat match
using the soccerdata library, which is more robust against site changes and includes
built‑in caching and anti‑bot measures.

The output format is compatible with the existing `save_match_shots` database function.
"""

import logging
from typing import Dict, List, Any, Optional
import pandas as pd
from soccerdata import Understat

logger = logging.getLogger(__name__)


def scale_coordinates(shots_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Scale X and Y coordinates from Understat's 0.0‑1.0 range to 0‑100.

    Understat stores shot locations as proportions of the pitch length/width.
    The database expects integer percentages (0‑100). This function multiplies
    each X and Y value by 100 and rounds to two decimal places.

    The input dictionary must have the structure {'h': [...], 'a': [...]}.
    Returns a new dictionary with scaled coordinates (original dict is not mutated).
    """
    scaled = {}
    for team_key, shot_list in shots_data.items():
        scaled_list = []
        for shot in shot_list:
            # Create a copy to avoid mutating the original
            scaled_shot = shot.copy()
            # Scale X and Y
            scaled_shot['X'] = round(float(shot['X']) * 100, 2)
            scaled_shot['Y'] = round(float(shot['Y']) * 100, 2)
            scaled_list.append(scaled_shot)
        scaled[team_key] = scaled_list
    return scaled


def fetch_match_shots(match_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve shot data for a specific Understat match using soccerdata.

    Args:
        match_id: Understat's internal match identifier (integer).

    Returns:
        A dictionary with the following keys:
            - 'home_team': str, home team name
            - 'away_team': str, away team name
            - 'shots_data': dict with keys 'h' and 'a', each a list of shot dicts.
               Each shot dict contains keys:
                   'minute', 'player', 'xG', 'result', 'X', 'Y'
        Returns None if the match cannot be fetched or parsed.

    Raises:
        ImportError: If soccerdata is not installed.
        ValueError: If the fetched DataFrame does not contain required columns.
    """
    try:
        understat = Understat()
        df = understat.read_match_shots(match_id=[match_id])
    except Exception as e:
        logger.error(f"Failed to fetch match {match_id} via soccerdata: {e}")
        return None

    if df.empty:
        logger.warning(f"No shot data found for match {match_id}")
        return None

    # Expected column names in soccerdata's DataFrame (adjust if necessary)
    column_map = {
        'X': 'X',
        'Y': 'Y',
        'xG': 'xG',
        'player': 'player',
        'result': 'result',
        'minute': 'minute',
        'team': 'team',  # 'h' or 'a'
    }

    # Rename columns to internal names (if different)
    for src, dst in column_map.items():
        if src in df.columns and dst not in df.columns:
            df = df.rename(columns={src: dst})

    # Ensure required columns are present
    required = ['X', 'Y', 'xG', 'player', 'result', 'minute', 'team']
    missing = [col for col in required if col not in df.columns]
    if missing:
        logger.error(f"DataFrame missing required columns: {missing}. Available columns: {list(df.columns)}")
        raise ValueError(f"Missing columns: {missing}")

    # Extract home and away team names (assuming they are uniform across rows)
    home_team = df.get('home_team', 'Home').iloc[0]
    away_team = df.get('away_team', 'Away').iloc[0]

    # Group shots by team
    shots_data = {'h': [], 'a': []}
    for _, row in df.iterrows():
        team_key = row['team'].lower()  # 'h' or 'a' (should be already)
        if team_key not in ('h', 'a'):
            # If team column is something else (e.g., 'home', 'away'), map it
            if row['team'] == 'home' or row['team'] == 'h_team':
                team_key = 'h'
            elif row['team'] == 'away' or row['team'] == 'a_team':
                team_key = 'a'
            else:
                logger.warning(f"Unknown team value '{row['team']}', skipping shot")
                continue

        shot = {
            'minute': int(row['minute']),
            'player': str(row['player']),
            'xG': float(row['xG']),
            'result': str(row['result']),
            'X': float(row['X']),
            'Y': float(row['Y']),
        }
        shots_data[team_key].append(shot)

    # Scale coordinates to 0‑100
    scaled_shots = scale_coordinates(shots_data)

    return {
        'home_team': home_team,
        'away_team': away_team,
        'shots_data': scaled_shots,
    }


async def save_match_shots_to_db(match_id: int, db_session) -> int:
    """
    Convenience async function that fetches shots for a match and saves them to the database
    using the existing `save_match_shots` CRUD function.

    Args:
        match_id: Understat match ID.
        db_session: SQLAlchemy async session.

    Returns:
        Total number of shots saved (home + away).

    Raises:
        ValueError: If fetch fails.
    """
    from app.api.crud import save_match_shots

    data = fetch_match_shots(match_id)
    if data is None:
        raise ValueError(f"Could not fetch shot data for match {match_id}")

    await save_match_shots(
        db=db_session,
        match_id=match_id,
        home_team=data['home_team'],
        away_team=data['away_team'],
        shots_data=data['shots_data'],
    )

    total_shots = len(data['shots_data']['h']) + len(data['shots_data']['a'])
    return total_shots


if __name__ == '__main__':
    # Command‑line test: fetch and display first 5 rows of DataFrame
    import sys
    import asyncio
    from app.db.database import AsyncSessionLocal

    if len(sys.argv) != 2:
        print("Usage: python soccerdata_engine.py <match_id>")
        sys.exit(1)

    try:
        match_id = int(sys.argv[1])
    except ValueError:
        print("Error: match_id must be an integer.")
        sys.exit(1)

    # Fetch and display DataFrame sample
    understat = Understat()
    df = understat.read_match_shots(match_id=[match_id])
    print(f"DataFrame shape: {df.shape}")
    print("\nFirst 5 rows:")
    print(df.head().to_string())
    print("\nColumns:", list(df.columns))

    # Optionally save to DB (comment out if only testing)
    # async def test_save():
    #     async with AsyncSessionLocal() as session:
    #         total = await save_match_shots_to_db(match_id, session)
    #         print(f"Saved {total} shots to database.")
    # asyncio.run(test_save())