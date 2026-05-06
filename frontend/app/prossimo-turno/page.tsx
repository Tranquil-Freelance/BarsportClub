"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ChevronRight, LayoutDashboard, ExternalLink } from "lucide-react";
import { useTranslation } from "react-i18next";
import "../i18n/config";
import TeamLogo from "../../components/TeamLogo";
import { fetcher } from "@/app/lib/apiClient";
export const dynamic = 'force-dynamic';

/* ─── Types ─────────────────────────────────────────────────────────── */

interface UpcomingMatch {
  id: number;
  date: string | null;
  league: string;
  home_team: string;
  away_team: string;
  round: number | null;
}

interface UpcomingResponse {
  matches: UpcomingMatch[];
  count: number;
}

/* ─── League selector — same as Meritometro ──────────────────────────── */

const LEAGUES = [
  { name: "Serie A", id: "Serie A", logo: "/leagues/seriea.png" },
  { name: "Premier League", id: "Premier League", logo: "/leagues/premierleague.png" },
  { name: "La Liga", id: "La Liga", logo: "/leagues/laliga.png" },
  { name: "Bundesliga", id: "Bundesliga", logo: "/leagues/bundesliga.png" },
  { name: "Ligue 1", id: "Ligue 1", logo: "/leagues/ligue1.png" },
];

/* ─── Helpers ───────────────────────────────────────────────────────── */

function formatMatchSubDate(iso: string | null): string {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    const day = d.toLocaleDateString("it-IT", { day: "2-digit", month: "short", year: "numeric" });
    return day;
  } catch {
    return "";
  }
}

/* ─── Page ──────────────────────────────────────────────────────────── */

export default function ProssimoTurnoPage() {
  const { t } = useTranslation();
  const [activeLeague, setActiveLeague] = useState("Serie A");
  const [matches, setMatches] = useState<UpcomingMatch[]>([]);
  const [loading, setLoading] = useState(true);

  /* Restore saved league */
  useEffect(() => {
    const saved = localStorage.getItem("active_league_barsport_prossimoturno");
    if (saved) setActiveLeague(saved);
  }, []);

  const handleLeagueChange = (leagueId: string) => {
    setActiveLeague(leagueId);
    localStorage.setItem("active_league_barsport_prossimoturno", leagueId);
  };

  /* ── Fetch upcoming matches ────────────────────────────────────── */
  useEffect(() => {
    setLoading(true);
    fetcher<UpcomingResponse>("/matches/upcoming?limit=50")
      .then((data) => {
        setMatches(data.matches ?? []);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load upcoming matches:", err);
        setLoading(false);
      });
  }, []);

  /* Filter by active league */
  const filteredMatches = matches.filter((m) => m.league === activeLeague);

  return (
    <div suppressHydrationWarning className="min-h-screen bg-[#F1F5F9] text-[#1E293B] font-sans pb-20">

      {/* ── LEAGUE SELECTOR — exact copy from Meritometro ──────────── */}
      <div className="w-full bg-white border-b border-slate-200 py-6 px-4 shadow-sm">
        <div className="max-w-[1400px] mx-auto flex justify-start md:justify-center gap-6 md:gap-12 overflow-x-auto no-scrollbar scroll-smooth py-2">
          {LEAGUES.map((l) => (
            <button
              key={l.id}
              onClick={() => handleLeagueChange(l.id)}
              className={`flex flex-col items-center gap-3 min-w-[100px] group transition-all duration-300 ${
                activeLeague === l.id ? "scale-105" : "opacity-40 hover:opacity-100 grayscale hover:grayscale-0"
              }`}
            >
              <div className={`p-3 rounded-2xl bg-slate-50 border-2 transition-all ${
                activeLeague === l.id ? "border-[#FF2A6D] bg-white shadow-lg" : "border-transparent"
              }`}>
                <img
                  src={l.logo}
                  alt={l.name}
                  className="w-10 h-10 md:w-14 md:h-14 object-contain"
                  onError={(e) => {
                    (e.currentTarget as HTMLImageElement).src = "/leagues/default.png";
                  }}
                />
              </div>
              <span className={`text-[10px] font-black uppercase tracking-widest ${
                activeLeague === l.id ? "text-[#0a192f]" : "text-slate-400"
              }`}>{l.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* ── FULL-WIDTH MAIN CONTENT (no sidebar) ──────────────────── */}
      <div className="max-w-[1400px] mx-auto px-4 md:px-8 mt-10">

        {/* Page title */}
        <div className="flex items-center gap-4 mb-10 px-2">
          <h2 className="text-3xl md:text-4xl font-black italic uppercase tracking-tighter text-[#0a192f] flex items-center gap-3">
            Prossimo Turno <ChevronRight className="text-[#FF2A6D]" size={32} /> <span className="text-[#FF2A6D]">{activeLeague}</span>
          </h2>
        </div>

        {loading ? (
          <div className="h-96 flex flex-col items-center justify-center bg-white rounded-3xl border-2 border-dashed border-slate-200 animate-pulse">
            <div className="w-12 h-12 border-4 border-[#FF2A6D] border-t-transparent rounded-full animate-spin mb-4"></div>
            <span className="text-slate-400 font-black uppercase tracking-widest text-[10px]">{t("meritometro.db_loading")}</span>
          </div>
        ) : filteredMatches.length > 0 ? (
          <div className="space-y-8">
            {filteredMatches.map((match) => (
              <div
                key={match.id}
                className="bg-white rounded-3xl shadow-lg border border-slate-200 overflow-hidden group hover:shadow-2xl transition-all duration-300"
              >
                {/* Top accent bar */}
                <div className="h-1.5 bg-gradient-to-r from-[#FF2A6D] to-[#ff5d92]"></div>

                {/* Main card body */}
                <div className="p-8 md:p-10">

                  {/* Round badge */}
                  <div className="flex items-center justify-between mb-6">
                    <span className="bg-slate-100 text-slate-500 text-[9px] font-black px-4 py-1.5 rounded-full uppercase tracking-tighter">
                      {t("meritometro.round")} {match.round ?? "—"}
                    </span>
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                      {match.league}
                    </span>
                  </div>

                  {/* ── Scoreboard area (Meritometro-inspired) ────── */}
                  <Link href={`/match/${match.id}`} className="block">
                    <div className="flex flex-col md:flex-row items-center gap-6 md:gap-12 mb-6">
                      {/* Home team */}
                      <div className="flex flex-col items-center text-center gap-3 md:w-44 flex-shrink-0">
                        <TeamLogo teamName={match.home_team} size={72} />
                        <span className="text-sm md:text-base font-black uppercase text-[#0a192f] leading-tight truncate w-full">
                          {match.home_team}
                        </span>
                      </div>

                      {/* Date/Time + VS scoreboard (Meritometro style) */}
                      <div className="flex-1 flex flex-col items-center justify-center">
                        <div className="flex items-center gap-3 mt-3">
                          <div className="h-px w-12 bg-slate-200"></div>
                          <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">VS</span>
                          <div className="h-px w-12 bg-slate-200"></div>
                        </div>
                        <div className="bg-[#0a192f] text-white text-[8px] font-bold px-4 py-1.5 rounded-full mt-3 uppercase tracking-widest">
                          {formatMatchSubDate(match.date)}
                        </div>
                      </div>

                      {/* Away team */}
                      <div className="flex flex-col items-center text-center gap-3 md:w-44 flex-shrink-0">
                        <TeamLogo teamName={match.away_team} size={72} />
                        <span className="text-sm md:text-base font-black uppercase text-[#0a192f] leading-tight truncate w-full">
                          {match.away_team}
                        </span>
                      </div>
                    </div>
                  </Link>

                  {/* ── Bottom row: AI link + Probabili Formazioni ── */}
                  <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-6 pt-6 border-t border-slate-100">

                    {/* Left: Link to match preview */}
                    <Link
                      href={`/match/${match.id}`}
                      className="group/link flex items-center gap-2 text-[11px] font-black uppercase tracking-widest text-[#FF2A6D] hover:text-[#ff5d92] transition-colors"
                    >
                      <span className="border-b-2 border-transparent group-hover/link:border-[#FF2A6D] transition-all">
                        Analisi & Previsione
                      </span>
                      <ChevronRight size={16} className="transition-transform group-hover/link:translate-x-1" />
                    </Link>

                    {/* Right: 🔍 Probabili Formazioni (Google link) */}
                    <a
                      href={`https://www.google.com/search?q=probabili+formazioni+${encodeURIComponent(match.home_team)}+${encodeURIComponent(match.away_team)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 text-[11px] font-bold uppercase tracking-widest text-slate-400 hover:text-[#FF2A6D] transition-colors border border-slate-200 hover:border-[#FF2A6D]/30 rounded-full px-5 py-2.5 hover:bg-[#FF2A6D]/5"
                    >
                      <span>🔍</span>
                      <span>Probabili Formazioni</span>
                      <ExternalLink size={12} className="opacity-50" />
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white p-20 rounded-3xl border-2 border-slate-100 text-center flex flex-col items-center gap-4">
            <LayoutDashboard size={64} className="text-slate-200" />
            <span className="text-slate-400 font-black uppercase tracking-widest">
              {t("common.no_data")}
            </span>
            <span className="text-xs text-slate-300 font-bold uppercase tracking-wider">
              Nessuna partita imminente per {activeLeague}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
