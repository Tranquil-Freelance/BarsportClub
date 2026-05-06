"use client";

import Link from "next/link";
import { Home, Settings, BarChart3 } from "lucide-react";

export default function AdminHeader() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800 bg-gradient-to-r from-slate-900 to-slate-950 shadow-xl">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Branding */}
          <div className="flex items-center gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-600 to-cyan-500 shadow-lg">
              <Settings className="h-6 w-6 text-white" />
            </div>
            <div className="flex flex-col">
              <Link
                href="/admin"
                className="text-xl font-bold tracking-tight text-white hover:text-emerald-300 transition-colors"
              >
                xPalermoStat{" "}
                <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                  Admin
                </span>
              </Link>
              <span className="mt-0.5 text-xs font-medium text-slate-400">
                Scraper Control Panel & Dashboard
              </span>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex items-center space-x-4">
            <Link
              href="/"
              className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-2.5 text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-white hover:border-emerald-600 transition-all duration-200"
            >
              <Home className="h-4 w-4" />
              Back to Site
            </Link>
            <Link
              href="/admin"
              className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-emerald-600 to-cyan-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg hover:from-emerald-500 hover:to-cyan-500 hover:shadow-emerald-500/25 transition-all duration-300"
            >
              <BarChart3 className="h-4 w-4" />
              Scraper Dashboard
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
}