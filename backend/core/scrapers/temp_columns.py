import soccerdata as sd
import pandas as pd
pd.set_option('display.max_columns', None)

# Use Serie B 25/26
fbref = sd.FBref(leagues="ITA-Serie B", seasons="2526")
print("Fetching player match stats...")
player_stats = fbref.read_player_match_stats()
print("Shape:", player_stats.shape)
print("Columns:", player_stats.columns.tolist())
print("\nFirst row:")
print(player_stats.iloc[0])
print("\nDataFrame info:")
print(player_stats.head())

# Let's see the column names that match our mapping
# Standard: Gls, Ast, xG, npxG, xAG
# Passing: ProgPass, Att, Cmp%
# Defense: Tkl, Int, Blocks
# GCA: SCA, GCA
# Possession: ProgC, SuccDrib
# We'll check if they exist
for col in ['Gls', 'Ast', 'xG', 'npxG', 'xAG', 'ProgPass', 'Att', 'Cmp%', 'Tkl', 'Int', 'Blocks', 'SCA', 'GCA', 'ProgC', 'SuccDrib']:
    if col in player_stats.columns:
        print(f"Column {col}: found")
    else:
        print(f"Column {col}: NOT found")

# Let's also see the multi-index structure
print("\nColumn multi-index levels:", player_stats.columns.nlevels)
if player_stats.columns.nlevels > 1:
    print("Level 0:", player_stats.columns.get_level_values(0).unique())
    print("Level 1:", player_stats.columns.get_level_values(1).unique())