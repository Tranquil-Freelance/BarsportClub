"use client";

import React, { useEffect, useState } from "react";

/* ─── Types ──────────────────────────────────────────────────────────── */

interface RosterPlayer {
  name: string;
  position?: string;
  goals: number;
  yellow_cards: number;
  red_cards: number;
  subbed_off?: boolean;
  sub_minute?: number | null;
  came_on?: boolean;
  came_on_minute?: number | null;
}

interface TeamRoster {
  team_name: string;
  formation: string;
  starters: RosterPlayer[];
  substitutes: RosterPlayer[];
}

interface LineupResponse {
  home: TeamRoster | null;
  away: TeamRoster | null;
  error?: string;
}

/* ─── Event Icons ────────────────────────────────────────────────────── */

function EventIcons({ player }: { player: RosterPlayer }) {
  const icons: React.ReactNode[] = [];

  for (let i = 0; i < player.goals; i++) {
    icons.push(<span key={`g-${i}`}>⚽</span>);
  }
  for (let i = 0; i < player.yellow_cards; i++) {
    icons.push(<span key={`yc-${i}`}>🟨</span>);
  }
  for (let i = 0; i < player.red_cards; i++) {
    icons.push(<span key={`rc-${i}`}>🟥</span>);
  }

  if (icons.length === 0) return null;
  return <span className="flex gap-0.5 items-center">{icons}</span>;
}

/* ─── Single Team Column ─────────────────────────────────────────────── */

function TeamColumn({ team }: { team: TeamRoster }) {
  const { starters, substitutes } = team;

  return (
    <div className="flex flex-col">
      {/* Team header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-black uppercase tracking-widest text-white">
          {team.team_name}
        </h3>
        {team.formation && (
          <span className="text-[10px] font-mono font-bold text-[#05D9E8]/70 bg-[#05D9E8]/10 px-2 py-0.5 rounded">
            {team.formation}
          </span>
        )}
      </div>

      {/* Starters */}
      <div className="space-y-[2px]">
        {starters.map((p, i) => (
          <PlayerRow key={`s-${i}`} player={p} />
        ))}
      </div>

      {/* Divider: starters / subs */}
      {substitutes.length > 0 && (
        <div className="flex items-center gap-2 my-3">
          <div className="h-px flex-1 bg-white/10" />
          <span className="text-[9px] font-black uppercase tracking-[0.2em] text-white/30">PANCHINA</span>
          <div className="h-px flex-1 bg-white/10" />
        </div>
      )}

      {/* Substitutes */}
      {substitutes.length > 0 && (
        <div className="space-y-[2px]">
          {substitutes.map((p, i) => (
            <PlayerRow key={`sub-${i}`} player={p} isSub />
          ))}
        </div>
      )}
    </div>
  );
}

/* ─── Single Player Row ──────────────────────────────────────────────── */

function PlayerRow({ player, isSub }: { player: RosterPlayer; isSub?: boolean }) {
  const hasEvents = player.goals > 0 || player.yellow_cards > 0 || player.red_cards > 0;

  return (
    <div
      className={`
        flex items-center justify-between gap-2 px-3 py-2 rounded-md
        transition-colors
        ${isSub
          ? "bg-white/[0.03] hover:bg-white/[0.06]"
          : "bg-white/[0.06] hover:bg-white/[0.09]"
        }
      `}
    >
      {/* Left: player info */}
      <div className="flex items-center gap-2 min-w-0 flex-1">
        {/* Position badge (starters only) */}
        {player.position && !isSub && (
          <span className="text-[9px] font-mono font-bold text-[#05D9E8]/60 bg-[#05D9E8]/10 px-1.5 py-0.5 rounded shrink-0 uppercase">
            {player.position}
          </span>
        )}

        {/* Player name */}
        <span
          className={`
            text-sm font-semibold truncate
            ${isSub ? "text-white/60" : "text-white"}
          `}
        >
          {player.name}
        </span>

        {/* Sub badge */}
        {player.subbed_off && player.sub_minute && (
          <span className="text-[9px] font-bold text-red-400/70 shrink-0">
            ↓{player.sub_minute}'
          </span>
        )}
        {player.came_on && player.came_on_minute && (
          <span className="text-[9px] font-bold text-emerald-400/70 shrink-0">
            ↑{player.came_on_minute}'
          </span>
        )}
      </div>

      {/* Right: event icons */}
      {hasEvents && (
        <div className="shrink-0 flex items-center">
          <EventIcons player={player} />
        </div>
      )}
    </div>
  );
}

/* ─── Loading / Error / Empty States ─────────────────────────────────── */

function LoadingSkeleton() {
  return (
    <div className="flex flex-col items-center justify-center py-12 gap-4">
      <div className="w-6 h-6 border-2 border-[#FF2A6D] border-t-transparent rounded-full animate-spin" />
      <span className="text-[10px] font-black uppercase tracking-[0.3em] text-white/40">
        Formazioni
      </span>
    </div>
  );
}

function EmptyState({ message }: { message?: string }) {
  return (
    <div className="text-center py-12">
      <svg className="mx-auto w-8 h-8 text-white/20 mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="12" cy="12" r="10" />
        <path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10A15.3 15.3 0 0112 2z" />
      </svg>
      <p className="text-xs font-semibold text-white/30">{message || "Nessun dato formazioni disponibile."}</p>
    </div>
  );
}

/* ─── Main Component ─────────────────────────────────────────────────── */

interface MatchRosterListProps {
  matchId: number | string;
  /** Optional pre-fetched data (server-side render mode) */
  data?: LineupResponse;
}

export default function MatchRosterList({ matchId, data: directData }: MatchRosterListProps) {
  const [fetchedData, setFetchedData] = useState<LineupResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // If data was passed directly (SSR), skip fetch
    if (directData) return;

    const numericId = typeof matchId === "string" ? parseInt(matchId, 10) : matchId;
    if (!numericId || isNaN(numericId)) {
      setError("ID partita non valido.");
      return;
    }

    setLoading(true);
    setError(null);

    fetch(`http://localhost:8000/api/v1/matches/${numericId}/lineup`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((json: LineupResponse) => {
        setFetchedData(json);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, [matchId, directData]);

  const data = directData || fetchedData;

  if (loading) return <LoadingSkeleton />;
  if (error) return <EmptyState message={`Errore: ${error}`} />;
  if (!data) return <LoadingSkeleton />;
  if (data.error) return <EmptyState message={data.error} />;
  if (!data.home && !data.away) return <EmptyState />;

  return (
    <section className="rounded-2xl overflow-hidden border border-white/10 bg-[#0f0f13]">
      {/* Header */}
      <div className="bg-[#0a0a0f] border-b border-white/5 px-5 py-3.5 flex items-center gap-3">
        <div className="w-2 h-2 rounded-full bg-[#FF2A6D]" />
        <span className="text-[10px] font-black uppercase tracking-[0.25em] text-white/50">
          Formazioni
        </span>
      </div>

      {/* Dual-column grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-0">
        {/* Home Column */}
        <div className="p-4 md:p-5 border-r-0 md:border-r border-white/5">
          {data.home ? (
            <TeamColumn team={data.home} />
          ) : (
            <p className="text-sm text-white/30 text-center py-6">N/D</p>
          )}
        </div>

        {/* Away Column */}
        <div className="p-4 md:p-5">
          {data.away ? (
            <TeamColumn team={data.away} />
          ) : (
            <p className="text-sm text-white/30 text-center py-6">N/D</p>
          )}
        </div>
      </div>

      {/* Footer — legend */}
      <div className="bg-[#0a0a0f] border-t border-white/5 px-5 py-2 flex items-center gap-4 text-[10px] text-white/30">
        <span>⚽ Gol</span>
        <span>🟨 Ammonizione</span>
        <span>🟥 Espulsione</span>
      </div>
    </section>
  );
}
