"""
UnderstatScraper – core scraping engine for xPalermoStat.
Fetches HTML from Understat, extracts player‑match statistics from the hidden JSON,
and upserts them into the PostgreSQL database using the football models (Player, PlayerMatchStat).
"""

import json
import random
import time
from typing import Dict, List, Any, Optional
import asyncio

import requests
from bs4 import BeautifulSoup
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
import pandas as pd

from app.scraper.understat_parser import extract_json_from_script
from app.scraper.data_cleaner import UnderstatCleaner
from app.models.football import Player, PlayerMatchStat, Team


class UnderstatScraper:
    """
    Scraper for Understat match pages.
    """

    # Default headers to mimic a real browser
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

    def __init__(self, base_url: str = "https://understat.com"):
        self.base_url = base_url

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

        response = requests.get(url, headers=self.DEFAULT_HEADERS, timeout=30)
        response.raise_for_status()
        return response.text

    def parse_match_data(self, html: str) -> Dict[str, Any]:
        """
        Extract the roster data (rostersData) from an Understat match page.

        Understat stores player‑level statistics in a JavaScript variable named
        `rostersData`. This method locates that variable, decodes the JSON,
        and returns the raw dictionary.

        Args:
            html: HTML content of a match page (e.g., https://understat.com/match/12345).

        Returns:
            Raw rostersData dictionary with keys 'h' (home) and 'a' (away), each
            mapping player IDs to player statistics dictionaries.

        Raises:
            ValueError: If the rostersData variable cannot be found or decoded.
        """
        try:
            data = extract_json_from_script(html, "rostersData")
        except ValueError as e:
            # Fallback: try to manually search for the variable
            soup = BeautifulSoup(html, "html.parser")
            scripts = soup.find_all("script")
            pattern = r"var\s+rostersData\s*=\s*JSON\.parse\s*\(\s*'(.*?)'\s*\)\s*;"
            import re
            for script in scripts:
                if script.string is None:
                    continue
                match = re.search(pattern, script.string, re.DOTALL)
                if match:
                    encoded = match.group(1)
                    decoded = encoded.encode("utf-8").decode("unicode_escape")
                    data = json.loads(decoded)
                    break
            else:
                raise ValueError(
                    "Could not find rostersData in the provided HTML"
                ) from e
        if not isinstance(data, dict) or "h" not in data or "a" not in data:
            raise ValueError(
                "Extracted rostersData is not a dictionary with 'h' and 'a' keys"
            )
        return data

    async def save_match_data(
        self,
        session: AsyncSession,
        match_id: int,
        raw_rosters_data: Dict[str, Any],
    ) -> None:
        """
        Upsert players and their match statistics into the database.

        For each player appearing in the roster:
          1. Upsert a Player record (keyed by Understat player ID).
          2. Upsert a PlayerMatchStat record linked to that player and the given match.

        Args:
            session: SQLAlchemy async session.
            match_id: Understat's internal match identifier.
            raw_rosters_data: Raw rostersData dictionary as returned by
                              `parse_match_data`.

        Returns:
            None
        """
        # Use the existing cleaner to obtain a structured DataFrame
        cleaner = UnderstatCleaner()
        df = cleaner.clean_match_roster(raw_rosters_data, match_id)

        # 1. Upsert Player records
        # Extract unique players
        player_cols = ["player_id", "player_name", "team_id"]
        player_df = df[player_cols].drop_duplicates(subset=["player_id"])
        player_df = player_df.rename(columns={
            "player_id": "id",
            "player_name": "name",
            "team_id": "current_team_id",
        })
        # Ensure integer IDs, nullable for team
        player_df["id"] = player_df["id"].astype(int)
        player_df["current_team_id"] = pd.to_numeric(
            player_df["current_team_id"], errors="coerce"
        ).astype("Int64")
        player_df = player_df.where(pd.notnull(player_df), None)
        player_records = player_df.to_dict(orient="records")

        if player_records:
            stmt = insert(Player).values(player_records)
            stmt = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "name": stmt.excluded.name,
                    "current_team_id": stmt.excluded.current_team_id,
                },
            )
            await session.execute(stmt)

        # 2. Upsert PlayerMatchStat records
        # Map columns to database columns
        stat_df = df[[
            "player_id",
            "match_id",
            "minutes_played",
            "goals",
            "assists",
            "shots",
            "key_passes",
            "xG",
            "xA",
            "xGChain",
            "xGBuildup",
            "position",
        ]].copy()
        stat_df = stat_df.rename(columns={
            "player_id": "player_id",
            "match_id": "match_id",
            "minutes_played": "minutes_played",
            "goals": "goals",
            "assists": "assists",
            "shots": "shots",
            "key_passes": "key_passes",
            "xG": "xG",
            "xA": "xA",
            "xGChain": "xGChain",
            "xGBuildup": "xGBuildup",
            "position": "position",
        })
        # Ensure correct types
        int_cols = ["player_id", "match_id", "minutes_played", "goals", "assists", "shots", "key_passes"]
        for col in int_cols:
            stat_df[col] = pd.to_numeric(stat_df[col], errors="coerce").astype("Int64")
        float_cols = ["xG", "xA", "xGChain", "xGBuildup"]
        for col in float_cols:
            stat_df[col] = pd.to_numeric(stat_df[col], errors="coerce").astype("float64")
        stat_df = stat_df.where(pd.notnull(stat_df), None)
        stat_records = stat_df.to_dict(orient="records")

        if stat_records:
            stmt = insert(PlayerMatchStat).values(stat_records)
            stmt = stmt.on_conflict_do_update(
                index_elements=["player_id", "match_id"],
                set_={
                    "minutes_played": stmt.excluded.minutes_played,
                    "goals": stmt.excluded.goals,
                    "assists": stmt.excluded.assists,
                    "shots": stmt.excluded.shots,
                    "key_passes": stmt.excluded.key_passes,
                    "xG": stmt.excluded.xG,
                    "xA": stmt.excluded.xA,
                    "xGChain": stmt.excluded.xGChain,
                    "xGBuildup": stmt.excluded.xGBuildup,
                    "position": stmt.excluded.position,
                },
            )
            await session.execute(stmt)

        await session.commit()
        print(f"Saved {len(player_records)} players and {len(stat_records)} match stats for match {match_id}")

    # Convenience method that combines fetching, parsing and saving
    async def scrape_and_save_match(
        self,
        session: AsyncSession,
        match_id: int,
    ) -> None:
        """
        Full pipeline: fetch HTML, parse roster data, and upsert into the database.

        Args:
            session: SQLAlchemy async session.
            match_id: Understat match identifier.

        Returns:
            None
        """
        url = f"{self.base_url}/match/{match_id}"
        html = self.fetch_html(url)
        rosters_data = self.parse_match_data(html)
        await self.save_match_data(session, match_id, rosters_data)