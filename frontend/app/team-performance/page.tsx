import { getTeamPerformanceMetrics, TeamPerformanceMetric } from '../services/statsService';

export default async function TeamPerformancePage() {
  let metrics: TeamPerformanceMetric[] = [];
  let error: string | null = null;

  try {
    metrics = await getTeamPerformanceMetrics();
  } catch (err) {
    console.error('Failed to fetch team performance metrics:', err);
    error = 'Unable to load team performance data at this time. Please ensure the backend is running.';
  }

  // Fallback UI for errors
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-950 p-4 md:p-8">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-slate-100">
            Team Performance Analytics
          </h1>
          <p className="mt-2 text-lg text-slate-400">
            Advanced metrics for evaluating team strength, shot quality, attacking efficiency, and more.
          </p>
        </header>
        <div className="rounded-2xl border border-rose-800 bg-rose-900/20 p-8 text-center">
          <h2 className="text-2xl font-bold text-rose-300 mb-4">Data Unavailable</h2>
          <p className="text-slate-300 mb-6">{error}</p>
          <div className="text-sm text-slate-400">
            Backend endpoint: <code className="bg-slate-800 px-2 py-1 rounded">http://localhost:8000/api/v1/team-performance</code>
          </div>
        </div>
      </div>
    );
  }

  // If no data
  if (metrics.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-950 p-4 md:p-8">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-slate-100">
            Team Performance Analytics
          </h1>
          <p className="mt-2 text-lg text-slate-400">
            Advanced metrics for evaluating team strength, shot quality, attacking efficiency, and more.
          </p>
        </header>
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8 text-center">
          <h2 className="text-2xl font-bold text-slate-300 mb-4">No Data Available</h2>
          <p className="text-slate-400">No team performance metrics found for the selected league and season.</p>
        </div>
      </div>
    );
  }

  // Helper to format numbers
  const fmt = (value: number, decimals: number = 3) =>
    value.toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-950 p-4 md:p-8">
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-slate-100">
          Team Performance Analytics
        </h1>
        <p className="mt-2 text-lg text-slate-400">
          Advanced metrics for evaluating team strength, shot quality, attacking efficiency, and more.
        </p>
        <div className="mt-4 flex items-center gap-4">
          <div className="h-1 w-24 rounded-full bg-gradient-to-r from-emerald-500 to-cyan-500"></div>
          <span className="text-sm text-slate-500">Football Analytics Platform – Macro‑Area 1</span>
        </div>
      </header>

      {/* Metrics table */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-2xl mb-8">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-slate-200">Team Performance Metrics</h2>
          <span className="rounded-full bg-emerald-900/50 px-3 py-1 text-sm font-medium text-emerald-300">
            Season 2025/26
          </span>
        </div>
        <p className="mb-6 text-slate-400">
          The table below shows the seven core metrics defined in the Football Analytics Platform Technical Design Document.
          Each metric is calculated from raw data (xG, shots, key passes, etc.) and normalized for cross‑team comparison.
        </p>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[1200px] text-sm text-left text-slate-300">
            <thead className="text-xs uppercase bg-slate-800/80 text-slate-400">
              <tr>
                <th scope="col" className="px-6 py-4 sticky left-0 bg-slate-900/95">Team</th>
                <th scope="col" className="px-6 py-4">True Team Strength (TTS)</th>
                <th scope="col" className="px-6 py-4">Shot Quality Differential (SQD)</th>
                <th scope="col" className="px-6 py-4">Attacking Efficiency (AE)</th>
                <th scope="col" className="px-6 py-4">Possession Danger Index (PDI)</th>
                <th scope="col" className="px-6 py-4">Threat Creation Index (TCI)</th>
                <th scope="col" className="px-6 py-4">Squad Architecture Score (SAS)</th>
                <th scope="col" className="px-6 py-4">Danger Flow Index (DFI)</th>
                <th scope="col" className="px-6 py-4">Matches</th>
                <th scope="col" className="px-6 py-4">Goals For</th>
                <th scope="col" className="px-6 py-4">Goals Against</th>
                <th scope="col" className="px-6 py-4">xG For</th>
                <th scope="col" className="px-6 py-4">xG Against</th>
                <th scope="col" className="px-6 py-4">Shots For</th>
                <th scope="col" className="px-6 py-4">Shots Against</th>
              </tr>
            </thead>
            <tbody>
              {metrics.map((item) => (
                <tr
                  key={item.team}
                  className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors"
                >
                  <td className="px-6 py-4 font-medium text-slate-200 sticky left-0 bg-slate-900/95">
                    {item.team}
                  </td>
                  <td className="px-6 py-4">{fmt(item.metrics.true_team_strength)}</td>
                  <td className="px-6 py-4">{fmt(item.metrics.shot_quality_differential)}</td>
                  <td className="px-6 py-4">{fmt(item.metrics.attacking_efficiency)}</td>
                  <td className="px-6 py-4">{fmt(item.metrics.possession_danger_index)}</td>
                  <td className="px-6 py-4">{fmt(item.metrics.threat_creation_index)}</td>
                  <td className="px-6 py-4">{fmt(item.metrics.squad_architecture_score)}</td>
                  <td className="px-6 py-4">{fmt(item.metrics.danger_flow_index)}</td>
                  <td className="px-6 py-4">{item.raw_data.matches_played}</td>
                  <td className="px-6 py-4">{item.raw_data.goals_for}</td>
                  <td className="px-6 py-4">{item.raw_data.goals_against}</td>
                  <td className="px-6 py-4">{fmt(item.raw_data.xg_for, 2)}</td>
                  <td className="px-6 py-4">{fmt(item.raw_data.xg_against, 2)}</td>
                  <td className="px-6 py-4">{item.raw_data.shots_for}</td>
                  <td className="px-6 py-4">{item.raw_data.shots_against}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-8 text-xs text-slate-500">
          <p>
            <strong>Definitions:</strong> TTS = xG‑xGA (true strength), SQD = (xG/shots) – (xGA/shots_conceded),
            AE = goals/xG, PDI = (shots + key_passes)/xG, TCI = (xgchain + attacks)/shots, SAS = composite of attack/creation/defense,
            DFI = xG per possession + key passes per possession + shots‑in‑area ratio.
          </p>
        </div>
      </section>

      {/* Raw data summary */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-2xl">
        <h3 className="text-xl font-bold text-slate-300 mb-4">Raw Data Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {metrics.slice(0, 4).map((item) => (
            <div
              key={item.team}
              className="rounded-xl border border-slate-800 bg-slate-900/50 p-4"
            >
              <h4 className="font-bold text-slate-200 mb-2">{item.team}</h4>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">Matches</span>
                  <span className="text-slate-300">{item.raw_data.matches_played}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Goals For</span>
                  <span className="text-emerald-400">{item.raw_data.goals_for}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Goals Against</span>
                  <span className="text-rose-400">{item.raw_data.goals_against}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">xG For</span>
                  <span className="text-cyan-400">{fmt(item.raw_data.xg_for, 2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">xG Against</span>
                  <span className="text-amber-400">{fmt(item.raw_data.xg_against, 2)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
        <p className="mt-6 text-sm text-slate-400">
          The raw data above is sourced from the <code className="bg-slate-800 px-1 rounded">TeamSeasonStat</code> and{' '}
          <code className="bg-slate-800 px-1 rounded">PlayerMatchStat</code> tables, aggregated per team per season.
        </p>
      </section>

      {/* Footer notes */}
      <div className="mt-12 rounded-xl border border-slate-800 bg-slate-900/50 p-6">
        <h3 className="text-xl font-semibold text-slate-300">How to Interpret These Metrics</h3>
        <div className="mt-4 grid grid-cols-1 gap-6 md:grid-cols-2">
          <div className="space-y-3">
            <h4 className="font-medium text-emerald-400">True Team Strength (TTS)</h4>
            <p className="text-sm text-slate-400">
              The difference between expected goals for and against. Positive values indicate a team that creates
              higher‑quality chances than it concedes, a robust indicator of underlying performance.
            </p>
          </div>
          <div className="space-y-3">
            <h4 className="font-medium text-rose-400">Attacking Efficiency (AE)</h4>
            <p className="text-sm text-slate-400">
              Ratio of actual goals to expected goals. Values above 1.0 suggest over‑performance in finishing;
              values below 1.0 indicate wastefulness in front of goal.
            </p>
          </div>
          <div className="space-y-3">
            <h4 className="font-medium text-cyan-400">Threat Creation Index (TCI)</h4>
            <p className="text-sm text-slate-400">
              Measures how well a team translates possession into dangerous actions. Combines xGChain, attacks, and
              key passes per shot taken.
            </p>
          </div>
          <div className="space-y-3">
            <h4 className="font-medium text-amber-400">Squad Architecture Score (SAS)</h4>
            <p className="text-sm text-slate-400">
              A composite score reflecting the balance between attack quality, creation diversity, and defensive
              stability. Higher scores denote a well‑rounded squad.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}