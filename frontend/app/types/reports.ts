export interface SeasonStats {
  matchesPlayed: number;
  wins: number;
  draws: number;
  losses: number;
  goalsScored: number;
  goalsConceded: number;
  cleanSheets: number;
  xGPerGame: number;
  shotsOnTargetPerGame: number;
  conversionRate: string;
  averagePossession: string;
}

export interface TopPerformer {
  name: string;
  metric: string;
  value: string | number;
}