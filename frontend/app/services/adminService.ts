/**
 * Admin API service for xPalermoStat.
 * Provides functions to trigger calendar synchronization, live scraping, and check database health.
 */

import { get, post } from '@/app/lib/apiClient';

// Response shape for sync/scrape endpoints (generic success message).
export interface AdminActionResponse {
  message: string;
  [key: string]: unknown; // allow extra fields like league, season
}

// Database health status.
export interface DatabaseHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  details: {
    total_tables: number;
    missing_tables: string[];
    last_scrape_time: string | null;
    uptime_seconds: number;
  };
}

// Mapping of UI league names to backend league_slug and league_id.
const leagueMapping: Record<string, { slug: string; id: number }> = {
  'Serie A': { slug: 'Serie_A', id: 1 },
  'Premier League': { slug: 'EPL', id: 2 },
  'La Liga': { slug: 'La_Liga', id: 3 },
  'Bundesliga': { slug: 'Bundesliga', id: 4 },
  'Ligue 1': { slug: 'Ligue_1', id: 5 },
};

/**
 * Trigger calendar synchronization for a given league and season.
 * @param league UI league name (e.g., 'Serie A', 'Premier League')
 * @param season Season year as string (e.g., '2024')
 */
export async function triggerCalendarSync(
  league: string,
  season: string
): Promise<AdminActionResponse> {
  const mapping = leagueMapping[league];
  if (!mapping) {
    throw new Error(`Unsupported league: ${league}`);
  }
  const seasonYear = parseInt(season, 10);
  if (isNaN(seasonYear)) {
    throw new Error(`Invalid season year: ${season}`);
  }

  // Build query parameters
  const query = new URLSearchParams({
    league_slug: mapping.slug,
    season_year: seasonYear.toString(),
    league_id: mapping.id.toString(),
  }).toString();

  const endpoint = `/scraper/trigger-sync?${query}`;
  // POST with empty body, parameters in query string
  return post<AdminActionResponse>(endpoint, undefined);
}

/**
 * Trigger live match scraping (process completed matches).
 */
export async function triggerLiveScraper(): Promise<AdminActionResponse> {
  return post<AdminActionResponse>('/scraper/trigger-scrape', undefined);
}

/**
 * Retrieve database health status.
 */
export async function getDatabaseHealth(): Promise<DatabaseHealth> {
  return get<DatabaseHealth>('/scraper/status');
}