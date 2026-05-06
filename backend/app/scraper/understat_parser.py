"""
Understat.com HTML scraping and JSON extraction.

This module provides functions to fetch Understat pages and extract statistical
data embedded as JavaScript variables in <script> tags.
Now uses the official understat Python package for reliability.
"""

import asyncio
import json
import re
from typing import Optional, Union, List, Dict, Any

import aiohttp
import requests
from bs4 import BeautifulSoup
from understat import Understat


async def get_league_season_data(
    league_slug: str, season_year: int
) -> List[Dict[str, Any]]:
    """
    Retrieve season‑level data for a given league and year.

    Uses the understat package to fetch both results and fixtures,
    merges them, and returns a unified list of matches.

    Args:
        league_slug: Understat's league identifier (e.g., 'EPL', 'La_Liga').
            The package expects lowercase slugs (e.g., 'serie_a').
        season_year: The calendar year the season ends (e.g., 2023 for 2022/23).

    Returns:
        A list of dictionaries, each representing a match‑day entry.
        The format matches the original 'datesData' structure as closely as
        possible for backward compatibility.

    Example:
        >>> data = await get_league_season_data('serie_a', 2025)
        >>> len(data)
        380
    """
    # Normalize slug to lowercase (Understat expects e.g., 'serie_a')
    normalized_slug = league_slug.lower()

    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        try:
            # Fetch already played matches
            results = await understat.get_league_results(normalized_slug, season_year)
        except Exception:
            results = []
        try:
            # Fetch scheduled fixtures (including future matches)
            fixtures = await understat.get_league_fixtures(normalized_slug, season_year)
        except Exception:
            fixtures = []

    # Merge and deduplicate by match ID
    merged = {}
    for match in results + fixtures:
        match_id = match.get('id')
        if match_id:
            merged[match_id] = match

    # Convert back to list and ensure consistent field names
    unified = list(merged.values())

    # Log summary
    print(f"[understat_parser] Fetched {len(results)} results, {len(fixtures)} fixtures, "
          f"total {len(unified)} unique matches for {league_slug} {season_year}")

    return unified


def fetch_html(url: str) -> str:
    """
    Fetch HTML content from a given URL.

    Kept for backward compatibility; used by the legacy shot/roster extraction.

    Args:
        url: The URL to request.

    Returns:
        The HTML content as a string.

    Raises:
        requests.exceptions.HTTPError: If the HTTP request returns a non‑200
            status code.
        requests.exceptions.RequestException: For network‑related errors.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text


def extract_json_from_script(
    html_content: str, variable_name: str
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Extract a JSON‑parsed JavaScript variable from HTML script tags.

    Understat stores data as `var <variable_name> = JSON.parse('...');`.
    This function locates that assignment, decodes the escaped string,
    and returns the parsed JSON (list or dictionary).

    Args:
        html_content: The full HTML page as a string.
        variable_name: The name of the JavaScript variable to extract.

    Returns:
        The decoded JSON data (usually a list of dicts or a dict).

    Raises:
        ValueError: If the variable cannot be found or the JSON is malformed.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    scripts = soup.find_all("script")

    # Pattern to match `var variable_name = JSON.parse('...');`
    # Also matches minimal whitespace variations.
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

    raise ValueError(
        f"Variable '{variable_name}' not found in any <script> tag."
    )


async def get_match_shots(match_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve shot‑level data for a specific match.

    Uses the understat package for reliable extraction.

    Args:
        match_id: Understat's internal match identifier.

    Returns:
        A list of dictionaries, each describing a shot event.

    Example:
        >>> shots = await get_match_shots(12345)
        >>> shots[0]['player']
        'C. Ronaldo'
    """
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        try:
            shots = await understat.get_match_shots(match_id)
            return shots
        except Exception as e:
            print(f"[understat_parser] Error fetching shots for match {match_id}: {e}")
            return []


async def get_match_roster(match_id: int) -> Dict[str, Any]:
    """
    Retrieve roster‑level data for a specific match.

    Uses the understat package for reliable extraction.

    Args:
        match_id: Understat's internal match identifier.

    Returns:
        A dictionary with keys 'h' (home) and 'a' (away), each containing
        a dictionary of player entries keyed by player ID.

    Example:
        >>> roster = await get_match_roster(12345)
        >>> len(roster['h'])
        11
    """
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        try:
            roster = await understat.get_match_players(match_id)
            # The package returns a dict with 'h' and 'a' keys directly
            return roster
        except Exception as e:
            print(f"[understat_parser] Error fetching roster for match {match_id}: {e}")
            return {'h': {}, 'a': {}}


# Legacy synchronous functions for compatibility
def get_league_season_data_sync(league_slug: str, season_year: int) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper for get_league_season_data.

    Useful for scripts that cannot use asyncio.
    """
    return asyncio.run(get_league_season_data(league_slug, season_year))


def get_match_shots_sync(match_id: int) -> List[Dict[str, Any]]:
    """Synchronous wrapper for get_match_shots."""
    return asyncio.run(get_match_shots(match_id))


def get_match_roster_sync(match_id: int) -> Dict[str, Any]:
    """Synchronous wrapper for get_match_roster."""
    return asyncio.run(get_match_roster(match_id))


if __name__ == "__main__":
    # Quick demonstration / smoke test (does not make real network calls).
    print("Module 'understat_parser' loaded successfully.")