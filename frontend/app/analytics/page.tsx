import PlayerRadar from '@/app/components/charts/PlayerRadar';
import EfficiencyScatter from '@/app/components/charts/EfficiencyScatter';
import { getPlayerRadarData, getEfficiencyScatterData, RadarDataPoint, ScatterDataPoint } from '../services/statsService';

export default async function AnalyticsPage() {
  let radarData: RadarDataPoint[] = [];
  let scatterData: ScatterDataPoint[] = [];
  let error: string | null = null;

  try {
    [radarData, scatterData] = await Promise.all([
      getPlayerRadarData(),
      getEfficiencyScatterData(),
    ]);
  } catch (err) {
    console.error('Failed to fetch analytics data:', err);
    error = 'Unable to load chart data at this time. Please ensure the backend is running.';
  }

  // Fallback UI for errors
  if (error) {
    return (
      <div className="min-h-screen bg-[#F8FAFC] p-4 md:p-8">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-[#0F172A]">
            Advanced Metrics – Visualizing Performance
          </h1>
          <p className="mt-2 text-lg text-slate-600">
            Interactive radar charts and scatter plots to dissect player profiles and league‑wide efficiency.
          </p>
        </header>
        <div className="rounded-2xl border border-rose-800 bg-rose-900/20 p-8 text-center">
          <h2 className="text-2xl font-bold text-rose-300 mb-4">Data Unavailable</h2>
          <p className="text-slate-300 mb-6">{error}</p>
          <div className="text-sm text-slate-400">
            Backend endpoint: <code className="bg-slate-800 px-2 py-1 rounded">http://localhost:8000</code>
          </div>
        </div>
      </div>
    );
  }

  // Fallback if data arrays are empty
  const hasRadarData = radarData && radarData.length > 0;
  const hasScatterData = scatterData && scatterData.length > 0;

  return (
    <div className="min-h-screen bg-[#F8FAFC] p-4 md:p-8">
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-[#0F172A]">
          Advanced Metrics – Visualizing Performance
        </h1>
        <p className="mt-2 text-lg text-slate-600">
          Interactive radar charts and scatter plots to dissect player profiles and league‑wide efficiency.
        </p>
        <div className="mt-4 flex items-center gap-4">
          <div className="h-1 w-24 rounded-full bg-gradient-to-r from-emerald-500 to-cyan-500"></div>
          <span className="text-sm text-slate-500">Emerald/Slate Design System</span>
        </div>
      </header>

      {/* Main content grid */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        {/* Left column: Player Radar */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-2xl">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-slate-200">Individual Player Profile</h2>
            <span className="rounded-full bg-emerald-900/50 px-3 py-1 text-sm font-medium text-emerald-300">
              Percentile Ranks
            </span>
          </div>
          <p className="mb-6 text-slate-400">
            Radar visualization of a player’s percentile ranks across eight key performance indicators.
            Higher values indicate stronger relative performance within the league.
          </p>
          {hasRadarData ? (
            <PlayerRadar data={radarData} />
          ) : (
            <div className="h-96 flex items-center justify-center rounded-xl border border-slate-800 bg-slate-900/50">
              <p className="text-slate-500">No radar data available.</p>
            </div>
          )}
          <div className="mt-6 flex flex-wrap gap-4 text-sm text-slate-500">
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-emerald-500/40"></div>
              <span>Non‑Penalty xG, xA, Shots, Key Passes, Touches in Box, Progressive Passes, Successful Dribbles, Defensive Actions</span>
            </div>
          </div>
        </section>

        {/* Right column: Efficiency Scatter */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-2xl">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-slate-200">League‑Wide xG Efficiency</h2>
            <span className="rounded-full bg-rose-900/50 px-3 py-1 text-sm font-medium text-rose-300">
              Over‑/Under‑Performance
            </span>
          </div>
          <p className="mb-6 text-slate-400">
            Scatter plot comparing Expected Goals (xG) vs Actual Goals for a sample of league players.
            The diagonal line (y = x) represents parity; points above indicate over‑performance.
          </p>
          {hasScatterData ? (
            <EfficiencyScatter data={scatterData} />
          ) : (
            <div className="h-96 flex items-center justify-center rounded-xl border border-slate-800 bg-slate-900/50">
              <p className="text-slate-500">No scatter plot data available.</p>
            </div>
          )}
          <div className="mt-6 grid grid-cols-1 gap-4 text-sm text-slate-500 sm:grid-cols-2">
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-emerald-500"></div>
              <span>League average performers</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-rose-500"></div>
              <span>Highlighted star (over‑performing)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full border border-slate-500"></div>
              <span>Parity line y = x</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full border border-dashed border-cyan-500"></div>
              <span>Reference line for comparison</span>
            </div>
          </div>
        </section>
      </div>

      {/* Footer notes */}
      <div className="mt-12 rounded-xl border border-slate-800 bg-slate-900/50 p-6">
        <h3 className="text-xl font-semibold text-slate-300">How to Interpret These Charts</h3>
        <div className="mt-4 grid grid-cols-1 gap-6 md:grid-cols-3">
          <div className="space-y-3">
            <h4 className="font-medium text-emerald-400">Radar Chart</h4>
            <p className="text-sm text-slate-400">
              Each axis represents a normalized metric (0‑100 percentile). A larger shaded area indicates a more complete player profile.
            </p>
          </div>
          <div className="space-y-3">
            <h4 className="font-medium text-rose-400">Scatter Plot</h4>
            <p className="text-sm text-slate-400">
              Points above the diagonal line indicate players scoring more goals than expected (over‑performers). Points below indicate under‑performers.
            </p>
          </div>
          <div className="space-y-3">
            <h4 className="font-medium text-cyan-400">Data Sources</h4>
            <p className="text-sm text-slate-400">
              All metrics are sourced from our proprietary pipeline, updated daily. Real data is now fetched from the backend.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}