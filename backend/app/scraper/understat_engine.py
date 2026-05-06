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
      1. GET request to `https://understat.com/match/{match_id}`
      2. Parse the HTML with BeautifulSoup
      3. Locate the JavaScript assignment `var shotsData = JSON.parse('...');`
      4. Decode the escaped JSON string (unicode_escape)
      5. Return the parsed JSON as a Python dictionary or list.

    Args:
        match_id: Understat's internal match identifier (integer).

    Returns:
        The decoded JSON data. In practice this is a list of dictionaries,
        each describing a shot event, but the function's return type is
        declared broadly to accommodate any JSON structure.

    Raises:
        requests.exceptions.RequestException: If the HTTP request fails
            (network error, non‑200 status, timeout, etc.).
        ValueError: If the `shotsData` variable cannot be found in the HTML,
            or if the extracted JSON string cannot be decoded/parsed.
    """
    url = f"https://understat.com/match/{match_id}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # raises HTTPError for 4xx/5xx
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(
            f"Failed to fetch {url}: {e}"
        ) from e

    html_content = response.text
    soup = BeautifulSoup(html_content, "html.parser")

    # Search for the script containing shotsData assignment
    pattern = re.compile(
        r"var\s+shotsData\s*=\s*JSON\.parse\s*\(\s*'(.*?)'\s*\)\s*;",
        re.DOTALL,
    )

    for script in soup.find_all("script"):
        if script.string is None:
            continue
        match = pattern.search(script.string)
        if match:
            encoded_json = match.group(1)
            # Decode Unicode escape sequences (e.g., \u2013, \x2D)
            decoded_json = encoded_json.encode("utf-8").decode("unicode_escape")
            try:
                return json.loads(decoded_json)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Extracted JSON is malformed: {e}"
                ) from e

    raise ValueError(
        "Variable 'shotsData' not found in any <script> tag of the page."
    )


if __name__ == "__main__":
    # Minimal smoke test – does not perform a real network call.
    # Simply verify that the module can be imported.
    print("Module 'understat_engine' loaded successfully.")