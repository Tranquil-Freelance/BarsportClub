import PlayerTable, { PlayerData } from "../components/PlayerTable";
import { BarChart3, Target, Zap, TrendingUp } from "lucide-react";
import { getTopPlayers } from "../services/statsService";

export default async function TopPlayersPage() {
  // Fetch real data from backend
  let players: PlayerData[] = [];
  let error: string | null = null;

  try {
    const data = await Promise.race([
      getTopPlayers(1, 90, 20),
      new Promise<never>((_, reject) => setTimeout(() => reject(new Error("Timeout")), 8000)),
    ]); // Serie A league ID = 1, min minutes = 90, limit = 20

    // Map backend PlayerStatAgg to PlayerData
    const mapped = data.map((item, index) => ({
      id: item.player_id,
      rank: index + 1, // temporary rank based on order (backend returns sorted by xG desc)
      name: item.player_name,
      team: item.team_name || "Unknown",
      goals: item.total_goals,
      xG: item.total_xG,
      assists: item.total_assists,
      xA: item.total_xA,
    }));

    // Re-rank by total xG + xA descending (more accurate)
    mapped.sort((a, b) => (b.xG + b.xA) - (a.xG + a.xA));
    mapped.forEach((p, idx) => p.rank = idx + 1);

    players = mapped;
  } catch (err) {
    console.error("Failed to fetch player statistics:", err);
    error = "Unable to load player statistics at this time. Please try again later.";
  }

  // Error fallback UI
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white flex items-center justify-center">
        <div className="text-center max-w-md p-8 rounded-2xl border border-rose-200 bg-gradient-to-br from-rose-50 to-white shadow-lg">
          <h2 className="text-2xl font-bold text-rose-800 mb-4">Data Unavailable</h2>
          <p className="text-slate-700 mb-6">{error}</p>
          <div className="text-sm text-slate-500">
            Ensure the backend server is running at <code className="bg-slate-100 px-2 py-1 rounded">http://localhost:8000</code>
          </div>
        </div>
      </div>
    );
  }

  // If no players (empty response)
  if (players.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white flex items-center justify-center">
        <div className="text-center max-w-md p-8 rounded-2xl border border-amber-200 bg-gradient-to-br from-amber-50 to-white shadow-lg">
          <h2 className="text-2xl font-bold text-amber-800 mb-4">No Player Data</h2>
          <p className="text-slate-700 mb-6">
            The backend returned an empty list. This may indicate that no matches have been scraped yet.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        {/* Page Header */}
        <div className="mb-10 text-center">
          <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            Serie A Player Performance Leaderboard
          </h1>
          <p className="mt-4 text-lg text-slate-600 max-w-3xl mx-auto">
            Advanced metrics showing expected goals (xG) and
            expected assists (xA) for the 2024‑25 season. Data updates daily.
          </p>
        </div>

        {/* Analytical Insight Section */}
        <div className="mb-12 rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-8 shadow-lg">
          <div className="flex items-start justify-between">
            <div>
              <div className="mb-4 flex items-center space-x-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-r from-emerald-500 to-cyan-400">
                  <BarChart3 className="h-6 w-6 text-white" />
                </div>
                <h2 className="text-2xl font-bold text-slate-900">
                  Understanding xG & xA
                </h2>
              </div>
              <p className="mb-4 text-slate-700">
                Expected Goals (xG) and Expected Assists (xA) are advanced
                football metrics that quantify the quality of scoring chances and
                key passes. They help evaluate player performance beyond
                traditional stats.
              </p>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
                <div className="rounded-xl border border-slate-200 bg-white p-5">
                  <div className="mb-3 flex items-center">
                    <Target className="h-5 w-5 text-emerald-600" />
                    <h3 className="ml-3 font-semibold text-slate-900">
                      Expected Goals (xG)
                    </h3>
                  </div>
                  <p className="text-sm text-slate-600">
                    Measures the probability that a shot will result in a goal,
                    based on factors like distance, angle, and assist type. A
                    higher xG indicates better scoring opportunities created.
                  </p>
                </div>
                <div className="rounded-xl border border-slate-200 bg-white p-5">
                  <div className="mb-3 flex items-center">
                    <Zap className="h-5 w-5 text-amber-500" />
                    <h3 className="ml-3 font-semibold text-slate-900">
                      Expected Assists (xA)
                    </h3>
                  </div>
                  <p className="text-sm text-slate-600">
                    Estimates the likelihood that a pass becomes a goal assist.
                    It reflects the quality of a player's creative passing,
                    independent of whether teammates finish the chance.
                  </p>
                </div>
                <div className="rounded-xl border border-slate-200 bg-white p-5">
                  <div className="mb-3 flex items-center">
                    <TrendingUp className="h-5 w-5 text-cyan-600" />
                    <h3 className="ml-3 font-semibold text-slate-900">
                      Performance Insight
                    </h3>
                  </div>
                  <p className="text-sm text-slate-600">
                    Comparing actual goals/assists with xG/xA reveals
                    over‑ or under‑performance. A player scoring more goals than
                    xG is finishing exceptionally well.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Player Table */}
        <div className="mb-16">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-3xl font-bold text-slate-900">
              Top Performers
            </h2>
            <div className="text-sm text-slate-500">
              Data sourced from Advanced Analytics Engine
            </div>
          </div>
          <PlayerTable players={players} />
        </div>

        {/* Additional Notes */}
        <div className="rounded-lg border border-slate-300 bg-slate-50 p-6">
          <h3 className="mb-3 text-lg font-semibold text-slate-900">
            How to Interpret the Table
          </h3>
          <ul className="list-disc space-y-2 pl-5 text-slate-700">
            <li>
              <span className="font-medium">Rank</span> is determined by total
              xG + xA, reflecting overall offensive contribution.
            </li>
            <li>
              <span className="font-medium">Overperforming</span> indicates a
              player is scoring/assisting more than expected (actual greater than expected).
            </li>
            <li>
              <span className="font-medium">Underperforming</span> suggests a
              player is converting chances below expectation (actual less than expected).
            </li>
            <li>
              <span className="font-medium">Total (xG + xA)</span> is a
              comprehensive metric combining a player's threat in both finishing
              and creation.
            </li>
          </ul>
          <div className="mt-6 text-sm text-slate-500">
            <p>
              Note: This leaderboard now uses live data from the backend scraping pipeline.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
