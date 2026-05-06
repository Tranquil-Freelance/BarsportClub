"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
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

/* ─── Component ─────────────────────────────────────────────────────── */

export default function ProssimoTurnoDropdown() {
  const pathname = usePathname();
  const [matches, setMatches] = useState<UpcomingMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

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

  /* Close on outside click */
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  /* Close on Escape */
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open]);

  /* ── Active state: true if any match detail page is open ────────── */
  const isActive = pathname.startsWith("/match/");

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((prev) => !prev)}
        onMouseEnter={() => setOpen(true)}
        aria-haspopup="true"
        aria-expanded={open}
        className={`relative py-7 text-sm font-bold tracking-widest uppercase transition-all duration-300 transform hover:-translate-y-0.5
          ${isActive ? "text-white" : "text-slate-400 hover:text-white"}
        `}
      >
        PROSSIMO TURNO
        {/* Active underline indicator — matches sibling links */}
        {isActive && (
          <span className="absolute bottom-0 left-0 w-full h-1 bg-[#FF2A6D] rounded-t-md shadow-[0_0_10px_#FF2A6D]" />
        )}
      </button>

      {/* ── Dropdown panel ─────────────────────────────────────────── */}
      {open && (
        <div
          onMouseEnter={() => setOpen(true)}
          onMouseLeave={() => setOpen(false)}
          className="absolute left-1/2 -translate-x-1/2 top-full mt-0 w-80 bg-[#0d2137] border border-slate-700 rounded shadow-xl z-50 max-h-96 overflow-y-auto"
        >
          {/* Loading state */}
          {loading && (
            <div className="px-4 py-6 text-center">
              <div className="inline-block w-5 h-5 border-2 border-slate-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-xs text-slate-500 mt-2 font-bold tracking-wider uppercase">
                Caricamento...
              </p>
            </div>
          )}

          {/* Empty state */}
          {!loading && matches.length === 0 && (
            <div className="px-4 py-6 text-center">
              <p className="text-xs text-slate-500 font-bold tracking-wider uppercase">
                Nessuna partita imminente
              </p>
            </div>
          )}

          {/* Match list */}
          {!loading && matches.length > 0 && (
            <div className="py-1">
              {matches.slice(0, 10).map((match) => (
                <Link
                  key={match.id}
                  href={`/match/${match.id}`}
                  onClick={() => setOpen(false)}
                  className="flex items-center gap-2 px-4 py-2.5 hover:bg-slate-800 transition-colors duration-150 group"
                >
                  {/* League badge */}
                  <span className="text-[6px] font-black uppercase tracking-wider text-slate-500 border border-slate-700 px-1.5 py-0.5 rounded-sm flex-shrink-0">
                    {match.league}
                  </span>

                  {/* Teams */}
                  <span className="text-xs font-bold text-slate-200 group-hover:text-[#FF2A6D] transition-colors truncate">
                    {match.home_team}
                  </span>
                  <span className="text-[8px] font-black text-slate-500 mx-0.5">VS</span>
                  <span className="text-xs font-bold text-slate-200 group-hover:text-[#FF2A6D] transition-colors truncate">
                    {match.away_team}
                  </span>

                  {/* Date */}
                  <span className="text-[8px] font-bold text-slate-500 ml-auto tabular-nums flex-shrink-0">
                    {formatMatchDate(match.date)}
                  </span>
                </Link>
              ))}

              {/* "View all" link */}
              {matches.length > 10 && (
                <Link
                  href="/campionati"
                  onClick={() => setOpen(false)}
                  className="block text-center text-[7px] font-black uppercase tracking-wider text-slate-500 hover:text-white border-t border-slate-700 py-2 transition-colors duration-150"
                >
                  +{matches.length - 10} altre partite
                </Link>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
