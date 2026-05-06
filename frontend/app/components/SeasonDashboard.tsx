"use client";

import {
  Trophy,
  Target,
  Zap,
  Shield,
  BarChart3,
  PieChart,
  TrendingUp,
  Users,
  Clock,
  Crosshair,
} from "lucide-react";
import { SeasonStats, TopPerformer } from "@/app/types/reports";

interface SeasonDashboardProps {
  seasonStats: SeasonStats;
  topPerformers: TopPerformer[];
}

export default function SeasonDashboard({
  seasonStats,
  topPerformers,
}: SeasonDashboardProps) {
  const recordItems = [
    {
      label: "Wins",
      value: seasonStats.wins,
      icon: Trophy,
      color: "bg-emerald-900 border-emerald-700 text-emerald-300",
      bgColor: "bg-emerald-950/30",
    },
    {
      label: "Draws",
      value: seasonStats.draws,
      icon: Shield,
      color: "bg-slate-800 border-slate-600 text-slate-300",
      bgColor: "bg-slate-900/30",
    },
    {
      label: "Losses",
      value: seasonStats.losses,
      icon: Target,
      color: "bg-rose-900 border-rose-700 text-rose-300",
      bgColor: "bg-rose-950/30",
    },
    {
      label: "Clean Sheets",
      value: seasonStats.cleanSheets,
      icon: Zap,
      color: "bg-cyan-900 border-cyan-700 text-cyan-300",
      bgColor: "bg-cyan-950/30",
    },
  ];

  const efficiencyMetrics = [
    {
      title: "Conversion Rate",
      value: seasonStats.conversionRate,
      description: "Shots to Goals",
      icon: Crosshair,
      color: "text-emerald-400",
      border: "border-emerald-800",
      bg: "bg-emerald-950/40",
    },
    {
      title: "xG / Game",
      value: seasonStats.xGPerGame.toFixed(2),
      description: "Expected Goals per match",
      icon: TrendingUp,
      color: "text-cyan-400",
      border: "border-cyan-800",
      bg: "bg-cyan-950/40",
    },
    {
      title: "Shots on Target / Game",
      value: seasonStats.shotsOnTargetPerGame.toFixed(1),
      description: "Average per match",
      icon: BarChart3,
      color: "text-violet-400",
      border: "border-violet-800",
      bg: "bg-violet-950/40",
    },
  ];

  const possessionPercentage = parseFloat(seasonStats.averagePossession);
  const possessionCircumference = 2 * Math.PI * 45; // radius 45
  const possessionStrokeDashoffset =
    possessionCircumference - (possessionPercentage / 100) * possessionCircumference;

  return (
    <div className="w-full space-y-8 p-4 md:p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl md:text-3xl font-bold text-white mb-2">
          Winter Season Performance Dashboard
        </h2>
        <p className="text-slate-400">
          Analytical overview of team metrics and top performers
        </p>
      </div>

      {/* Record Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {recordItems.map((item) => (
          <div
            key={item.label}
            className={`${item.bgColor} rounded-xl border ${item.color} p-5 transition-all duration-300 hover:scale-[1.02] hover:shadow-xl`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-300">{item.label}</p>
                <p className="text-3xl font-bold mt-2">{item.value}</p>
              </div>
              <div className={`p-3 rounded-full ${item.color}`}>
                <item.icon className="h-6 w-6" />
              </div>
            </div>
            <div className="mt-4 h-1 w-full bg-gradient-to-r from-transparent via-current to-transparent opacity-30"></div>
          </div>
        ))}
      </div>

      {/* Efficiency Grid & Control Section */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Efficiency Grid */}
        <div className="lg:col-span-2">
          <div className="mb-4 flex items-center gap-2">
            <PieChart className="h-5 w-5 text-emerald-400" />
            <h3 className="text-xl font-semibold text-white">Efficiency Metrics</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {efficiencyMetrics.map((metric) => (
              <div
                key={metric.title}
                className={`${metric.bg} border ${metric.border} rounded-xl p-5`}
              >
                <div className="flex items-center justify-between mb-3">
                  <metric.icon className={`h-8 w-8 ${metric.color}`} />
                  <span className="text-2xl font-bold text-white">
                    {metric.value}
                  </span>
                </div>
                <h4 className="font-medium text-white mb-1">{metric.title}</h4>
                <p className="text-sm text-slate-400">{metric.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Control Section - Possession */}
        <div className="bg-slate-900/50 border border-slate-700 rounded-xl p-6">
          <div className="mb-4 flex items-center gap-2">
            <Clock className="h-5 w-5 text-cyan-400" />
            <h3 className="text-xl font-semibold text-white">Average Possession</h3>
          </div>
          <div className="flex flex-col items-center justify-center py-4">
            <div className="relative w-48 h-48">
              <svg className="w-full h-full" viewBox="0 0 100 100">
                {/* Background circle */}
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke="#1e293b"
                  strokeWidth="8"
                />
                {/* Progress circle */}
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke="url(#possessionGradient)"
                  strokeWidth="8"
                  strokeDasharray={possessionCircumference}
                  strokeDashoffset={possessionStrokeDashoffset}
                  strokeLinecap="round"
                  transform="rotate(-90 50 50)"
                />
                <defs>
                  <linearGradient id="possessionGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#0d9488" />
                    <stop offset="100%" stopColor="#22d3ee" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-5xl font-bold text-white">
                  {seasonStats.averagePossession}
                </span>
                <span className="text-slate-400 mt-2">Ball Control</span>
              </div>
            </div>
            <p className="text-slate-400 text-center mt-6 max-w-xs">
              The team maintained dominant possession throughout the season, enabling
              sustained attacking pressure.
            </p>
          </div>
        </div>
      </div>

      {/* Top Performers List */}
      <div className="bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 rounded-xl p-6">
        <div className="mb-6 flex items-center gap-2">
          <Users className="h-5 w-5 text-emerald-400" />
          <h3 className="text-xl font-semibold text-white">Top Performers</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {topPerformers.map((performer, idx) => (
            <div
              key={idx}
              className="bg-slate-800/40 hover:bg-slate-800/70 border border-slate-700 rounded-lg p-4 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-white">{performer.name}</h4>
                  <p className="text-sm text-slate-400">{performer.metric}</p>
                </div>
                <div className="text-2xl font-bold text-emerald-400">
                  {typeof performer.value === "number"
                    ? performer.value.toFixed(2)
                    : performer.value}
                </div>
              </div>
              <div className="mt-3 h-1 w-full bg-gradient-to-r from-emerald-500/30 to-transparent rounded-full"></div>
            </div>
          ))}
        </div>
        {topPerformers.length === 0 && (
          <p className="text-slate-500 text-center py-8">
            No performer data available.
          </p>
        )}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div className="bg-slate-900/30 border border-slate-800 rounded-lg p-4">
          <p className="text-slate-400">Matches Played</p>
          <p className="text-2xl font-bold text-white">{seasonStats.matchesPlayed}</p>
        </div>
        <div className="bg-slate-900/30 border border-slate-800 rounded-lg p-4">
          <p className="text-slate-400">Goals Scored</p>
          <p className="text-2xl font-bold text-white">{seasonStats.goalsScored}</p>
        </div>
        <div className="bg-slate-900/30 border border-slate-800 rounded-lg p-4">
          <p className="text-slate-400">Goals Conceded</p>
          <p className="text-2xl font-bold text-white">{seasonStats.goalsConceded}</p>
        </div>
        <div className="bg-slate-900/30 border border-slate-800 rounded-lg p-4">
          <p className="text-slate-400">Goal Difference</p>
          <p className="text-2xl font-bold text-white">
            {seasonStats.goalsScored - seasonStats.goalsConceded}
          </p>
        </div>
      </div>
    </div>
  );
}