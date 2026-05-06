import { Target, Trophy, TrendingUp, Users, Zap, BarChart3, Shield } from "lucide-react";
import PlayerRadarPink from "./components/PlayerRadarPink";
import EfficiencyScatterPink from "./components/EfficiencyScatterPink";

export default function PalermoHubPage() {
  // Mock key metrics for Palermo
  const keyMetrics = [
    {
      title: "Expected Points (xPTS)",
      value: "42.7",
      change: "+2.3",
      icon: <Target className="h-8 w-8 text-pink-500" />,
      color: "from-pink-600 to-rose-800",
      description: "Projected points based on xG/xGA",
    },
    {
      title: "Top xG Creator",
      value: "Matteo Brunori",
      change: "9.8 xG",
      icon: <Zap className="h-8 w-8 text-pink-400" />,
      color: "from-pink-500 to-pink-800",
      description: "Leads squad in expected goals",
    },
    {
      title: "Defensive Solidity",
      value: "68%",
      change: "+5%",
      icon: <Shield className="h-8 w-8 text-pink-300" />,
      color: "from-pink-700 to-purple-900",
      description: "Ball‑recovery success rate",
    },
    {
      title: "Avg Possession",
      value: "54.2%",
      change: "-1.1%",
      icon: <TrendingUp className="h-8 w-8 text-pink-200" />,
      color: "from-pink-800 to-black",
      description: "Season‑long possession average",
    },
    {
      title: "Shot Efficiency",
      value: "12.3%",
      change: "+0.8%",
      icon: <BarChart3 className="h-8 w-8 text-pink-600" />,
      color: "from-pink-900 to-rose-950",
      description: "Shots on target / total shots",
    },
    {
      title: "Squad Depth",
      value: "24",
      change: "2 injuries",
      icon: <Users className="h-8 w-8 text-pink-700" />,
      color: "from-black to-pink-950",
      description: "Available senior players",
    },
  ];

  const upcomingMatches = [
    { opponent: "Parma", competition: "Serie B", date: "Mar 15", venue: "A" },
    { opponent: "Venezia", competition: "Serie B", date: "Mar 22", venue: "H" },
    { opponent: "Como", competition: "Serie B", date: "Apr 5", venue: "A" },
    { opponent: "Cagliari", competition: "Coppa Italia", date: "Apr 12", venue: "H" },
  ];

  return (
    <div className="space-y-10">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-2xl border border-pink-800 bg-gradient-to-br from-black via-zinc-950 to-pink-950 p-8 md:p-12 text-white shadow-2xl">
        <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-pink-900/20 blur-3xl" />
        <div className="absolute -left-20 bottom-0 h-48 w-48 rounded-full bg-pink-800/10 blur-3xl" />
        <div className="relative z-10">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-8">
            <div>
              <div className="inline-flex items-center gap-3 rounded-full border border-pink-700 bg-pink-900/30 px-5 py-2 mb-6">
                <Trophy className="h-5 w-5 text-pink-300" />
                <span className="text-sm font-medium text-pink-200">Serie B 2025‑26</span>
              </div>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight">
                <span className="bg-gradient-to-r from-pink-500 via-pink-400 to-pink-300 bg-clip-text text-transparent">
                  Palermo FC
                </span>
                <br />
                <span className="text-white">Analytics Hub</span>
              </h1>
              <p className="mt-4 max-w-2xl text-lg text-pink-100">
                Real‑time performance metrics, advanced xG breakdowns, and tactical insights
                dedicated to the Rosanero. Everything you need to understand the club’s season.
              </p>
              <div className="mt-8 flex flex-wrap gap-4">
                <button className="rounded-full bg-gradient-to-r from-pink-600 to-pink-800 px-6 py-3 font-semibold text-white shadow-lg hover:from-pink-700 hover:to-pink-900 transition-all hover:scale-105">
                  Explore Squad
                </button>
                <button className="rounded-full border border-pink-700 bg-transparent px-6 py-3 font-semibold text-pink-300 hover:bg-pink-900/30 transition-colors">
                  Download Data Report
                </button>
                <button className="rounded-full border border-zinc-700 bg-zinc-900/50 px-6 py-3 font-semibold text-zinc-300 hover:bg-zinc-800 transition-colors">
                  Compare with Rivals
                </button>
              </div>
            </div>
            <div className="md:w-1/3">
              <div className="rounded-2xl border border-pink-900 bg-black/50 p-6 backdrop-blur">
                <h3 className="mb-4 text-xl font-bold text-white">Quick Snapshot</h3>
                <ul className="space-y-4">
                  <li className="flex items-center justify-between border-b border-pink-900/30 pb-3">
                    <span className="text-pink-300">Current Position</span>
                    <span className="text-2xl font-bold text-white">3rd</span>
                  </li>
                  <li className="flex items-center justify-between border-b border-pink-900/30 pb-3">
                    <span className="text-pink-300">Points</span>
                    <span className="text-2xl font-bold text-white">52</span>
                  </li>
                  <li className="flex items-center justify-between border-b border-pink-900/30 pb-3">
                    <span className="text-pink-300">Goal Difference</span>
                    <span className="text-2xl font-bold text-green-400">+18</span>
                  </li>
                  <li className="flex items-center justify-between">
                    <span className="text-pink-300">Next Match</span>
                    <span className="text-lg font-bold text-white">vs Parma</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Key Metrics Grid */}
      <section>
        <h2 className="mb-6 text-3xl font-bold text-white">
          Club <span className="text-pink-500">KPIs</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {keyMetrics.map((metric, idx) => (
            <div
              key={idx}
              className={`relative rounded-2xl border border-pink-900/50 bg-gradient-to-br ${metric.color} p-6 text-white overflow-hidden`}
            >
              <div className="absolute -right-6 -top-6 h-20 w-20 rounded-full bg-white/5" />
              <div className="flex items-start justify-between">
                <div>
                  <div className="mb-4">{metric.icon}</div>
                  <h3 className="text-xl font-bold">{metric.title}</h3>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-3xl font-extrabold">{metric.value}</span>
                    <span className="rounded-full bg-pink-900/50 px-3 py-1 text-sm font-medium text-pink-200">
                      {metric.change}
                    </span>
                  </div>
                </div>
              </div>
              <p className="mt-4 text-sm text-pink-200/80">{metric.description}</p>
              <div className="mt-6 h-1 w-full rounded-full bg-pink-900/30">
                <div
                  className="h-full rounded-full bg-pink-500"
                  style={{ width: `${((idx * 13) % 60) + 40}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Charts Section */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div>
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-3xl font-bold text-white">
              Player <span className="text-pink-500">Radar</span>
            </h2>
            <div className="rounded-full border border-pink-800 bg-pink-950/30 px-4 py-2 text-sm font-medium text-pink-300">
              Palermo Edition
            </div>
          </div>
          <PlayerRadarPink />
        </div>
        <div>
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-3xl font-bold text-white">
              Efficiency <span className="text-pink-500">Scatter</span>
            </h2>
            <div className="rounded-full border border-pink-800 bg-pink-950/30 px-4 py-2 text-sm font-medium text-pink-300">
              xG vs Goals
            </div>
          </div>
          <EfficiencyScatterPink />
        </div>
      </section>

      {/* Upcoming Fixtures */}
      <section className="rounded-2xl border border-pink-900/30 bg-black/30 p-8">
        <h2 className="mb-6 text-3xl font-bold text-white">
          Upcoming <span className="text-pink-500">Fixtures</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {upcomingMatches.map((match, idx) => (
            <div
              key={idx}
              className="rounded-xl border border-pink-900/40 bg-gradient-to-br from-zinc-900 to-black p-6 hover:border-pink-700 transition-colors"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="rounded-full border border-pink-800 bg-pink-950/30 p-2">
                  <Trophy className="h-5 w-5 text-pink-400" />
                </div>
                <span className="text-sm font-medium text-pink-300">{match.competition}</span>
              </div>
              <h3 className="text-2xl font-bold text-white">{match.opponent}</h3>
              <div className="mt-4 flex items-center justify-between text-sm text-pink-300">
                <div className="flex items-center gap-2">
                  <span className={`inline-block h-3 w-3 rounded-full ${match.venue === 'H' ? 'bg-pink-500' : 'bg-zinc-600'}`} />
                  <span>{match.venue === 'H' ? 'Home' : 'Away'}</span>
                </div>
                <span className="font-semibold">{match.date}</span>
              </div>
              <button className="mt-6 w-full rounded-lg border border-pink-800 bg-pink-900/20 py-2 text-sm font-medium text-pink-300 hover:bg-pink-900/40 transition-colors">
                View Detailed Preview
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <div className="rounded-2xl border border-pink-800 bg-gradient-to-r from-pink-950/40 to-black p-10 text-center">
        <h3 className="text-3xl font-bold text-white">
          Ready to dive deeper into Palermo’s data?
        </h3>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-pink-200">
          Access full‑season analytics, player‑by‑player breakdowns, and custom report generation.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-6">
          <button className="rounded-full bg-gradient-to-r from-pink-600 to-rose-700 px-8 py-3 font-bold text-white shadow-xl hover:shadow-pink-900/50 hover:scale-105 transition-all">
            Unlock Premium Dashboard
          </button>
          <button className="rounded-full border border-pink-700 bg-transparent px-8 py-3 font-bold text-pink-300 hover:bg-pink-900/30 transition-colors">
            Contact Data Team
          </button>
        </div>
      </div>
    </div>
  );
}