"use client";

import { useEffect, useState, Suspense } from "react";
import { useParams, useRouter, useSearchParams, usePathname } from "next/navigation";
import { Loader2, ChevronLeft, Download } from "lucide-react";
import dynamic from "next/dynamic";
import ShotMapHorizontal, { type ShotData } from "../../components/ShotMapHorizontal";
import MatchLog from "../../components/MatchLog";

const RadarEcharts = dynamic(() => import("../../components/RadarEcharts"), { ssr: false });

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SEASONS  = ["All", "2025/26", "2024/25", "2023/24"];
const LEAGUES  = [
  { id: 1, name: "Serie A" }, { id: 2, name: "Premier" },
  { id: 3, name: "La Liga" }, { id: 4, name: "Bundesliga" }, { id: 5, name: "Ligue 1" },
];

const HISTORY_TABS = [
  { id: "season",     label: "Season"     },
  { id: "position",   label: "Position"   },
  { id: "situation",  label: "Situation"  },
  { id: "shot_zones", label: "Shot zones" },
  { id: "shot_types", label: "Shot types" },
] as const;

type HistTab = typeof HISTORY_TABS[number]["id"];

interface HistRow { label: string; [key: string]: number | string; }
interface RadarData {
  name: string; xG_p90: number; xA_p90: number; shots_p90: number;
  key_passes_p90: number; xGChain_p90: number; xGBuildup_p90: number;
  goals_p90: number; assists_p90: number;
}

function Delta({ base, actual }: { base: number; actual: number }) {
  const d = actual - base;
  const color = d >= 0 ? "#10B981" : "#EF4444";
  return <sup className="ml-0.5 text-[9px] font-black" style={{ color }}>{d >= 0 ? "+" : ""}{d.toFixed(2)}</sup>;
}

const SEASON_COLS = [
  { key: "label",   h: "Season",  align: "left"  },
  { key: "matches", h: "Apps",    align: "right" },
  { key: "minutes", h: "Min",     align: "right" },
  { key: "goals",   h: "G",       align: "right" },
  { key: "assists", h: "A",       align: "right" },
  { key: "shots",   h: "Sh",      align: "right" },
  { key: "sh90",    h: "Sh90",    align: "right" },
  { key: "kp90",    h: "KP90",    align: "right" },
  { key: "xg",      h: "xG",      align: "right", delta: "goals"   },
  { key: "xa",      h: "xA",      align: "right", delta: "assists"  },
  { key: "xg90",    h: "xG90",    align: "right" },
  { key: "xa90",    h: "xA90",    align: "right" },
] as const;

const SIT_COLS = [
  { key: "label",          h: "Situation",   align: "left"  },
  { key: "shots",          h: "Sh",          align: "right" },
  { key: "goals",          h: "G",           align: "right" },
  { key: "xg",             h: "xG",          align: "right", delta: "goals" },
  { key: "xg_per_shot",    h: "xG/Sh",       align: "right" },
  { key: "conversion_pct", h: "Conv%",       align: "right" },
] as const;

// shot_zones and shot_types reuse situation data as a visual alias
function backendTabFor(tab: HistTab): string {
  if (tab === "shot_zones" || tab === "shot_types") return "situation";
  return tab;
}

function colsFor(tab: HistTab) {
  return (tab === "situation" || tab === "shot_zones" || tab === "shot_types")
    ? SIT_COLS
    : SEASON_COLS;
}

function cellFmt(val: number | string, key: string): string {
  if (key === "label") return String(val);
  if (typeof val !== "number") return String(val);
  if (["matches", "goals", "assists", "shots"].includes(key)) return String(Math.round(val));
  if (key === "minutes") return val.toLocaleString();
  if (key === "conversion_pct") return `${val.toFixed(1)}%`;
  if (["xg90", "xa90", "xg_per_shot"].includes(key)) return val.toFixed(3);
  return val.toFixed(2);
}

function PlayerPageInner() {
  const params   = useParams();
  const router   = useRouter();
  const pathname = usePathname();
  const sp       = useSearchParams();

  const playerName = decodeURIComponent(params.slug as string);
  const season     = sp.get("season")  ?? "2025/26";
  const leagueIds  = (sp.get("leagues") ?? "").split(",").map(Number).filter(Boolean);
  const histTab    = (sp.get("htab") ?? "season") as HistTab;

  const [history,       setHistory]       = useState<HistRow[]>([]);
  const [shots,         setShots]         = useState<ShotData[]>([]);
  const [radar,         setRadar]         = useState<RadarData | null>(null);
  const [loadH,         setLoadH]         = useState(false);
  const [loadS,         setLoadS]         = useState(false);
  const [shotSituation, setShotSituation] = useState("All");
  const [shotResult,    setShotResult]    = useState("All");

  function setParam(key: string, val: string) {
    const next = new URLSearchParams(sp.toString());
    next.set(key, val);
    router.replace(`${pathname}?${next.toString()}`, { scroll: false });
  }

  // History
  useEffect(() => {
    if (!playerName) return;
    setLoadH(true);
    const p = new URLSearchParams({ player: playerName, tab: backendTabFor(histTab) });
    leagueIds.forEach(id => p.append("league_ids", String(id)));
    fetch(`${API_BASE}/api/nerd-zone/player-history?${p}`, { cache: "no-store" })
      .then(r => r.json())
      .then(setHistory)
      .catch(() => setHistory([]))
      .finally(() => setLoadH(false));
  }, [playerName, histTab, leagueIds.join(",")]);

  // Shots + radar
  useEffect(() => {
    if (!playerName) return;
    setLoadS(true);
    const p = new URLSearchParams({ player: playerName, season });
    leagueIds.forEach(id => p.append("league_ids", String(id)));
    if (shotSituation !== "All") p.set("situation", shotSituation);
    if (shotResult    !== "All") p.set("result",    shotResult);

    Promise.all([
      fetch(`${API_BASE}/api/nerd-zone/player-shots?${p}`, { cache: "no-store" }).then(r => r.json()),
      fetch(`${API_BASE}/api/nerd-zone/player-radar?${new URLSearchParams({ player: playerName, season })}`, { cache: "no-store" }).then(r => r.json()),
    ]).then(([s, r]) => { setShots(s); setRadar(r); })
      .catch(() => {})
      .finally(() => setLoadS(false));
  }, [playerName, season, leagueIds.join(","), shotSituation, shotResult]);

  // Totals row
  const seasonRows = (histTab !== "situation" && histTab !== "shot_zones" && histTab !== "shot_types") ? history as any[] : [];
  const totals = seasonRows.reduce(
    (acc: any, r: any) => ({
      matches: (acc.matches || 0) + (r.matches || 0),
      minutes: (acc.minutes || 0) + (r.minutes || 0),
      goals:   (acc.goals   || 0) + (r.goals   || 0),
      assists: (acc.assists  || 0) + (r.assists  || 0),
      shots:   (acc.shots || 0) + (r.shots || 0),
      xg:      (acc.xg    || 0) + (r.xg    || 0),
      xa:      (acc.xa      || 0) + (r.xa      || 0),
    }),
    {}
  );
  const hasTotals = histTab !== "situation" && histTab !== "shot_zones" && histTab !== "shot_types" && seasonRows.length > 1;

  const cols = colsFor(histTab) as readonly { key: string; h: string; align: string; delta?: string }[];

  function handleHistCSV() {
    const headers = cols.map(c => c.h).join(",");
    const csvRows = history.map((row: any) =>
      cols.map(c => cellFmt(row[c.key], c.key)).join(",")
    );
    const blob = new Blob([headers + "\n" + csvRows.join("\n")], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${playerName}_${histTab}.csv`;
    a.click();
  }

  return (
    <div className="min-h-screen bg-[#1A202C] text-white">
      {/* Header */}
      <div className="border-b border-slate-800/60 bg-[#080b12] px-4 md:px-6 py-4 flex items-center gap-4 sticky top-0 z-30">
        <button onClick={() => router.back()} className="text-slate-600 hover:text-white transition-colors">
          <ChevronLeft size={20} />
        </button>
        <div>
          <h1 className="font-black text-xl tracking-tight">{playerName}</h1>
          <p className="text-[10px] text-slate-600 uppercase tracking-[0.2em]">Player Analytics</p>
        </div>
        <div className="ml-auto flex items-center gap-3 flex-wrap">
          <select value={season} onChange={e => setParam("season", e.target.value)}
            className="bg-[#0d1220] border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none">
            {SEASONS.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <div className="flex gap-1.5">
            {LEAGUES.map(l => (
              <button
                key={l.id}
                onClick={() => {
                  const next = leagueIds.includes(l.id)
                    ? leagueIds.filter(x => x !== l.id)
                    : [...leagueIds, l.id];
                  setParam("leagues", next.join(","));
                }}
                className={`px-2 py-1 rounded text-[9px] font-black uppercase border transition-all ${
                  leagueIds.includes(l.id)
                    ? "bg-[#10B981]/15 border-[#10B981]/40 text-[#10B981]"
                    : "bg-[#0d1220] border-slate-800 text-slate-600"
                }`}
              >
                {l.name}
              </button>
            ))}
          </div>
          {(loadH || loadS) && <Loader2 size={14} className="animate-spin text-[#10B981]" />}
        </div>
      </div>

      <div className="px-4 md:px-6 py-6 space-y-8">

        {/* ── Historical Stats Table ─────────────────────────────────── */}
        <section>
          <div className="flex items-center border-b border-slate-800/60 mb-4">
            {HISTORY_TABS.map(t => (
              <button key={t.id} onClick={() => setParam("htab", t.id)}
                className={`relative px-5 py-2.5 text-[11px] font-black uppercase tracking-widest transition-colors ${
                  histTab === t.id ? "text-white" : "text-slate-600 hover:text-slate-400"
                }`}
              >
                {t.label}
                {histTab === t.id && (
                  <span className="absolute bottom-0 left-0 w-full h-0.5 bg-[#10B981] rounded-t" />
                )}
              </button>
            ))}
            <button
              onClick={handleHistCSV}
              disabled={!history.length}
              className="ml-auto p-1.5 rounded border border-slate-800 bg-[#0d1220] text-slate-600 hover:text-white transition-colors disabled:opacity-30"
              title="Download CSV"
            >
              <Download size={12} />
            </button>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800/60">
            {loadH ? (
              <div className="flex items-center justify-center h-28 text-slate-700 text-xs">Loading…</div>
            ) : !history.length ? (
              <div className="flex items-center justify-center h-28 text-slate-800 text-xs">No data</div>
            ) : (
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-[#0d1220]">
                    <th className="px-3 py-2.5 text-left text-[10px] font-black uppercase tracking-widest text-slate-600 w-6">#</th>
                    {cols.map(c => (
                      <th key={c.key} className={`px-3 py-2.5 text-[10px] font-black uppercase tracking-widest text-slate-500 whitespace-nowrap ${c.align === "right" ? "text-right" : "text-left"}`}>
                        {c.h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {history.map((row, i) => (
                    <tr key={i} className="border-t border-slate-800/40 hover:bg-[#0d1220] transition-colors">
                      <td className="px-3 py-2 text-slate-700 font-mono">{i + 1}</td>
                      {cols.map(c => {
                        const val = row[c.key];
                        const isXG = c.delta && typeof val === "number";
                        const deltaActual = c.delta ? (row[c.delta] as number) : 0;
                        return (
                          <td key={c.key} className={`px-3 py-2 font-mono text-[11px] whitespace-nowrap ${
                            c.align === "right" ? "text-right" : "text-left"
                          } ${c.key === "label" ? "text-white font-semibold" : "text-slate-400"}
                          ${c.key === "xg" ? "text-[#60a5fa]" : ""}
                          ${c.key === "xa" ? "text-[#818cf8]" : ""}
                          `}>
                            {cellFmt(val, c.key)}
                            {isXG && <Delta base={val as number} actual={deltaActual} />}
                          </td>
                        );
                      })}
                    </tr>
                  ))}

                  {hasTotals && (
                    <tr className="border-t-2 border-slate-700 bg-[#0d1220] font-bold">
                      <td className="px-3 py-2 text-slate-600 text-[10px]" />
                      {cols.map(c => {
                        if (c.key === "label") return <td key="label" className="px-3 py-2 text-slate-600 text-[10px] uppercase tracking-widest">Total</td>;
                        const tv = (totals as any)[c.key];
                        if (tv == null) return <td key={c.key} className="px-3 py-2" />;
                        return (
                          <td key={c.key} className="px-3 py-2 text-right font-mono text-[11px] text-slate-300 whitespace-nowrap">
                            {cellFmt(tv, c.key)}
                            {c.delta && <Delta base={tv} actual={(totals as any)[c.delta] ?? 0} />}
                          </td>
                        );
                      })}
                    </tr>
                  )}
                </tbody>
              </table>
            )}
          </div>
        </section>

        {/* ── Radar + Shot Map ──────────────────────────────────────────── */}
        <section className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* Radar */}
          <div>
            <p className="text-[10px] font-black tracking-[0.2em] uppercase text-slate-600 mb-3">
              Radar Profile — {season}
            </p>
            {loadS || !radar ? (
              <div className="flex items-center justify-center h-64 text-slate-800 text-xs bg-[#0a0e17] border border-slate-800/60 rounded-2xl">
                {loadS ? "Loading…" : "No radar data"}
              </div>
            ) : (
              <RadarEcharts data={radar} />
            )}
          </div>

          {/* Shot map */}
          <div>
            <p className="text-[10px] font-black tracking-[0.2em] uppercase text-slate-600 mb-3">
              Shot Map — {season}
            </p>
            {/* Shot map filters */}
            <div className="flex flex-wrap gap-3 mb-3">
              <div>
                <label className="text-[9px] text-slate-600 uppercase tracking-widest block mb-1">Situation</label>
                <select
                  value={shotSituation}
                  onChange={e => setShotSituation(e.target.value)}
                  className="bg-[#0d1220] border border-slate-800 rounded px-2 py-1 text-xs text-white focus:outline-none"
                >
                  {["All","OpenPlay","FromCorner","SetPiece","DirectFreekick","Penalty"].map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-[9px] text-slate-600 uppercase tracking-widest block mb-1">Result</label>
                <select
                  value={shotResult}
                  onChange={e => setShotResult(e.target.value)}
                  className="bg-[#0d1220] border border-slate-800 rounded px-2 py-1 text-xs text-white focus:outline-none"
                >
                  {["All","Goal","SavedShot","MissedShots","BlockedShot"].map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
            </div>
            {loadS ? (
              <div className="flex items-center justify-center h-64 text-slate-800 text-xs bg-[#0a0e17] border border-slate-800/60 rounded-2xl">
                Loading…
              </div>
            ) : !shots.length ? (
              <div className="flex items-center justify-center h-64 text-slate-800 text-xs bg-[#0a0e17] border border-slate-800/60 rounded-2xl">
                No shot data for this filter
              </div>
            ) : (
              <ShotMapHorizontal shots={shots} />
            )}
          </div>
        </section>

        {/* ── Match Log ─────────────────────────────────────────────────── */}
        <section>
          <p className="text-[10px] font-black tracking-[0.2em] uppercase text-slate-600 mb-3">
            Match Log
          </p>
          <MatchLog player={playerName} season={season} leagueIds={leagueIds} />
        </section>
      </div>
    </div>
  );
}

export default function PlayerPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#1A202C] flex items-center justify-center">
        <Loader2 size={24} className="animate-spin text-[#10B981]" />
      </div>
    }>
      <PlayerPageInner />
    </Suspense>
  );
}
