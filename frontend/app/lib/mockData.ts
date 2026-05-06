/**
 * Realistic mock data for football statistics
 * Strictly typed and reusable across components
 */

// ==================== Team Standings ====================

export interface TeamStanding {
  position: number;
  team: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDifference: number;
  points: number;
  form: string[]; // 'W', 'D', 'L'
  isPalermo?: boolean;
}

export const serieAStandings: TeamStanding[] = [
  {
    position: 1,
    team: 'Inter',
    played: 28,
    won: 23,
    drawn: 3,
    lost: 2,
    goalsFor: 67,
    goalsAgainst: 12,
    goalDifference: +55,
    points: 72,
    form: ['W', 'W', 'D', 'W', 'W'],
    isPalermo: false,
  },
  {
    position: 2,
    team: 'Milan',
    played: 28,
    won: 19,
    drawn: 5,
    lost: 4,
    goalsFor: 55,
    goalsAgainst: 32,
    goalDifference: +23,
    points: 62,
    form: ['W', 'D', 'W', 'L', 'W'],
    isPalermo: false,
  },
  {
    position: 3,
    team: 'Juventus',
    played: 28,
    won: 17,
    drawn: 7,
    lost: 4,
    goalsFor: 44,
    goalsAgainst: 23,
    goalDifference: +21,
    points: 58,
    form: ['D', 'W', 'W', 'D', 'L'],
    isPalermo: false,
  },
  {
    position: 4,
    team: 'Atalanta',
    played: 28,
    won: 16,
    drawn: 5,
    lost: 7,
    goalsFor: 58,
    goalsAgainst: 32,
    goalDifference: +26,
    points: 53,
    form: ['W', 'W', 'L', 'W', 'D'],
    isPalermo: false,
  },
  {
    position: 5,
    team: 'Bologna',
    played: 28,
    won: 15,
    drawn: 8,
    lost: 5,
    goalsFor: 42,
    goalsAgainst: 25,
    goalDifference: +17,
    points: 53,
    form: ['D', 'W', 'W', 'D', 'W'],
    isPalermo: false,
  },
  {
    position: 6,
    team: 'Roma',
    played: 28,
    won: 14,
    drawn: 6,
    lost: 8,
    goalsFor: 52,
    goalsAgainst: 35,
    goalDifference: +17,
    points: 48,
    form: ['W', 'L', 'W', 'D', 'W'],
    isPalermo: false,
  },
  {
    position: 7,
    team: 'Lazio',
    played: 28,
    won: 13,
    drawn: 5,
    lost: 10,
    goalsFor: 36,
    goalsAgainst: 30,
    goalDifference: +6,
    points: 44,
    form: ['L', 'W', 'D', 'L', 'W'],
    isPalermo: false,
  },
  {
    position: 8,
    team: 'Fiorentina',
    played: 28,
    won: 12,
    drawn: 7,
    lost: 9,
    goalsFor: 42,
    goalsAgainst: 32,
    goalDifference: +10,
    points: 43,
    form: ['D', 'L', 'W', 'D', 'W'],
    isPalermo: false,
  },
  // Palermo row – highlighted even though not in top 8
  {
    position: 9,
    team: 'Palermo',
    played: 28,
    won: 18,
    drawn: 6,
    lost: 4,
    goalsFor: 48,
    goalsAgainst: 25,
    goalDifference: +23,
    points: 60,
    form: ['W', 'W', 'D', 'L', 'W'],
    isPalermo: true,
  },
];

// ==================== Team Advanced Stats ====================

export interface TeamStats {
  team: string;
  xgPerMatch: number;
  xgAgainstPerMatch: number;
  ppda: number; // Passes per defensive action (lower = more pressing)
  possession: number; // percentage
  rankingBadge: 'top' | 'mid' | 'low';
}

export const teamStatsList: TeamStats[] = [
  {
    team: 'Inter',
    xgPerMatch: 2.1,
    xgAgainstPerMatch: 0.7,
    ppda: 9.2,
    possession: 58.4,
    rankingBadge: 'top',
  },
  {
    team: 'Milan',
    xgPerMatch: 1.8,
    xgAgainstPerMatch: 1.0,
    ppda: 8.8,
    possession: 54.2,
    rankingBadge: 'top',
  },
  {
    team: 'Juventus',
    xgPerMatch: 1.5,
    xgAgainstPerMatch: 0.8,
    ppda: 10.5,
    possession: 52.7,
    rankingBadge: 'top',
  },
  {
    team: 'Atalanta',
    xgPerMatch: 1.9,
    xgAgainstPerMatch: 1.1,
    ppda: 7.9,
    possession: 56.1,
    rankingBadge: 'top',
  },
  {
    team: 'Bologna',
    xgPerMatch: 1.4,
    xgAgainstPerMatch: 0.9,
    ppda: 11.3,
    possession: 48.9,
    rankingBadge: 'mid',
  },
  {
    team: 'Roma',
    xgPerMatch: 1.7,
    xgAgainstPerMatch: 1.2,
    ppda: 9.8,
    possession: 53.5,
    rankingBadge: 'mid',
  },
  {
    team: 'Lazio',
    xgPerMatch: 1.3,
    xgAgainstPerMatch: 1.0,
    ppda: 10.1,
    possession: 51.8,
    rankingBadge: 'mid',
  },
  {
    team: 'Fiorentina',
    xgPerMatch: 1.5,
    xgAgainstPerMatch: 1.1,
    ppda: 9.5,
    possession: 55.0,
    rankingBadge: 'mid',
  },
  // Palermo stats (Serie B but shown for comparison)
  {
    team: 'Palermo',
    xgPerMatch: 1.6,
    xgAgainstPerMatch: 0.9,
    ppda: 8.5,
    possession: 53.2,
    rankingBadge: 'top',
  },
];

// ==================== Utility Functions ====================

export function getPalermoStanding(): TeamStanding {
  return serieAStandings.find(s => s.isPalermo) ?? serieAStandings[8];
}

export function getPalermoStats(): TeamStats {
  return teamStatsList.find(s => s.team === 'Palermo') ?? teamStatsList[8];
}

// ==================== League Gateway Data ====================

export interface LeagueGatewayCard {
  id: number;
  name: string;
  country: string;
  level: string;
  logoPlaceholder: string;
  color: string;
  description: string;
  stats: {
    matchesAnalyzed: number;
    topTeam: string;
    avgGoals: number;
    avgPossession: number;
  };
}

export const featuredLeagues: LeagueGatewayCard[] = [
  {
    id: 1,
    name: 'Serie A',
    country: 'Italy',
    level: 'Top‑Tier',
    logoPlaceholder: '🏆',
    color: 'from-green-900 to-emerald-800',
    description: 'Italy’s premier division, home to historic clubs and tactical innovation. Dive into advanced metrics, team‑by‑team xG breakdowns, and live match analysis.',
    stats: {
      matchesAnalyzed: 312,
      topTeam: 'Inter',
      avgGoals: 2.8,
      avgPossession: 52.4,
    },
  },
  {
    id: 2,
    name: 'Premier League',
    country: 'England',
    level: 'Top‑Tier',
    logoPlaceholder: '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
    color: 'from-red-900 to-purple-800',
    description: 'The most‑watched league in the world, known for its pace and intensity. Explore pressing stats, player radar charts, and fixture difficulty ratings.',
    stats: {
      matchesAnalyzed: 380,
      topTeam: 'Manchester City',
      avgGoals: 3.1,
      avgPossession: 56.7,
    },
  },
];

// ==================== API Mock Data ====================

export interface League {
  id: number;
  name: string;
  understat_slug: string;
}

export const mockLeagues: League[] = [
  { id: 1, name: 'Serie A', understat_slug: 'serie_a' },
  { id: 2, name: 'Premier League', understat_slug: 'premier_league' },
  { id: 3, name: 'La Liga', understat_slug: 'la_liga' },
  { id: 4, name: 'Bundesliga', understat_slug: 'bundesliga' },
  { id: 5, name: 'Ligue 1', understat_slug: 'ligue_1' },
];

export interface Team {
  id: number;
  name: string;
  league_id: number;
}

export const mockTeams: Team[] = [
  { id: 1, name: 'Palermo', league_id: 1 },
  { id: 2, name: 'Inter', league_id: 1 },
  { id: 3, name: 'Milan', league_id: 1 },
  { id: 4, name: 'Juventus', league_id: 1 },
  { id: 5, name: 'Manchester City', league_id: 2 },
  { id: 6, name: 'Liverpool', league_id: 2 },
];

export interface Match {
  id: number;
  home_team: string;
  away_team: string;
}

export const mockMatches: Match[] = [
  { id: 27362, home_team: 'Palermo', away_team: 'Cosenza' },
  { id: 27363, home_team: 'Inter', away_team: 'Milan' },
  { id: 27364, home_team: 'Juventus', away_team: 'Napoli' },
];

export interface Shot {
  minute: number;
  player: string;
  xG: number;
  result: string;
  X: number;
  Y: number;
  team_type: 'h' | 'a';
}

export interface MatchData {
  match: {
    home_team: string;
    away_team: string;
  };
  shots: {
    h: Shot[];
    a: Shot[];
  };
}

export const mockMatchData: MatchData = {
  match: {
    home_team: 'Palermo',
    away_team: 'Cosenza',
  },
  shots: {
    h: [
      { minute: 23, player: 'Brunori', xG: 0.8, result: 'Goal', X: 45, Y: 30, team_type: 'h' },
      { minute: 56, player: 'Lund', xG: 0.5, result: 'Saved', X: 60, Y: 20, team_type: 'h' },
      { minute: 78, player: 'Di Mariano', xG: 0.3, result: 'Blocked', X: 70, Y: 40, team_type: 'h' },
    ],
    a: [
      { minute: 34, player: 'Tutino', xG: 0.6, result: 'Post', X: 55, Y: 70, team_type: 'a' },
      { minute: 67, player: 'Marino', xG: 0.2, result: 'Off Target', X: 40, Y: 80, team_type: 'a' },
    ],
  },
};

export interface Article {
  id: number;
  slug: string;
  title: string;
  author: string;
  content: string;
  hero_image: string | null;
  category: string | null;
  league: string | null;
  team: string | null;
  is_featured: boolean;
  match_id: number | null;
  created_at: string;
}

export const mockArticles: Article[] = [
  {
    id: 1,
    slug: 'palermo-victory-analysis',
    title: 'Palermo Victory Analysis',
    author: 'John Doe',
    content: '...',
    hero_image: '/da8qkwmw0aaiyr12387620460391257045.jpg',
    category: 'Match Analysis',
    league: 'Serie B',
    team: 'Palermo',
    is_featured: true,
    match_id: 27362,
    created_at: '2026-02-23T10:00:00Z',
  },
];

export default {
  serieAStandings,
  teamStatsList,
  featuredLeagues,
  mockLeagues,
  mockTeams,
  mockMatches,
  mockMatchData,
  mockArticles,
};