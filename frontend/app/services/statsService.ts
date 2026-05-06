/**
 * Statistics API service for xPalermoStat.
 * Provides typed functions for fetching player leaderboards and seasonal reports.
 */

import { get } from '@/app/lib/apiClient';
import { SeasonStats } from '@/app/types/reports';

// Match‑level statistics for a single player in a single match.
// Corresponds to the backend `PlayerMatchStat` model.
export interface PlayerMatchStat {
  id: string; // UUID
  player_id: number;
  match_id: number;
  minutes_played: number;
  goals: number;
  assists: number;
  shots: number;
  key_passes: number;
  xG: number;
  xA: number;
  xGChain: number;
  xGBuildup: number;
  position: string;
}

// Aggregated player statistics as returned by the `/statistics/top‑players` endpoint.
export interface PlayerStatAgg {
  player_id: number;
  player_name: string;
  team_name: string | null;
  matches_played: number;
  total_minutes: number;
  total_goals: number;
  total_assists: number;
  total_xG: number;
  total_xA: number;
  xG_per_90: number;
}

// Response shape for the player leaderboard.
export type TopPlayersResponse = PlayerStatAgg[];

// Response shape for the seasonal report.
export type SeasonReportResponse = SeasonStats;

// Radar chart data point
export interface RadarDataPoint {
  subject: string;
  A: number;
  fullMark: number;
}

// Scatter plot data point
export interface ScatterDataPoint {
  name: string;
  xG: number;
  goals: number;
  fill: string;
}

/**
 * Fetches the player leaderboard from `/statistics/top‑players`.
 * Optionally accepts league and minimum‑minutes filters.
 */
export async function getTopPlayers(
  leagueId: number = 1, // Default: Serie A
  minMinutes: number = 90,
  limit: number = 20
): Promise<TopPlayersResponse> {
  const params = new URLSearchParams({
    league_id: leagueId.toString(),
    min_minutes: minMinutes.toString(),
    limit: limit.toString(),
  });
  return get<TopPlayersResponse>(`/statistics/top-players?${params.toString()}`);
}

/**
 * Fetches the seasonal data from `/statistics/season‑report`.
 * Accepts a league ID and a season identifier (e.g., "2024‑2025").
 */
export async function getWinterReport(
  leagueId: number = 1,
  season: string = '2024-2025'
): Promise<SeasonReportResponse> {
  const params = new URLSearchParams({
    league_id: leagueId.toString(),
    season,
  });
  return get<SeasonReportResponse>(`/statistics/season-report?${params.toString()}`);
}

/**
 * Fetches radar chart data for a given player (defaults to first player in leaderboard).
 * Returns percentile ranks across eight key performance indicators.
 */
export async function getPlayerRadarData(playerId?: number): Promise<RadarDataPoint[]> {
  const players = await getTopPlayers(1, 90, 20);
  const player = players[0]; // fallback to top player
  // For now, return mock data; replace with real percentile calculation when backend supports
  return [
    { subject: 'Non-Penalty xG', A: 85, fullMark: 100 },
    { subject: 'xA', A: 70, fullMark: 100 },
    { subject: 'Shots', A: 90, fullMark: 100 },
    { subject: 'Key Passes', A: 65, fullMark: 100 },
    { subject: 'Touches in Box', A: 80, fullMark: 100 },
    { subject: 'Progressive Passes', A: 75, fullMark: 100 },
    { subject: 'Successful Dribbles', A: 60, fullMark: 100 },
    { subject: 'Defensive Actions', A: 50, fullMark: 100 },
  ];
}

/**
 * Fetches scatter plot data comparing xG vs actual goals for league players.
 * Uses real aggregated data from the top‑players endpoint.
 */
export async function getEfficiencyScatterData(): Promise<ScatterDataPoint[]> {
  const players = await getTopPlayers(1, 90, 20);
  return players.map((p, idx) => ({
    name: p.player_name,
    xG: p.total_xG,
    goals: p.total_goals,
    fill: idx === 0 ? '#f472b6' : '#10b981', // highlight first player
  }));
}

export interface TeamPerformanceMetric {
  team: string;
  metrics: {
    true_team_strength: number;
    shot_quality_differential: number;
    attacking_efficiency: number;
    possession_danger_index: number;
    threat_creation_index: number;
    squad_architecture_score: number;
    danger_flow_index: number;
  };
  raw_data: {
    matches_played: number;
    goals_for: number;
    goals_against: number;
    xg_for: number;
    xg_against: number;
    shots_for: number;
    shots_against: number;
    key_passes: number;
    xgchain: number;
    xgbuildup: number;
  };
}

export async function getTeamPerformanceMetrics(
  leagueId: number = 1,
  season: string = "2025/26"
): Promise<TeamPerformanceMetric[]> {
  const params = new URLSearchParams({
    league_id: leagueId.toString(),
    season,
  });
  return get<TeamPerformanceMetric[]>(`/api/v1/team-performance?${params.toString()}`);
}