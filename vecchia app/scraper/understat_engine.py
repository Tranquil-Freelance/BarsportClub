"""
Understat match‑shot data extraction engine.

This module provides a low‑level function to retrieve shot‑level data
for a given Understat match identifier. It directly fetches the HTML,
extracts the JSON‑encoded `shotsData` variable, and returns it as a
Python dictionary (or list of dictionaries).
"""

import json
import re
from typing import Dict, List, Any, Union

import requests
from bs4 import BeautifulSoup


def get_understat_match_shots(match_id: int) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Retrieve shot‑level data for a specific Understat match.

    The function performs the following steps:
      1. POST request to `https://understat.com/main/getMatchShots` with JSON payload `{"id": match_id}`.
      2. Parse the JSON response, which should contain keys 'h' (home) and 'a' (away) each being a list of shot dicts.
      3. Return the parsed JSON as a Python dictionary.

    Args:
        match_id: Understat's internal match identifier (integer).

    Returns:
        The decoded JSON data. Expected to be a dictionary with keys 'h' and 'a',
        each containing a list of shot dictionaries.

    Raises:
        requests.exceptions.RequestException: If the HTTP request fails
            (network error, non‑200 status, timeout, etc.).
        ValueError: If the response status is not 200, or if the JSON structure is unexpected.
    """
    url = "https://understat.com/main/getMatchShots"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/json",
        "Referer": f"https://understat.com/match/{match_id}",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    }
    payload = {"id": match_id}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()  # raises HTTPError for 4xx/5xx
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(
            f"Failed to fetch {url}: {e}"
        ) from e

    # Parse JSON response
    try:
        data = response.json()
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Response is not valid JSON: {e}"
        ) from e

    # Validate structure
    if not isinstance(data, dict):
        raise ValueError(f"Expected dict, got {type(data).__name__}")
    if "h" not in data or "a" not in data:
        raise ValueError("Response missing 'h' or 'a' keys. Keys: " + ", ".join(data.keys()))

    # Ensure each value is a list
    if not isinstance(data["h"], list) or not isinstance(data["a"], list):
        raise ValueError("'h' or 'a' is not a list")

    return data


if __name__ == "__main__":
    # Minimal smoke test – does not perform a real network call.
    # Simply verify that the module can be imported.
    print("Module 'understat_engine' loaded successfully.")