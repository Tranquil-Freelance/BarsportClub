"""
Data cleaning module for Understat JSON extraction.

Transforms raw JSON data from Understat into structured pandas DataFrames,
ready for insertion into the PostgreSQL database.
"""

import pandas as pd
from typing import List, Dict, Any


class UnderstatCleaner:
    """
    Static methods for cleaning Understat JSON data.
    """

    @staticmethod
    def clean_match_calendar(raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert raw match‑calendar data (from Understat's 'datesData') into a
        flat, database‑ready pandas DataFrame.

        The raw JSON contains nested dictionaries for home/away teams (`h`, `a`),
        goals (`goals`), and expected goals (`xG`). This method flattens those
        structures, renames columns to match the database schema, and ensures
        proper data types.

        Args:
            raw_data: List of dictionaries as returned by `extract_json_from_script`
                with variable name 'datesData'.

        Returns:
            A pandas DataFrame with the following columns:
                - id (int): Understat's match identifier.
                - datetime (pd.Timestamp): UTC match start time.
                - is_completed (bool): Whether the match has been played.
                - home_team_id (int): Understat's home team ID.
                - home_team_name (str): Home team's full name.
                - away_team_id (int): Understat's away team ID.
                - away_team_name (str): Away team's full name.
                - home_goals (Int64): Actual home goals (nullable).
                - away_goals (Int64): Actual away goals (nullable).
                - home_xG (float64): Expected home goals (nullable).
                - away_xG (float64): Expected away goals (nullable).

        Raises:
            ValueError: If the raw_data is not a list of dictionaries.
        """
        if not isinstance(raw_data, list):
            raise ValueError("raw_data must be a list of dictionaries")
        if raw_data and not isinstance(raw_data[0], dict):
            raise ValueError("raw_data elements must be dictionaries")

        df = pd.DataFrame(raw_data)

        # Flatten nested team dictionaries
        df["home_team_id"] = df["h"].apply(
            lambda x: x.get("id") if isinstance(x, dict) else None
        )
        df["home_team_name"] = df["h"].apply(
            lambda x: x.get("title") if isinstance(x, dict) else None
        )
        df["away_team_id"] = df["a"].apply(
            lambda x: x.get("id") if isinstance(x, dict) else None
        )
        df["away_team_name"] = df["a"].apply(
            lambda x: x.get("title") if isinstance(x, dict) else None
        )

        # Flatten goals dictionary
        df["home_goals"] = df["goals"].apply(
            lambda x: x.get("h") if isinstance(x, dict) else None
        )
        df["away_goals"] = df["goals"].apply(
            lambda x: x.get("a") if isinstance(x, dict) else None
        )

        # Flatten xG dictionary
        df["home_xG"] = df["xG"].apply(
            lambda x: x.get("h") if isinstance(x, dict) else None
        )
        df["away_xG"] = df["xG"].apply(
            lambda x: x.get("a") if isinstance(x, dict) else None
        )
        # Add round column (not provided by Understat)
        df["round"] = pd.NA

        # Rename boolean column to match database field
        df.rename(columns={"isResult": "is_completed"}, inplace=True)

        # Convert isResult to boolean (0/1 -> True/False)
        df["is_completed"] = df["is_completed"].astype(bool)

        # Cast team IDs to nullable integer
        df["home_team_id"] = pd.to_numeric(df["home_team_id"], errors="coerce").astype("Int64")
        df["away_team_id"] = pd.to_numeric(df["away_team_id"], errors="coerce").astype("Int64")

        # Convert datetime string to pandas Timestamp (UTC‑aware)
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

        # Compute round based on chronological order
        df = df.sort_values("datetime", na_position="last")
        matches_per_round = len(df) // 38  # 38 rounds in a season
        df = df.reset_index(drop=True)
        df["round"] = (df.index // matches_per_round) + 1

        # Cast numeric columns with proper nullable types
        df["home_goals"] = pd.to_numeric(df["home_goals"], errors="coerce").astype(
            "Int64"
        )
        df["away_goals"] = pd.to_numeric(df["away_goals"], errors="coerce").astype(
            "Int64"
        )
        df["home_xG"] = pd.to_numeric(df["home_xG"], errors="coerce").astype("float64")
        df["away_xG"] = pd.to_numeric(df["away_xG"], errors="coerce").astype("float64")

        # Drop original nested columns and any other unexpected fields
        columns_to_drop = ["h", "a", "goals", "xG"]
        # Also drop any extra columns that are not part of the target schema
        target_columns = {
            "id",
            "datetime",
            "is_completed",
            "home_team_id",
            "home_team_name",
            "away_team_id",
            "away_team_name",
            "home_goals",
            "away_goals",
            "home_xG",
            "away_xG",
            "round",
        }
        extra_columns = [c for c in df.columns if c not in target_columns]
        df.drop(columns=columns_to_drop + extra_columns, errors="ignore", inplace=True)

        # Ensure column order for readability (optional)
        column_order = [
            "id",
            "datetime",
            "is_completed",
            "home_team_id",
            "home_team_name",
            "away_team_id",
            "away_team_name",
            "home_goals",
            "away_goals",
            "home_xG",
            "away_xG",
            "round",
        ]
        # Keep only columns that actually exist (e.g., if some were missing)
        existing_columns = [c for c in column_order if c in df.columns]
        df = df[existing_columns]

        return df

    @staticmethod
    def clean_match_roster(raw_data: Dict[str, Any], match_id: int) -> pd.DataFrame:
        """
        Convert raw roster data (from Understat's 'rostersData') into a flat,
        database‑ready pandas DataFrame.

        The raw JSON is a dictionary with two keys: 'h' (home) and 'a' (away).
        Each key maps to a dictionary where the keys are player IDs and the
        values are player‑level dictionaries containing statistics.

        Args:
            raw_data: Dictionary as returned by `extract_json_from_script`
                with variable name 'rostersData'.
            match_id: Understat's internal match identifier.

        Returns:
            A pandas DataFrame with the following columns:
                - player_id (int): Understat's player identifier.
                - player_name (str): Player's full name.
                - team_id (int): Understat's team identifier.
                - match_id (int): The match identifier (same for all rows).
                - minutes_played (int): Minutes on pitch.
                - goals (int): Goals scored.
                - assists (int): Assists provided.
                - shots (int): Total shots.
                - key_passes (int): Key passes.
                - xG (float64): Expected goals.
                - xA (float64): Expected assists.
                - xGChain (float64): Expected goal chain value.
                - xGBuildup (float64): Expected goal buildup value.
                - position (str): Player's position (e.g., 'GK', 'DF', 'MF', 'FW').

        Raises:
            ValueError: If raw_data does not contain 'h' and/or 'a' keys.
        """
        if not isinstance(raw_data, dict) or "h" not in raw_data or "a" not in raw_data:
            raise ValueError("raw_data must be a dict with 'h' and 'a' keys")

        rows = []

        # Process home players
        for player_id_str, player_dict in raw_data["h"].items():
            if not isinstance(player_dict, dict):
                continue
            row = {
                "player_id": (
                    int(player_id_str) if player_id_str.isdigit() else None
                ),
                "player_name": player_dict.get("player"),
                "team_id": (
                    int(player_dict.get("team_id"))
                    if player_dict.get("team_id")
                    else None
                ),
                "match_id": match_id,
                "minutes_played": int(player_dict.get("time", 0)),
                "goals": int(player_dict.get("goals", 0)),
                "assists": int(player_dict.get("assists", 0)),
                "shots": int(player_dict.get("shots", 0)),
                "key_passes": int(player_dict.get("key_passes", 0)),
                "xG": float(player_dict.get("xG", 0.0)),
                "xA": float(player_dict.get("xA", 0.0)),
                "xGChain": float(player_dict.get("xGChain", 0.0)),
                "xGBuildup": float(player_dict.get("xGBuildup", 0.0)),
                "position": player_dict.get("position"),
            }
            rows.append(row)

        # Process away players
        for player_id_str, player_dict in raw_data["a"].items():
            if not isinstance(player_dict, dict):
                continue
            row = {
                "player_id": (
                    int(player_id_str) if player_id_str.isdigit() else None
                ),
                "player_name": player_dict.get("player"),
                "team_id": (
                    int(player_dict.get("team_id"))
                    if player_dict.get("team_id")
                    else None
                ),
                "match_id": match_id,
                "minutes_played": int(player_dict.get("time", 0)),
                "goals": int(player_dict.get("goals", 0)),
                "assists": int(player_dict.get("assists", 0)),
                "shots": int(player_dict.get("shots", 0)),
                "key_passes": int(player_dict.get("key_passes", 0)),
                "xG": float(player_dict.get("xG", 0.0)),
                "xA": float(player_dict.get("xA", 0.0)),
                "xGChain": float(player_dict.get("xGChain", 0.0)),
                "xGBuildup": float(player_dict.get("xGBuildup", 0.0)),
                "position": player_dict.get("position"),
            }
            rows.append(row)

        df = pd.DataFrame(rows)

        # Convert numeric columns to nullable types (Int64, float64)
        int_columns = ["player_id", "team_id", "minutes_played", "goals", "assists", "shots", "key_passes"]
        for col in int_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

        float_columns = ["xG", "xA", "xGChain", "xGBuildup"]
        for col in float_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")

        # Ensure match_id is integer
        df["match_id"] = pd.to_numeric(df["match_id"], errors="coerce").astype("Int64")

        # Drop rows where player_id is missing (should not happen)
        df.dropna(subset=["player_id"], inplace=True)

        # Order columns
        column_order = [
            "player_id",
            "player_name",
            "team_id",
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
        ]
        # Keep only columns that exist (should be all)
        existing_columns = [c for c in column_order if c in df.columns]
        df = df[existing_columns]

        return df


if __name__ == "__main__":
    # Quick demonstration / smoke test (does not make real network calls).
    print("Module 'data_cleaner' loaded successfully.")