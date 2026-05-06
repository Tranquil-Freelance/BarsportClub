"use client";

import { Database, Users, Calendar, Activity, CheckCircle, AlertCircle } from "lucide-react";

export default function DatabaseStatus() {
  const stats = [
    {
      label: "Total Matches Scraped",
      value: "380",
      description: "From Serie A & Premier League",
      icon: <Database className="h-6 w-6 text-emerald-400" />,
      color: "from-emerald-900/40 to-emerald-950/40",
      border: "border-emerald-800/50",
      trend: "+12 today",
    },
    {
      label: "Players in DB",
      value: "542",
      description: "Active player profiles",
      icon: <Users className="h-6 w-6 text-cyan-400" />,
      color: "from-cyan-900/40 to-cyan-950/40",
      border: "border-cyan-800/50",
      trend: "+5 new",
    },
    {
      label: "Last Scrape",
      value: "Today, 03:00 AM",
      description: "Cronjob (Data API)",
      icon: <Calendar className="h-6 w-6 text-amber-400" />,
      color: "from-amber-900/40 to-amber-950/40",
      border: "border-amber-800/50",
      trend: "On schedule",
    },
    {
      label: "Database Status",
      value: "Healthy",
      description: "PostgreSQL 15.3",
      icon: (
        <div className="relative">
          <div className="absolute h-6 w-6 rounded-full bg-emerald-500/30 animate-ping" />
          <CheckCircle className="h-6 w-6 text-emerald-400 relative" />
        </div>
      ),
      color: "from-slate-900/40 to-slate-950/40",
      border: "border-slate-800/50",
      trend: "All systems operational",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
          <Activity className="h-6 w-6 text-cyan-400" />
          Database Health & Statistics
        </h2>
        <p className="mt-2 text-slate-400">
          Real‑time overview of PostgreSQL metrics and scraping volume.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className={`rounded-2xl border ${stat.border} bg-gradient-to-br ${stat.color} p-6 backdrop-blur-sm transition-all hover:scale-[1.02] hover:shadow-2xl`}
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-400">{stat.label}</p>
                <p className="mt-2 text-3xl font-bold text-white">{stat.value}</p>
                <p className="mt-1 text-sm text-slate-300">{stat.description}</p>
                <div className="mt-3 flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-emerald-500" />
                  <span className="text-xs font-medium text-slate-400">{stat.trend}</span>
                </div>
              </div>
              <div className="rounded-lg bg-slate-900/80 p-3">
                {stat.icon}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Additional Metrics */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-white">Storage Usage</h3>
              <p className="mt-1 text-sm text-slate-400">PostgreSQL data directory</p>
            </div>
            <div className="text-2xl font-bold text-emerald-400">18%</div>
          </div>
          <div className="mt-4 h-2 w-full rounded-full bg-slate-800">
            <div className="h-full w-1/5 rounded-full bg-gradient-to-r from-emerald-500 to-cyan-500" />
          </div>
          <p className="mt-2 text-xs text-slate-500">2.1 GB / 12 GB used</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-white">Cache Hit Rate</h3>
              <p className="mt-1 text-sm text-slate-400">Query performance</p>
            </div>
            <div className="text-2xl font-bold text-cyan-400">98.7%</div>
          </div>
          <div className="mt-4 h-2 w-full rounded-full bg-slate-800">
            <div className="h-full w-98/100 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500" />
          </div>
          <p className="mt-2 text-xs text-slate-500">Excellent</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-white">Replication Lag</h3>
              <p className="mt-1 text-sm text-slate-400">Primary ↔ Replica</p>
            </div>
            <div className="text-2xl font-bold text-emerald-400">0 ms</div>
          </div>
          <div className="mt-4 flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-sm text-slate-300">Synchronized</span>
          </div>
          <p className="mt-2 text-xs text-slate-500">No lag detected</p>
        </div>
      </div>

      {/* Health Alerts */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-6">
        <h3 className="text-lg font-bold text-white flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-amber-400" />
          System Health Alerts
        </h3>
        <p className="mt-2 text-slate-400">No critical issues detected. All services are running normally.</p>
        <div className="mt-4 flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-emerald-500" />
            <span className="text-sm text-slate-300">Scraper API</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-emerald-500" />
            <span className="text-sm text-slate-300">Database Connections</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-emerald-500" />
            <span className="text-sm text-slate-300">Queue Workers</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-amber-500" />
            <span className="text-sm text-slate-300">Backup (pending)</span>
          </div>
        </div>
      </div>
    </div>
  );
}