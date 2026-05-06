import pandas as pd
import soccerdata as sd

print("Initializing FBref...")
fbref = sd.FBref(leagues="ITA-Serie B", seasons="2526")

print("Fetching match results...")
matches = fbref.read_match_results()
print(f"Matches shape: {matches.shape}")
print("Columns:", matches.columns.tolist())
print("\nFirst few rows:")
print(matches.head())

print("\nFetching player match stats...")
player_stats = fbref.read_player_match_stats()
print(f"Player stats shape: {player_stats.shape}")
print("Columns:", player_stats.columns.tolist())
print("\nFirst few rows:")
print(player_stats.head())

print("\nFetching team match stats...")
team_stats = fbref.read_team_match_stats()
print(f"Team stats shape: {team_stats.shape}")
print("Columns:", team_stats.columns.tolist())
print("\nFirst few rows:")
print(team_stats.head())

# Show unique players for Palermo
if 'player' in player_stats.columns:
    palermo_players = player_stats[player_stats['team'] == 'Palermo']['player'].unique()
    print(f"\nPalermo players sample: {palermo_players[:10]}")

print("\nDone.")