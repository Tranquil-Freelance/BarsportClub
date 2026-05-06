#!/usr/bin/env python3
"""
Import match and shots data from a local Understat HTML file and raw JSON shots file.

Steps:
1. Read HTML file (`backend/imports/Cagliari 1 - 2 Como.html`) to extract match metadata.
2. Read raw JSON shots file (`backend/imports/shots_30116.json`).
3. Parse JSON (iterate through 'h' and 'a' arrays) and extract shot fields.
4. Insert match (30116) into `matches` table.
5. Insert all parsed shots into `shots` table.

Uses database connection with 127.0.0.1 (fixed from localhost).
"""

import asyncio
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession

# Adjust sys.path to allow imports from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import AsyncSessionLocal
from app.api.crud import save_match_shots


def extract_variable(html: str, variable_name: str):
    """
    Extract a JSON‑parsed JavaScript variable from HTML script tags.

    Understat stores data as `var variable_name = JSON.parse('...');`.
    This function locates that assignment, decodes the escaped string,
    and returns the parsed JSON (list or dictionary).

    Raises ValueError if the variable cannot be found.
    """
    soup = BeautifulSoup(html, "html.parser")
    scripts = soup.find_all("script")

    # Pattern to match `var variable_name = JSON.parse('...');`
    pattern = re.compile(
        rf"var\s+{re.escape(variable_name)}\s*=\s*JSON\.parse\s*\(\s*'(.*?)'\s*\)\s*;",
        re.DOTALL,
    )

    for script in scripts:
        if script.string is None:
            continue
        match = pattern.search(script.string)
        if match:
            encoded = match.group(1)
            # Decode unicode escape sequences (e.g., \x2D, \u2013)
            decoded = encoded.encode("utf-8").decode("unicode_escape")
            return json.loads(decoded)

    # Try double‑quoted version
    pattern2 = re.compile(
        rf'var\s+{re.escape(variable_name)}\s*=\s*JSON\.parse\s*\(\s*"(.*?)"\s*\)\s*;',
        re.DOTALL,
    )
    for script in scripts:
        if script.string is None:
            continue
        match = pattern2.search(script.string)
        if match:
            encoded = match.group(1)
            decoded = encoded.encode("utf-8").decode("unicode_escape")
            return json.loads(decoded)

    raise ValueError(f"Variable '{variable_name}' not found in any <script> tag.")


def extract_match_info(html: str):
    """
    Extract match metadata from HTML.

    Tries to extract 'match_info' first, then falls back to 'matchData'.
    Returns a dict with keys:
        - 'home_team' (str)
        - 'away_team' (str)
        - 'home_goals' (int or None)
        - 'away_goals' (int or None)
        - 'match_date' (str or None)
        - 'league' (str or None)
        - 'match_id' (int or None)

    Raises ValueError if neither variable can be found.
    """
    # Try match_info
    try:
        data = extract_variable(html, "match_info")
    except ValueError:
        data = None

    if isinstance(data, dict):
        # Determine structure based on available keys
        if "team_h" in data and "team_a" in data:
            # New structure (match_info from Understat 2025+)
            home_team = data.get("team_h")
            away_team = data.get("team_a")
            home_goals = data.get("h_goals")
            away_goals = data.get("a_goals")
            match_date = data.get("date")
            league = data.get("league")
            match_id = data.get("id")
        else:
            # Old structure: nested h/a objects
            home_team = data.get("h", {}).get("title")
            away_team = data.get("a", {}).get("title")
            home_goals = data.get("goals", {}).get("h")
            away_goals = data.get("goals", {}).get("a")
            match_date = data.get("datetime")
            league = data.get("league")
            match_id = data.get("id")
    else:
        # Try matchData
        try:
            data = extract_variable(html, "matchData")
        except ValueError as e:
            raise ValueError(
                "Neither 'match_info' nor 'matchData' found in HTML."
            ) from e
        if isinstance(data, dict):
            home_team = data.get("h", {}).get("title")
            away_team = data.get("a", {}).get("title")
            home_goals = data.get("goals", {}).get("h")
            away_goals = data.get("goals", {}).get("a")
            match_date = data.get("datetime")
            league = data.get("league")
            match_id = data.get("id")
        else:
            raise ValueError("Extracted match data is not a dict")

    return {
        "home_team": home_team or "Home",
        "away_team": away_team or "Away",
        "home_goals": home_goals,
        "away_goals": away_goals,
        "match_date": match_date,
        "league": league,
        "match_id": match_id,
    }


def scale_coordinates(shots_data):
    """
    Scale X and Y coordinates from Understat's 0.0‑1.0 range to 0‑100.

    The input dictionary must have the structure {'h': [...], 'a': [...]}.
    Returns a new dictionary with scaled coordinates (original dict is not mutated).
    """
    scaled = {}
    for team_key, shot_list in shots_data.items():
        scaled_list = []
        for shot in shot_list:
            scaled_shot = shot.copy()
            # Scale X and Y
            scaled_shot["X"] = round(float(shot["X"]) * 100, 2)
            scaled_shot["Y"] = round(float(shot["Y"]) * 100, 2)
            scaled_list.append(scaled_shot)
        scaled[team_key] = scaled_list
    return scaled


def read_shots_json(json_path: Path) -> dict:
    """
    Read raw JSON shots file and ensure it has 'h' and 'a' arrays.

    The JSON file is expected to be a direct copy of the network response,
    which should contain a top‑level object with 'h' and 'a' keys, each an array
    of shot objects.

    Each shot object must contain at least:
        - 'id' (int or str)
        - 'minute' (int)
        - 'result' (str)
        - 'X' (float)
        - 'Y' (float)
        - 'xG' (float)
        - 'player' (str)
        - 'h_a' (str) optional, can be inferred from parent array.

    Returns the parsed dict.
    """
    if not json_path.is_file():
        raise FileNotFoundError(f"JSON shots file not found at {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # The JSON might be wrapped in a higher‑level object (e.g., {'data': {...}}).
    # Try to locate the dict that contains 'h' and 'a' arrays.
    def locate_shots(obj):
        if isinstance(obj, dict):
            if "h" in obj and "a" in obj:
                return obj
            for value in obj.values():
                result = locate_shots(value)
                if result is not None:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = locate_shots(item)
                if result is not None:
                    return result
        return None

    shots = locate_shots(data)
    if shots is None:
        # Assume the top‑level is already the shots dict
        if isinstance(data, dict) and "h" in data and "a" in data:
            shots = data
        else:
            raise ValueError(
                "JSON does not contain 'h' and 'a' arrays. "
                "Please provide raw shots response from Understat."
            )

    # Ensure each shot has required fields; add missing h_a if needed.
    for team_key, shot_list in (("h", shots["h"]), ("a", shots["a"])):
        for shot in shot_list:
            # Ensure numeric conversion
            shot["X"] = float(shot.get("X", 0))
            shot["Y"] = float(shot.get("Y", 0))
            shot["xG"] = float(shot.get("xG", 0))
            shot["minute"] = int(shot.get("minute", 0))
            # If h_a missing, set based on parent array
            if "h_a" not in shot:
                shot["h_a"] = team_key
    return shots


async def import_match_and_shots(
    html_path: Path,
    json_path: Path,
) -> dict:
    """
    Main import routine: read HTML and JSON, insert match and shots.
    """
    print(f"Processing HTML: {html_path}")
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    match_info = extract_match_info(html)

    # Determine match ID (prefer extracted, fallback to 30116)
    match_id = match_info.get("match_id")
    if match_id is None:
        match_id = 30116
        print(f"  Warning: No match ID found in HTML, using hardcoded {match_id}")
    else:
        try:
            match_id = int(match_id)
        except (ValueError, TypeError):
            print(f"  Warning: match_id '{match_id}' is not integer, converting to int")
            match_id = int(match_id) if match_id is not None else 30116

    home_team = match_info["home_team"]
    away_team = match_info["away_team"]
    home_goals = match_info["home_goals"]
    away_goals = match_info["away_goals"]
    match_date = match_info["match_date"]
    league = match_info["league"]

    print(f"  Match ID: {match_id}")
    print(f"  Teams: {home_team} vs {away_team}")
    if home_goals is not None and away_goals is not None:
        print(f"  Score: {home_goals}-{away_goals}")
    if match_date:
        print(f"  Date: {match_date}")
    if league:
        print(f"  League: {league}")

    # Read shots from JSON
    print(f"Reading shots JSON: {json_path}")
    raw_shots = read_shots_json(json_path)
    scaled_shots = scale_coordinates(raw_shots)

    print(f"  Home shots: {len(scaled_shots['h'])}")
    print(f"  Away shots: {len(scaled_shots['a'])}")

    # Save to database
    async with AsyncSessionLocal() as session:
        await save_match_shots(
            db=session,
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            shots_data=scaled_shots,
        )
        await session.commit()
    print("  Data saved to database.")

    total_shots = len(scaled_shots["h"]) + len(scaled_shots["a"])
    return {
        "match_id": match_id,
        "home_team": home_team,
        "away_team": away_team,
        "home_shots": len(scaled_shots["h"]),
        "away_shots": len(scaled_shots["a"]),
        "total_shots": total_shots,
        "home_goals": home_goals,
        "away_goals": away_goals,
    }


async def main():
    """Entry point."""
    html_path = Path(__file__).parent.parent / "imports" / "Cagliari 1 - 2 Como.html"
    json_path = Path(__file__).parent.parent / "imports" / "shots_30116.json"

    if not html_path.is_file():
        print(f"Error: HTML file not found at {html_path}")
        sys.exit(1)
    if not json_path.is_file():
        print(f"Error: JSON shots file not found at {json_path}")
        print("Please ensure the raw JSON response is saved as 'shots_30116.json'.")
        sys.exit(1)

    try:
        result = await import_match_and_shots(html_path, json_path)
        print("\nImport successful!")
        print(f"Total shots inserted: {result['total_shots']}")
    except Exception as e:
        print(f"\nError during import: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())