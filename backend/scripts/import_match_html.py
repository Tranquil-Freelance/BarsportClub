#!/usr/bin/env python3
"""
Manual HTML importer for Understat match data.

This script reads a locally saved Understat match HTML file, extracts shotsData
and match_info (or matchData), and saves the parsed data into the PostgreSQL
'matches' and 'shots' tables.

Usage:
    python import_match_html.py <html_file_path>
    python import_match_html.py   (scans backend/imports for latest HTML)

The script expects the HTML to contain the JavaScript variables 'shotsData'
and either 'match_info' or 'matchData'.
"""

import asyncio
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Union

from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession

# Adjust sys.path to allow imports from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import AsyncSessionLocal
from app.api.crud import save_match_shots


def extract_variable(html: str, variable_name: str) -> Union[Dict[str, Any], list]:
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


def extract_shots_data(html: str) -> Dict[str, list]:
    """
    Extract shotsData from HTML and ensure it has the expected structure.

    Returns a dict with keys 'h' (home) and 'a' (away), each mapping to a list
    of shot dictionaries. Each shot dict contains at least:
        - 'minute' (int)
        - 'player' (str)
        - 'xG' (float)
        - 'result' (str)
        - 'X' (float)   # coordinate 0.0‑1.0
        - 'Y' (float)   # coordinate 0.0‑1.0

    Raises ValueError if shotsData is missing or malformed.
    """
    data = extract_variable(html, "shotsData")
    if not isinstance(data, dict):
        raise ValueError(f"shotsData is not a dict, got {type(data).__name__}")
    if "h" not in data or "a" not in data:
        raise ValueError("shotsData must contain 'h' and 'a' keys")
    for key in ("h", "a"):
        if not isinstance(data[key], list):
            raise ValueError(f"shotsData['{key}'] is not a list")
    return data


def extract_match_info(html: str) -> Dict[str, Any]:
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

    Raises ValueError if neither variable can be found.
    """
    # Try match_info
    try:
        data = extract_variable(html, "match_info")
    except ValueError:
        data = None

    if isinstance(data, dict):
        # match_info structure: {'h': {'title': '...'}, 'a': {...}, 'goals': {'h': ..., 'a': ...}}
        home_team = data.get("h", {}).get("title")
        away_team = data.get("a", {}).get("title")
        home_goals = data.get("goals", {}).get("h")
        away_goals = data.get("goals", {}).get("a")
        match_date = data.get("datetime")
        league = data.get("league")
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
        else:
            raise ValueError("Extracted match data is not a dict")

    return {
        "home_team": home_team or "Home",
        "away_team": away_team or "Away",
        "home_goals": home_goals,
        "away_goals": away_goals,
        "match_date": match_date,
        "league": league,
    }


def scale_coordinates(shots_data: Dict[str, list]) -> Dict[str, list]:
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


async def import_html_file(file_path: Path, dry_run: bool = False) -> Dict[str, Any]:
    """
    Read an HTML file, extract match and shot data, and save to database.

    Args:
        file_path: Path to the HTML file.
        dry_run: If True, only extract and print data without saving to the database.

    Returns a summary dictionary with keys:
        - 'match_id' (int, inferred from file name or extracted from HTML)
        - 'home_team' (str)
        - 'away_team' (str)
        - 'home_shots' (int)
        - 'away_shots' (int)
        - 'total_shots' (int)
        - 'home_goals' (int or None)
        - 'away_goals' (int or None)
    """
    print(f"Processing {file_path}...")
    html = file_path.read_text(encoding="utf-8", errors="ignore")

    # Extract data
    raw_shots = extract_shots_data(html)
    scaled_shots = scale_coordinates(raw_shots)
    match_info = extract_match_info(html)

    # Try to infer match ID from file name (e.g., "match_27362.html")
    # If not possible, we could extract from match_info (some variants contain 'id')
    match_id = None
    stem = file_path.stem
    numbers = re.findall(r"\d+", stem)
    if numbers:
        match_id = int(numbers[-1])
    else:
        # Fallback: attempt to extract from match_info
        if "id" in match_info:
            match_id = match_info["id"]
        else:
            raise ValueError(
                "Could not determine match ID from file name or extracted data. "
                "Please rename the file to contain the match ID (e.g., 'match_27362.html')."
            )

    home_team = match_info["home_team"]
    away_team = match_info["away_team"]
    home_goals = match_info["home_goals"]
    away_goals = match_info["away_goals"]

    print(f"  Match ID: {match_id}")
    print(f"  Teams: {home_team} vs {away_team}")
    if home_goals is not None and away_goals is not None:
        print(f"  Score: {home_goals}‑{away_goals}")
    print(f"  Home shots: {len(scaled_shots['h'])}")
    print(f"  Away shots: {len(scaled_shots['a'])}")

    if dry_run:
        print("  DRY RUN: Skipping database insertion.")
    else:
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


async def main() -> None:
    """Command‑line entry point."""
    parser = argparse.ArgumentParser(
        description="Import Understat match data from local HTML file(s)."
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to an HTML file (default: scan backend/imports directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract and print data without saving to the database.",
    )
    args = parser.parse_args()

    imports_dir = Path(__file__).parent.parent / "imports"
    if not imports_dir.is_dir():
        print(f"Error: imports directory not found at {imports_dir}")
        sys.exit(1)

    if args.file:
        file_path = Path(args.file).resolve()
        if not file_path.is_file():
            print(f"Error: file '{file_path}' does not exist.")
            sys.exit(1)
        await import_html_file(file_path, dry_run=args.dry_run)
        return

    # Otherwise, scan the imports directory for HTML files
    html_files = list(imports_dir.glob("*.html"))
    if not html_files:
        print(f"No HTML files found in {imports_dir}")
        print("Please save an Understat match page as HTML in that directory.")
        sys.exit(1)

    # Process each file
    for file_path in html_files:
        try:
            summary = await import_html_file(file_path, dry_run=args.dry_run)
            print(f"✓ Successfully imported {file_path.name}")
        except Exception as e:
            print(f"✗ Failed to import {file_path.name}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())