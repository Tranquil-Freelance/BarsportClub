import type { Metadata } from "next";
import ScraperPanel from "@/app/components/admin/ScraperPanel";
import DatabaseStatus from "@/app/components/admin/DatabaseStatus";

export const metadata: Metadata = {
  title: "Command Center - xPalermoStat Admin",
  description: "Admin dashboard for managing Python FastAPI scraper and monitoring PostgreSQL database",
};

export default function AdminPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white">xPalermoStat Data Command Center</h1>
        <p className="mt-2 text-slate-400">
          Administrative hub for managing the data extraction pipeline and monitoring database health.
        </p>
      </div>

      {/* Database Status at the top */}
      <DatabaseStatus />

      {/* Scraper Panel below */}
      <ScraperPanel />

      {/* Info Panel */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-8">
        <h3 className="text-xl font-bold text-white flex items-center gap-3">
          <svg
            className="h-5 w-5 text-cyan-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          System Notes
        </h3>
        <p className="mt-2 text-slate-400">
          This dashboard is strictly for managing the Python FastAPI scraper (advanced analytics data extraction) and monitoring the PostgreSQL database.
          <strong className="block mt-2 text-amber-300">NO exercises or coach portals.</strong>
        </p>
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
            <div className="flex items-center gap-3">
              <div className="h-3 w-3 rounded-full bg-emerald-500" />
              <span className="font-medium text-white">Scraper API Endpoint</span>
            </div>
            <p className="mt-3 text-sm text-slate-400">http://localhost:8000/api/v1/scraper/trigger</p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
            <div className="flex items-center gap-3">
              <div className="h-3 w-3 rounded-full bg-cyan-500" />
              <span className="font-medium text-white">Database Connection</span>
            </div>
            <p className="mt-3 text-sm text-slate-400">PostgreSQL 15.3 on localhost:5432/xpalermostat</p>
          </div>
        </div>
      </div>
    </div>
  );
}