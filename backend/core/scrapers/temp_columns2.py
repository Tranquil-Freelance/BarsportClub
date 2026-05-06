import soccerdata as sd
import pandas as pd
pd.set_option('display.max_columns', None)

# Use Serie A (valid)
fbref = sd.FBref(leagues="ITA-Serie A", seasons="2526")
print("Fetching player match stats...")
player_stats = fbref.read_player_match_stats()
print("Shape:", player_stats.shape)
print("Columns:", player_stats.columns.tolist())
print("\nFirst row index:", player_stats.index.names)
print("\nFirst row:")
print(player_stats.iloc[0])
print("\nColumn multi-index levels:", player_stats.columns.nlevels)
if player_stats.columns.nlevels > 1:
    print("Level 0 unique:", player_stats.columns.get_level_values(0).unique())
    print("Level 1 unique:", player_stats.columns.get_level_values(1).unique())
    # Let's see mapping for each subcategory
    for cat in player_stats.columns.get_level_values(0).unique():
        subcols = player_stats.columns[player_stats.columns.get_level_values(0) == cat]
        print(f"\nCategory '{cat}': {list(subcols.get_level_values(1))}")

# Let's also fetch a single match stats to see structure
# We need a match ID; maybe we can get from schedule
print("\n--- Schedule ---")
schedule = fbref.read_schedule()
print("Schedule columns:", schedule.columns.tolist())
print("First row:", schedule.iloc[0])
if 'game_id' in schedule.columns:
    match_id = schedule.iloc[0]['game_id']
    print(f"Game ID: {match_id}")
    # Fetch player match stats for that game
    player_stats_match = fbref.read_player_match_stats(match_id=match_id)
    print(f"Player stats for match {match_id} shape:", player_stats_match.shape)
    if not player_stats_match.empty:
        print("Columns:", player_stats_match.columns.tolist())
        print("First player:", player_stats_match.iloc[0])
else:
    print("No game_id column")