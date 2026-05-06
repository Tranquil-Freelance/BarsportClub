"use client";

import { useEffect, useState, Suspense } from "react";
import { useParams, useRouter, useSearchParams, usePathname } from "next/navigation";
import { Loader2, ChevronLeft } from "lucide-react";
import MatchCalendar from "../../components/MatchCalendar";
import TeamSituationTable, { type TabId } from "../../components/TeamSituationTable";
import RosterTable, { type RosterRow } from "../../components/RosterTable";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SEASONS  = ["2025/26", "2024/25", "2023/24"];

interface Match {
  match_id: number; date: string; home_team: string; away_team: string;
  home_team_id: number; away_team_id: number;
  home_goals: number|null; away_goals: number|null;
  home_xg: number|null; away_xg: number|null;
  is_completed: boolean; matchday: number|null; is_home: boolean;
}

interface TeamInfo { id: number; name: string; }

function TeamPageInner() {
  const params   = useParams();
  const router   = useRouter();
  const pathname = usePathname();
  const sp       = useSearchParams();

  const teamId = parseInt(params.id as string, 10);

  const season  = sp.get("season")  ?? "2025/26";
  const statTab = (sp.get("tab") ?? "situation") as TabId;

  const [teamInfo,   setTeamInfo]   = useState<TeamInfo | null>(null);
  const [matches,    setMatches]    = useState<Match[]>([]);
  const [roster,     setRoster]     = useState<RosterRow[]>([]);
  const [sortKey,    setSortKey]    = useState<keyof RosterRow>("xg");
  const [sortDir,    setSortDir]    = useState<"asc"|"desc">("desc");
  const [loading,    setLoading]    = useState(false);
  const [posFilter,  setPosFilter]  = useState("All");
  const [lastN,      setLastN]      = useState<number|null>(null);

  function setParam(key: string, val: string) {
    const next = new URLSearchParams(sp.toString());
    next.set(key, val);
    router.replace(`${pathname}?${next.toString()}`, { scroll: false });
  }

  // Load matches (once per season)
  useEffect(() => {
    if (!teamId) return;
    fetch(
      `${API_BASE}/api/nerd-zone/team-matches?team_id=${teamId}&season=${encodeURIComponent(season)}&limit=38`,
      { cache: "no-store" }
    )
      .then(r => r.json())
      .then((data: Match[]) => {
        setMatches(data);
        if (data.length) {
          const m = data[0];
          const name = m.home_team_id === teamId ? m.home_team : m.away_team;
          setTeamInfo({ id: teamId, name });
        }
      });
  }, [teamId, season]);

  // Load roster (re-fetches on filter change)
  useEffect(() => {
    if (!teamId) return;
    setLoading(true);
    let url = `${API_BASE}/api/nerd-zone/team-roster?team_id=${teamId}&season=${encodeURIComponent(season)}`;
    if (posFilter !== "All") url += `&position=${posFilter}`;
    if (lastN) url += `&last_n=${lastN}`;
    fetch(url, { cache: "no-store" })
      .then(r => r.json())
      .then(setRoster)
      .catch(() => setRoster([]))
      .finally(() => setLoading(false));
  }, [teamId, season, posFilter, lastN]);

  function handleSort(key: keyof RosterRow) {
    if (key === sortKey) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortKey(key); setSortDir("desc"); }
  }

  const teamName = teamInfo?.name ?? `Team ${teamId}`;

  return (
    <div className="min-h-screen bg-[#1A202C] text-white">
      {/* Header */}
      <div className="border-b border-slate-800/60 bg-[#080b12] px-4 md:px-6 py-4 flex items-center gap-4 sticky top-0 z-30">
        <button
          onClick={() => router.push("/nerd-zone")}
          className="text-slate-600 hover:text-white transition-colors"
        >
          <ChevronLeft size={20} />
        </button>
        <div>
          <h1 className="font-black text-xl tracking-tight">{teamName}</h1>
          <p className="text-[10px] text-slate-600 uppercase tracking-[0.2em]">Team Analytics</p>
        </div>
        <div className="ml-auto flex items-center gap-3">
          <select
            value={season}
            onChange={e => setParam("season", e.target.value)}
            className="bg-[#0d1220] border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none"
          >
            {SEASONS.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          {loading && <Loader2 size={14} className="animate-spin text-[#10B981]" />}
        </div>
      </div>

      <div className="px-4 md:px-6 py-6 space-y-6">

        {/* Match Calendar */}
        <section>
          <p className="text-[10px] font-black tracking-[0.2em] uppercase text-slate-600 mb-3">Matches</p>
          {matches.length > 0
            ? <MatchCalendar matches={matches} teamId={teamId} />
            : <div className="text-slate-700 text-xs py-4">No matches found for this season.</div>
          }
        </section>

        {/* Shot Analytics */}
        <section>
          <p className="text-[10px] font-black tracking-[0.2em] uppercase text-slate-600 mb-3">
            Shot Analytics — For &amp; Against
          </p>
          <TeamSituationTable
            teamId={teamId}
            season={season}
            tab={statTab}
            onTabChange={t => setParam("tab", t)}
          />
        </section>

        {/* Player Roster */}
        <section>
          <p className="text-[10px] font-black tracking-[0.2em] uppercase text-slate-600 mb-3">Player Roster</p>

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-3 mb-3">
            <div className="flex gap-1.5">
              {["All", "GK", "DF", "MF", "FW"].map(pos => (
                <button
                  key={pos}
                  onClick={() => setPosFilter(pos)}
                  className={`px-2.5 py-1 rounded text-[10px] font-black uppercase border transition-all ${
                    posFilter === pos
                      ? "bg-[#10B981]/15 border-[#10B981]/40 text-[#10B981]"
                      : "bg-[#0d1220] border-slate-800 text-slate-600 hover:text-slate-400"
                  }`}
                >
                  {pos}
                </button>
              ))}
            </div>
            <div className="flex gap-1.5">
              {([null, 5, 10, 15] as (number|null)[]).map(n => (
                <button
                  key={String(n)}
                  onClick={() => setLastN(n)}
                  className={`px-2.5 py-1 rounded text-[10px] font-black uppercase border transition-all ${
                    lastN === n
                      ? "bg-[#10B981]/15 border-[#10B981]/40 text-[#10B981]"
                      : "bg-[#0d1220] border-slate-800 text-slate-600 hover:text-slate-400"
                  }`}
                >
                  {n === null ? "All" : `Last ${n}`}
                </button>
              ))}
            </div>
          </div>

          {roster.length > 0 ? (
            <RosterTable
              rows={roster}
              selectedPlayer={null}
              onSelectPlayer={name => router.push(`/nerd-zone/player/${encodeURIComponent(name)}?season=${encodeURIComponent(season)}`)}
              sortKey={sortKey}
              sortDir={sortDir}
              onSort={handleSort}
            />
          ) : loading ? (
            <div className="flex items-center justify-center h-32 text-slate-700 text-xs">Loading roster…</div>
          ) : (
            <div className="flex items-center justify-center h-32 text-slate-800 text-xs">No roster data</div>
          )}
        </section>
      </div>
    </div>
  );
}

export default function TeamPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#1A202C] flex items-center justify-center">
        <Loader2 size={24} className="animate-spin text-[#10B981]" />
      </div>
    }>
      <TeamPageInner />
    </Suspense>
  );
}
