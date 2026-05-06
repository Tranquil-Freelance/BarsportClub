import SeasonDashboard from "@/app/components/SeasonDashboard";
import { SeasonStats, TopPerformer } from "@/app/types/reports";
import { Brain, Target, Shield, BarChart } from "lucide-react";

export default function ReportPage() {
  // Exact values as per task
  const seasonStats: SeasonStats = {
    matchesPlayed: 18,
    wins: 10,
    draws: 4,
    losses: 4,
    goalsScored: 32,
    goalsConceded: 18,
    cleanSheets: 7,
    xGPerGame: 1.85,
    shotsOnTargetPerGame: 5.2,
    conversionRate: "14%",
    averagePossession: "54%",
  };

  const topPerformers: TopPerformer[] = [
    { name: "Matteo Brunori", metric: "Goals", value: 12 },
    { name: "Jacopo Segre", metric: "Assists", value: 7 },
    { name: "Ivan Marconi", metric: "Pass Accuracy", value: "92%" },
    { name: "Alessandro Aurelio", metric: "Tackles per Game", value: 3.8 },
    { name: "Roberto Crivello", metric: "Key Passes", value: 24 },
    { name: "Leo Štulac", metric: "xA per 90", value: 0.32 },
  ];

  const coachInsights = [
    {
      title: "High xG Creation",
      description:
        "Averaging 1.85 xG per match indicates consistent high‑quality chance generation, though conversion (14%) suggests room for sharper finishing.",
      icon: Target,
      color: "text-emerald-400",
      border: "border-emerald-800",
    },
    {
      title: "Defensive Solidity",
      description:
        "Only 18 goals conceded across 18 matches, with 7 clean sheets, reflects a well‑organized defensive unit that limits opponents’ big chances.",
      icon: Shield,
      color: "text-cyan-400",
      border: "border-cyan-800",
    },
    {
      title: "Possession Dominance",
      description:
        "54% average possession allows controlled build‑up, but a higher tempo in the final third could increase shot volume and conversion.",
      icon: BarChart,
      color: "text-violet-400",
      border: "border-violet-800",
    },
    {
      title: "Set‑Piece Threat",
      description:
        "Set‑piece routines have produced 6 goals this season, accounting for nearly 20% of total output—a key tactical strength.",
      icon: Brain,
      color: "text-amber-400",
      border: "border-amber-800",
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 to-slate-900 text-white">
      {/* Background Grid */}
      <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-5 pointer-events-none" />

      <div className="relative container mx-auto px-4 py-8 md:py-12">
        {/* Page Header */}
        <header className="mb-10">
          <div className="inline-flex items-center gap-3 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-5 py-2 text-sm font-medium text-emerald-300 mb-6">
            <Brain className="h-4 w-4" />
            Analytical Review
          </div>
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-4">
            Winter Season Analytical Review{" "}
            <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
              2025/26
            </span>
          </h1>
          <p className="text-xl text-slate-400 max-w-4xl">
            A comprehensive performance breakdown of Palermo's winter campaign,
            featuring key metrics, player highlights, and tactical insights.
          </p>
        </header>

        {/* Main Dashboard */}
        <section className="mb-12">
          <SeasonDashboard seasonStats={seasonStats} topPerformers={topPerformers} />
        </section>

        {/* Coach Insights */}
        <section className="mb-16">
          <div className="flex items-center gap-3 mb-8">
            <div className="p-2 rounded-lg bg-slate-800/50 border border-slate-700">
              <Brain className="h-6 w-6 text-emerald-400" />
            </div>
            <h2 className="text-3xl font-bold">Coach Insights</h2>
          </div>
          <p className="text-slate-300 mb-8 max-w-4xl text-lg">
            A technical analysis of the season's underlying patterns, strengths, and
            areas for improvement based on the data collected.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {coachInsights.map((insight) => (
              <div
                key={insight.title}
                className={`bg-slate-900/50 border ${insight.border} rounded-xl p-6 hover:bg-slate-900/80 transition-colors`}
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className={`p-2 rounded-lg ${insight.color} bg-opacity-20`}>
                    <insight.icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-xl font-semibold">{insight.title}</h3>
                </div>
                <p className="text-slate-400">{insight.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Key Data Summary */}
        <section className="bg-slate-900/30 border border-slate-800 rounded-2xl p-8 mb-12">
          <h3 className="text-2xl font-bold mb-6">Season at a Glance</h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-5xl font-bold text-emerald-400 mb-2">
                {seasonStats.wins}W‑{seasonStats.draws}D‑{seasonStats.losses}L
              </div>
              <p className="text-slate-400">Record</p>
            </div>
            <div className="text-center">
              <div className="text-5xl font-bold text-cyan-400 mb-2">
                +{seasonStats.goalsScored - seasonStats.goalsConceded}
              </div>
              <p className="text-slate-400">Goal Difference</p>
            </div>
            <div className="text-center">
              <div className="text-5xl font-bold text-violet-400 mb-2">
                {seasonStats.cleanSheets}
              </div>
              <p className="text-slate-400">Clean Sheets</p>
            </div>
            <div className="text-center">
              <div className="text-5xl font-bold text-amber-400 mb-2">
                {seasonStats.averagePossession}
              </div>
              <p className="text-slate-400">Avg. Possession</p>
            </div>
          </div>
          <div className="mt-10 pt-8 border-t border-slate-800">
            <h4 className="text-xl font-semibold mb-4">Interpretation</h4>
            <p className="text-slate-300">
              This winter season saw Palermo achieve a balanced performance with a strong
              defensive record and efficient attacking output. The team's ability to
              control matches (54% possession) while creating high‑value chances (1.85 xG/game)
              demonstrates a well‑executed tactical plan. The conversion rate of 14% indicates
              a slight underperformance relative to expected goals, pointing to a potential
              focus area for the second half of the season. Defensive organization has been a
              standout strength, conceding only one goal per match on average.
            </p>
          </div>
        </section>

        {/* Footer Note */}
        <footer className="text-center text-slate-500 text-sm border-t border-slate-800 pt-8">
          <p>
            Data sourced from internal tracking systems • Report generated on{" "}
            {new Date('2026-02-20').toLocaleDateString("en-US", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </p>
          <p className="mt-2">
            This analytical review is intended for coaching staff and performance analysts.
          </p>
        </footer>
      </div>
    </div>
  );
}