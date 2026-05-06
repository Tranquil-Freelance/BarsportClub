import pandas as pd

def clean_match_stats(df_player_stats: pd.DataFrame, match_id: int) -> pd.DataFrame:
    """
    Convert FBref player‑match stats DataFrame into database‑ready format.

    The input DataFrame should be the output of
    `sd.FBref().read_player_match_stats()` filtered for a single match.

    Returns a DataFrame with columns:
        player_id, player_name, team_id, match_id, minutes_played,
        goals, assists, shots, key_passes, xG, xA, xGChain, xGBuildup, position,
        progressive_passes, passes_completed, passes_attempted, pass_completion_pct,
        progressive_carries, dribbles_succeeded, dribbles_attempted,
        tackles, interceptions, blocks, clearances, aerials_won, aerials_lost,
        shot_creating_actions, goal_creating_actions, touches, pressures,
        successful_pressures, recoveries

    Column mapping based on FBref's column names (multi‑index).
    """
    # Flatten multi‑index columns if present
    if isinstance(df_player_stats.columns, pd.MultiIndex):
        # Create flattened column names by joining levels with '_'
        df = df_player_stats.copy()
        df.columns = ['_'.join(filter(None, map(str, col))).strip('_') for col in df.columns]
    else:
        df = df_player_stats.copy()

    # Ensure standard columns exist (player, team, minutes, position)
    # FBref may have 'player', 'team', 'minutes', 'pos' etc.
    # We'll map based on common naming.
    # Player name column (likely 'player')
    player_name_col = None
    for col in ['player', 'Player', 'name', 'Name']:
        if col in df.columns:
            player_name_col = col
            break
    if player_name_col is None:
        raise ValueError("Could not find player name column in FBref data")

    # Team column
    team_col = None
    for col in ['team', 'Team', 'squad', 'Squad']:
        if col in df.columns:
            team_col = col
            break
    if team_col is None:
        raise ValueError("Could not find team column in FBref data")

    # Minutes played column
    minutes_col = None
    for col in ['minutes', 'Minutes', 'min', 'Min']:
        if col in df.columns:
            minutes_col = col
            break
    if minutes_col is None:
        raise ValueError("Could not find minutes column in FBref data")

    # Position column
    position_col = None
    for col in ['position', 'Position', 'pos', 'Pos']:
        if col in df.columns:
            position_col = col
            break
    if position_col is None:
        # Position may not be present; we can default to empty string
        df['position'] = ''
        position_col = 'position'

    # Map FBref columns to our database columns
    # We'll use a mapping dict where keys are our column names, values are tuples (category, stat) or flattened column name
    # For simplicity, we assume flattened column names.
    # Define mapping based on user-provided list.
    mapping = {
        'goals': 'Gls',
        'assists': 'Ast',
        'xG': 'xG',
        'xA': 'xAG',
        'progressive_passes': 'ProgPass',
        'passes_attempted': 'Att',
        'pass_completion_pct': 'Cmp%',
        'tackles': 'Tkl',
        'interceptions': 'Int',
        'blocks': 'Blocks',
        'shot_creating_actions': 'SCA',
        'goal_creating_actions': 'GCA',
        'progressive_carries': 'ProgC',
        'dribbles_succeeded': 'SuccDrib',
    }
    # Additional mapping for columns that may have different names
    # We'll also need to compute passes_completed from Att and Cmp% if possible
    # For now set to None.

    # Initialize output DataFrame with required columns
    out = pd.DataFrame()
    out['player_name'] = df[player_name_col]
    out['team_name'] = df[team_col]  # we'll later map to team_id
    out['minutes_played'] = pd.to_numeric(df[minutes_col], errors='coerce').fillna(0).astype(int)
    out['position'] = df[position_col]

    # Map each stat
    for db_col, fbref_col in mapping.items():
        if fbref_col in df.columns:
            out[db_col] = pd.to_numeric(df[fbref_col], errors='coerce')
        else:
            out[db_col] = None  # will become NaN

    # Handle NaN values: for numeric columns, fill with 0.0 (or None as per DB schema)
    # For nullable columns we keep NaN (will become NULL in DB).
    # For required columns (goals, assists, etc.) we fill with 0.
    required_numeric = ['goals', 'assists', 'xG', 'xA', 'progressive_passes', 'passes_attempted',
                        'pass_completion_pct', 'tackles', 'interceptions', 'blocks',
                        'shot_creating_actions', 'goal_creating_actions', 'progressive_carries',
                        'dribbles_succeeded']
    for col in required_numeric:
        if col in out.columns:
            out[col] = out[col].fillna(0)

    # Compute passes_completed if we have passes_attempted and pass_completion_pct
    if 'passes_attempted' in out.columns and 'pass_completion_pct' in out.columns:
        # pass_completion_pct is percentage (e.g., 85.2)
        out['passes_completed'] = (out['passes_attempted'] * out['pass_completion_pct'] / 100).round().astype('Int64')
    else:
        out['passes_completed'] = None

    # Add missing columns with None
    missing_cols = ['shots', 'key_passes', 'xGChain', 'xGBuildup', 'clearances',
                    'aerials_won', 'aerials_lost', 'touches', 'pressures',
                    'successful_pressures', 'recoveries', 'dribbles_attempted']
    for col in missing_cols:
        out[col] = None

    # Add match_id and placeholder player_id, team_id (will be filled later)
    out['match_id'] = match_id
    out['player_id'] = None  # to be filled by upsert_players
    out['team_id'] = None    # to be filled by upsert_teams

    # Reorder columns to match expected order (not strictly necessary)
    expected_order = ['player_id', 'player_name', 'team_id', 'match_id', 'minutes_played',
                      'goals', 'assists', 'shots', 'key_passes', 'xG', 'xA', 'xGChain', 'xGBuildup', 'position',
                      'progressive_passes', 'passes_completed', 'passes_attempted', 'pass_completion_pct',
                      'progressive_carries', 'dribbles_succeeded', 'dribbles_attempted',
                      'tackles', 'interceptions', 'blocks', 'clearances', 'aerials_won', 'aerials_lost',
                      'shot_creating_actions', 'goal_creating_actions', 'touches', 'pressures',
                      'successful_pressures', 'recoveries']
    # Ensure all columns exist
    for col in expected_order:
        if col not in out.columns:
            out[col] = None
    out = out[expected_order]

    return out