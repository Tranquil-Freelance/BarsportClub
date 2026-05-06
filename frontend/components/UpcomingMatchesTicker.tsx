"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { fetcher } from "@/app/lib/apiClient";

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

/* ─── Helpers ───────────────────────────────────────────────────────── */

function formatMatchDate(iso: string | null): string {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    const day = d.toLocaleDateString("it-IT", { day: "2-digit", month: "short" });
    const time = d.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });
    return `${day} ${time}`;
  } catch {
    return "";
  }
}

/* ─── Navbar Dropdown Component ─────────────────────────────────────── */

interface Props {
  /** Optional className for the outer container */
  className?: string;
}

export default function UpcomingMatchesTicker({ className = "" }: Props) {
  const [matches, setMatches] = useState<UpcomingMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetcher<UpcomingResponse>("/matches/upcoming?limit=20")
      .then((data) => {
        setMatches(data.matches ?? []);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load upcoming matches:", err);
        setLoading(false);
      });
  }, []);

  /* Close dropdown on outside click */
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  /* ── Silent while loading/empty — no UI pollution ─────────────────── */
  if (loading || matches.length === 0) return null;

  return (
    <div ref={dropdownRef} className={`relative ${className}`}>
      {/* Trigger button */}
      <button
        onClick={() => setOpen((v) => !v)}
        onMouseEnter={() => setOpen(true)}
        className="relative py-7 text-sm font-bold tracking-widest uppercase transition-all duration-300 transform hover:-translate-y-0.5 text-[#FF2A6D] hover:text-white flex items-center gap-1.5"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-[#FF2A6D] animate-pulse" />
        NEXT
      </button>

      {/* Dropdown panel */}
      {open && (
        <div
          onMouseEnter={() => setOpen(true)}
          onMouseLeave={() => setOpen(false)}
          className="absolute top-full left-1/2 -translate-x-1/2 mt-0 w-80 bg-[#0a192f] border border-slate-800 rounded-sm shadow-2xl z-50 max-h-96 overflow-y-auto"
        >
          <div className="p-1.5">
            {matches.slice(0, 10).map((match) => (
              <Link
                key={match.id}
                href={`/match/${match.id}`}
                className="flex items-center gap-2 px-3 py-2.5 rounded-sm hover:bg-slate-800/60 transition-colors duration-150 group"
              >
                {/* League badge */}
                <span className="text-[6px] font-black uppercase tracking-wider text-slate-500 border border-slate-700 px-1.5 py-0.5 rounded-sm flex-shrink-0">
                  {match.league}
                </span>

                {/* Teams */}
                <span className="text-xs font-bold text-white group-hover:text-[#FF2A6D] transition-colors truncate">
                  {match.home_team}
                </span>
                <span className="text-[8px] font-black text-slate-500 mx-1">VS</span>
                <span className="text-xs font-bold text-white group-hover:text-[#FF2A6D] transition-colors truncate">
                  {match.away_team}
                </span>

                {/* Date */}
                <span className="text-[8px] font-bold text-slate-400 ml-auto tabular-nums flex-shrink-0">
                  {formatMatchDate(match.date)}
                </span>
              </Link>
            ))}
          </div>

          {/* View all link */}
          {matches.length > 10 && (
            <Link
              href="/campionati"
              className="block text-center text-[7px] font-black uppercase tracking-wider text-slate-500 hover:text-white border-t border-slate-800 py-2 transition-colors duration-150"
            >
              +{matches.length - 10} more matches
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
