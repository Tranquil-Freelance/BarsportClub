"""
Understat.com match scraper for xPalermoStat.

Class‑based scraper that extracts shotsData and matchData from Understat match pages,
scales coordinates, and provides structured data ready for database ingestion.
"""

import json
import re
import time
import random
from typing import Dict, List, Any, Optional, Union
import requests
from bs4 import BeautifulSoup
from app.scraper.understat_engine import get_understat_match_shots


class UnderstatScraper:
    """
    Scraper for Understat match pages.
    
    Attributes:
        base_url (str): Base URL of Understat (default https://understat.com).
        headers (dict): HTTP headers to mimic a real browser.
    """
    
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }
    
    def __init__(self, base_url: str = "https://understat.com", headers: Optional[Dict[str, str]] = None):
        self.base_url = base_url.rstrip('/')
        self.headers = headers or self.DEFAULT_HEADERS
    
    def fetch_html(self, url: str) -> str:
        """
        Fetch HTML content from a given URL with a random delay to avoid blocking.
        
        Args:
            url: Full URL to request.
            
        Returns:
            HTML content as a string.
            
        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        # Random sleep between 2 and 5 seconds to mimic human browsing
        time.sleep(random.uniform(2, 5))
        
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.text
    
    def extract_variable(self, html: str, variable_name: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Extract a JSON‑parsed JavaScript variable from HTML script tags.
        
        Understat stores data as `var <variable_name> = JSON.parse('...');`.
        This method locates that assignment, decodes the escaped string,
        and returns the parsed JSON (list or dictionary).
        
        Args:
            html: The full HTML page as a string.
            variable_name: The name of the JavaScript variable to extract.
            
        Returns:
            The decoded JSON data (usually a list of dicts or a dict).
            
        Raises:
            ValueError: If the variable cannot be found or the JSON is malformed.
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
        
        raise ValueError(f"Variable '{variable_name}' not found in any <script> tag.")
    
    def get_shots_data(self, html: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract shotsData from HTML and ensure it has the expected structure.
        
        Args:
            html: HTML content of a match page.
            
        Returns:
            Dictionary with keys 'h' (home) and 'a' (away), each mapping to a list
            of shot dictionaries. Each shot dict contains at least:
                - 'minute' (int)
                - 'player' (str)
                - 'xG' (float)
                - 'result' (str)
                - 'X' (float)   # coordinate 0.0‑1.0
                - 'Y' (float)   # coordinate 0.0‑1.0
                
        Raises:
            ValueError: If shotsData is missing or malformed.
        """
        try:
            data = self.extract_variable(html, "shotsData")
        except ValueError as e:
            # DEBUG: print script tags to see what's available
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            scripts = soup.find_all("script")
            print("\n=== DEBUG shotsData not found ===")
            for i, script in enumerate(scripts):
                if script.string:
                    if 'Data' in script.string or 'var' in script.string:
                        print(f"\n--- Script {i} (length {len(script.string)}) ---")
                        # print first 2000 chars
                        print(script.string[:2000])
            print("=== END DEBUG ===")
            raise
        # The extracted data may be a dict with 'h'/'a' keys, or a list that we need to group.
        # Based on Understat's structure, shotsData is a dict with 'h' and 'a' keys.
        if not isinstance(data, dict):
            raise ValueError(f"shotsData is not a dict, got {type(data).__name__}")
        if "h" not in data or "a" not in data:
            raise ValueError("shotsData must contain 'h' and 'a' keys")
        # Ensure each value is a list
        for key in ("h", "a"):
            if not isinstance(data[key], list):
                raise ValueError(f"shotsData['{key}'] is not a list")
        return data
    
    def get_match_data(self, html: str) -> Dict[str, Any]:
        """
        Extract matchData from HTML (if present) or fallback to parsing page title.
        
        Attempts to extract the JavaScript variable `matchData`. If not found,
        tries to infer home/away team names from the <title> tag.
        
        Args:
            html: HTML content of a match page.
            
        Returns:
            Dictionary with keys:
                - 'home_team' (str)
                - 'away_team' (str)
                - 'home_goals' (int or None)
                - 'away_goals' (int or None)
                - 'match_date' (str or None)
                - 'league' (str or None)
                
        Raises:
            ValueError: If neither matchData nor a usable title can be found.
        """
        # First try to extract matchData variable
        try:
            data = self.extract_variable(html, "matchData")
            if isinstance(data, dict):
                # Expect structure: {'h': {'title': 'TeamName', 'id': ...}, 'a': {...}, 'goals': {'h': ..., 'a': ...}, ...}
                home_team = data.get("h", {}).get("title")
                away_team = data.get("a", {}).get("title")
                home_goals = data.get("goals", {}).get("h")
                away_goals = data.get("goals", {}).get("a")
                match_date = data.get("datetime")
                league = data.get("league")
                return {
                    "home_team": home_team,
                    "away_team": away_team,
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "match_date": match_date,
                    "league": league,
                }
        except ValueError:
            # DEBUG: print script tags to see what's available
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            scripts = soup.find_all("script")
            print("\n=== DEBUG matchData not found ===")
            for i, script in enumerate(scripts):
                if script.string:
                    if 'Data' in script.string or 'var' in script.string:
                        print(f"\n--- Script {i} (length {len(script.string)}) ---")
                        # print first 2000 chars
                        print(script.string[:2000])
            print("=== END DEBUG ===")
            pass  # matchData not found, fallback to title parsing
        
        # Fallback: parse <title> tag
        soup = BeautifulSoup(html, "html.parser")
        title_tag = soup.title
        if title_tag is not None:
            title = title_tag.string.strip()
            # Typical Understat title format: "Understat - TeamA vs TeamB"
            # We'll attempt to extract teams by removing prefix and splitting by ' vs '
            prefix = "Understat - "
            if title.startswith(prefix):
                teams_part = title[len(prefix):]
                teams = teams_part.split(" vs ")
                if len(teams) == 2:
                    return {
                        "home_team": teams[0].strip(),
                        "away_team": teams[1].strip(),
                        "home_goals": None,
                        "away_goals": None,
                        "match_date": None,
                        "league": None,
                    }
        
        raise ValueError("Could not extract match data from HTML")
    
    @staticmethod
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
    
    def scrape_match(self, match_id: int, force: bool = False) -> Dict[str, Any]:
        """
        Full pipeline: fetch HTML, extract shotsData and matchData, scale coordinates.
        
        Args:
            match_id: Understat's internal match identifier.
            force: If True, continue even when shotsData is missing (return empty shots).
            
        Returns:
            Dictionary with keys:
                - 'match_id' (int)
                - 'shots_data' (dict): scaled shots data with keys 'h'/'a'
                - 'match_data' (dict): match metadata (home_team, away_team, etc.)
                
        Raises:
            requests.exceptions.RequestException: If network request fails.
            ValueError: If required data cannot be extracted and force=False.
        """
        url = f"{self.base_url}/match/{match_id}"
        try:
            html = self.fetch_html(url)
        except requests.exceptions.HTTPError as e:
            if force:
                # Page does not exist (e.g., future match). Return empty data.
                return {
                    "match_id": match_id,
                    "shots_data": {'h': [], 'a': []},
                    "match_data": {
                        "home_team": "Home",
                        "away_team": "Away",
                        "home_goals": None,
                        "away_goals": None,
                        "match_date": None,
                        "league": None,
                    },
                }
            else:
                raise
        
        # DEBUG: print first 5000 characters for match 27362
        if match_id == 27362:
            print("\n=== DEBUG HTML (first 5000 chars) ===")
            print(html[:5000])
            print("=== END DEBUG ===\n")
            # Also print script tags that contain 'shotsData' or 'matchData' or 'var'
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            scripts = soup.find_all("script")
            for i, script in enumerate(scripts):
                if script.string:
                    if 'shotsData' in script.string or 'matchData' in script.string:
                        print(f"\n--- Script {i} (relevant) ---")
                        print(script.string[:2000])
                        print("--- End script ---")
        
        try:
            shots_data = get_understat_match_shots(match_id)
        except ValueError as e:
            if force:
                # If shotsData not found, return empty shots
                shots_data = {'h': [], 'a': []}
            else:
                raise
        scaled_shots = self.scale_coordinates(shots_data)
        try:
            match_data = self.get_match_data(html)
        except ValueError as e:
            if force:
                # If matchData not found, return default metadata
                match_data = {
                    "home_team": "Home",
                    "away_team": "Away",
                    "home_goals": None,
                    "away_goals": None,
                    "match_date": None,
                    "league": None,
                }
            else:
                raise
        
        return {
            "match_id": match_id,
            "shots_data": scaled_shots,
            "match_data": match_data,
        }


if __name__ == "__main__":
    # Quick demonstration / smoke test
    scraper = UnderstatScraper()
    # Use a known match ID (replace with a valid one for testing)
    try:
        result = scraper.scrape_match(12345)
        print(f"Successfully scraped match {result['match_id']}")
        print(f"Home team: {result['match_data']['home_team']}")
        print(f"Away team: {result['match_data']['away_team']}")
        print(f"Home shots: {len(result['shots_data']['h'])}")
        print(f"Away shots: {len(result['shots_data']['a'])}")
    except Exception as e:
        print(f"Test failed: {e}")