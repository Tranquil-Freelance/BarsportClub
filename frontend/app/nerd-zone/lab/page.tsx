"use client";

import { useState, Suspense } from "react";
import { useRouter } from "next/navigation";
import { Loader2, ChevronLeft, Play, ArrowUpDown } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const DIMENSIONS = [
  { id: "season",    label: "Season"     },
  { id: "situation", label: "Situation"  },
  { id: "position",  label: "Position"   },
  { id: "home_away", label: "Home / Away"},
  { id: "timing",    label: "Time Period"},
  { id: "zone",      label: "Shot Zone"  },
  { id: "result",    label: "Shot Result"},
] as const;

const METRICS = [
  { id: "apps",       label: "Appearances"  },
  { id: "minutes",    label: "Minutes"      },
  { id: "goals",      label: "Goals"        },
  { id: "assists",    label: "Assists"      },
  { id: "shots",      label: "Shots"        },
  { id: "key_passes", label: "Key Passes"   },
  { id: "xg",         label: "xG"           },
  { id: "xa",         label: "xA"           },
  { id: "xgchain",    label: "xGChain"      },
  { id: "xgbuildup",  label: "xGBuildup"    },
  { id: "xg90",       label: "xG/90"        },
  { id: "xa90",       label: "xA/90"        },
  { id: "g90",        label: "G/90"         },
  { id: "sh90",       label: "Sh/90"        },
  { id: "kp90",       label: "KP/90"        },
  { id: "shot_xg_sum",label: "Shot xG (raw)"},
  { id: "shot_goals", label: "Shot Goals"   },
] as const;

const LEAGUES  = [
  { id: 1, name: "Serie A" }, { id: 2, name: "Premier League" },
  { id: 3, name: "La Liga"  }, { id: 4, name: "Bundesliga"     },
  { id: 5, name: "Ligue 1"  },
];
const SEASONS  = ["2025/26", "2024/25", "2023/24"];

interface QueryResult {
  columns: string[];
  rows: Record<string, string | number | null>[];
}

function Toggle({
  id, label, active, onClick,
}: { id: string; label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider border transition-all ${
        active
          ? "bg-[#10B981]/15 border-[#10B981]/40 text-[#10B981]"
          : "bg-[#0d1220] border-slate-800 text-slate-600 hover:text-slate-400"
      }`}
    >
      {label}
    </button>
  );
}

function LabInner() {
  const router = useRouter();

  const [entity,     setEntity]     = useState<"player"|"team">("player");
  const [dims,       setDims]       = useState<Set<string>>(new Set(["season"]));
  const [mets,       setMets]       = useState<Set<string>>(new Set(["goals","xg","xg90","minutes"]));
  const [leagueIds,  setLeagueIds]  = useState<number[]>([1]);
  const [season,     setSeason]     = useState("2025/26");
  const [minMin,     setMinMin]     = useState(0);
  const [result,     setResult]     = useState<QueryResult | null>(null);
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState<string | null>(null);
  const [sortCol,    setSortCol]    = useState<string | null>(null);
  const [sortDir,    setSortDir]    = useState<"asc"|"desc">("desc");

  function toggleSet(s: Set<string>, val: string): Set<string> {
    const n = new Set(s);
    n.has(val) ? n.delete(val) : n.add(val);
    return n;
  }

  async function runQuery() {
    if (!dims.size || !mets.size) return;
    setLoading(true);
    setError(null);
    try {
      const p = new URLSearchParams({ entity, season, min_minutes: String(minMin) });
      [...dims].forEach(d => p.append("dimensions", d));
      [...mets].forEach(m => p.append("metrics", m));
      leagueIds.forEach(id => p.append("league_ids", String(id)));
      const res = await fetch(`${API_BASE}/api/nerd-zone/lab?${p}`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `HTTP ${res.status}`);
      }
      setResult(await res.json());
      setSortCol(null);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  // Sort result rows
  const displayRows = result
    ? [...result.rows].sort((a, b) => {
        if (!sortCol) return 0;
        const av = a[sortCol] ?? "";
        const bv = b[sortCol] ?? "";
        const diff = av < bv ? -1 : av > bv ? 1 : 0;
        return sortDir === "asc" ? diff : -diff;
      })
    : [];

  function handleColSort(col: string) {
    if (sortCol === col) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortCol(col); setSortDir("desc"); }
  }

  function fmtCell(val: string | number | null): string {
    if (val == null) return "—";
    if (typeof val === "number") return val.toFixed(3).replace(/\.?0+$/, "");
    return String(val);
  }

  return (
    <div className="min-h-screen bg-[#1A202C] text-white">
      {/* Header */}
      <div className="border-b border-slate-800/60 bg-[#080b12] px-4 md:px-6 py-4 flex items-center gap-4 sticky top-0 z-30">
        <button onClick={() => router.push("/nerd-zone")} className="text-slate-600 hover:text-white transition-colors">
          <ChevronLeft size={20} />
        </button>
        <div>
          <h1 className="font-black text-xl tracking-tight">Query Lab</h1>
          <p className="text-[10px] text-slate-600 uppercase tracking-[0.2em]">God Mode — Combine any dimension × metric</p>
        </div>
      </div>

      <div className="px-4 md:px-8 py-6 max-w-7xl mx-auto space-y-6">

        {/* Config panel */}
        <div className="bg-[#0a0c14] border border-slate-800/60 rounded-2xl p-5 space-y-5">

          {/* Entity */}
          <div>
            <p className="text-[10px] font-black tracking-widest uppercase text-slate-600 mb-2">Entity</p>
            <div className="flex rounded-xl overflow-hidden border border-slate-800 w-fit">
              {(["player","team"] as const).map(e => (
                <button key={e} onClick={() => setEntity(e)}
                  className={`px-5 py-2 text-xs font-black uppercase tracking-wider transition-colors ${
                    entity === e ? "bg-[#10B981] text-white" : "bg-[#0d1220] text-slate-500 hover:text-white"
                  }`}
                >
                  {e}
                </button>
              ))}
            </div>
          </div>

          {/* Dimensions */}
          <div>
            <p className="text-[10px] font-black tracking-widest uppercase text-slate-600 mb-2">
              Group By (Dimensions)
            </p>
            <div className="flex flex-wrap gap-2">
              {DIMENSIONS.map(d => (
                <Toggle key={d.id} id={d.id} label={d.label}
                  active={dims.has(d.id)} onClick={() => setDims(s => toggleSet(s, d.id))} />
              ))}
            </div>
          </div>

          {/* Metrics */}
          <div>
            <p className="text-[10px] font-black tracking-widest uppercase text-slate-600 mb-2">
              Show Metrics
            </p>
            <div className="flex flex-wrap gap-2">
              {METRICS.map(m => (
                <Toggle key={m.id} id={m.id} label={m.label}
                  active={mets.has(m.id)} onClick={() => setMets(s => toggleSet(s, m.id))} />
              ))}
            </div>
          </div>

          {/* Filters row */}
          <div className="flex flex-wrap gap-6 items-end border-t border-slate-800/60 pt-4">
            {/* Leagues */}
            <div>
              <p className="text-[10px] text-slate-600 uppercase tracking-widest mb-1.5">Leagues</p>
              <div className="flex flex-wrap gap-1.5">
                {LEAGUES.map(l => (
                  <label key={l.id} className="flex items-center gap-1.5 cursor-pointer group">
                    <input type="checkbox" checked={leagueIds.includes(l.id)}
                      onChange={() => setLeagueIds(prev =>
                        prev.includes(l.id) ? prev.filter(x => x !== l.id) : [...prev, l.id]
                      )}
                      className="accent-[#10B981] w-3.5 h-3.5"
                    />
                    <span className="text-xs text-slate-500 group-hover:text-slate-300 transition-colors">{l.name}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Season */}
            <div>
              <p className="text-[10px] text-slate-600 uppercase tracking-widest mb-1.5">Season</p>
              <select value={season} onChange={e => setSeason(e.target.value)}
                className="bg-[#0d1220] border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none">
                {SEASONS.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            {/* Min minutes */}
            <div>
              <div className="flex justify-between mb-1">
                <p className="text-[10px] text-slate-600 uppercase tracking-widest">Min. Minutes</p>
                <span className="text-[10px] font-mono text-[#10B981] ml-4">{minMin}</span>
              </div>
              <input type="range" min={0} max={2000} step={50} value={minMin}
                onChange={e => setMinMin(Number(e.target.value))}
                className="w-36 accent-[#10B981] h-1.5 cursor-pointer" />
            </div>

            {/* Run */}
            <button
              onClick={runQuery}
              disabled={loading || !dims.size || !mets.size || !leagueIds.length}
              className="flex items-center gap-2 py-2.5 px-8 bg-[#10B981] hover:bg-[#0da271] disabled:opacity-40 disabled:cursor-not-allowed rounded-xl font-black text-xs uppercase tracking-widest transition-all shadow-[0_0_16px_rgba(16,185,129,0.3)]"
            >
              {loading ? <Loader2 size={13} className="animate-spin" /> : <Play size={13} />}
              Run Query
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-950/40 border border-red-800/40 rounded-xl px-4 py-3 text-red-400 text-sm">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Results table */}
        {result && !loading && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <p className="text-[10px] font-black tracking-[0.2em] uppercase text-slate-600">
                Results — {result.rows.length} rows
              </p>
              <p className="text-[10px] text-slate-700">Click column headers to sort</p>
            </div>
            <div className="overflow-x-auto rounded-xl border border-slate-800/60">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-[#0d1220]">
                    {result.columns.map(col => (
                      <th
                        key={col}
                        onClick={() => handleColSort(col)}
                        className={`px-3 py-3 text-[10px] font-black uppercase tracking-widest cursor-pointer select-none whitespace-nowrap transition-colors hover:text-white ${
                          sortCol === col ? "text-white" : "text-slate-500"
                        } ${[...dims].includes(col) ? "text-left" : "text-right"}`}
                      >
                        {col.replace(/_/g, " ")}
                        {sortCol === col
                          ? (sortDir === "asc" ? " ↑" : " ↓")
                          : <ArrowUpDown size={8} className="inline ml-1 opacity-30" />
                        }
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {displayRows.map((row, i) => (
                    <tr key={i} className="border-t border-slate-800/40 hover:bg-[#0d1220] transition-colors">
                      {result.columns.map(col => (
                        <td
                          key={col}
                          className={`px-3 py-2 font-mono text-[11px] whitespace-nowrap ${
                            [...dims].includes(col)
                              ? "text-left text-white font-semibold"
                              : "text-right text-slate-400"
                          }`}
                        >
                          {fmtCell(row[col])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {!result && !loading && (
          <div className="flex flex-col items-center justify-center py-20 text-center gap-3">
            <div className="text-6xl">🔬</div>
            <p className="text-slate-700 text-sm uppercase tracking-[0.2em]">Configure your query and hit Run</p>
            <p className="text-slate-800 text-xs max-w-md leading-relaxed">
              Pick any combination of dimensions (how to group) and metrics (what to measure).
              Example: group by <span className="text-slate-600">Situation × Season</span> and show{" "}
              <span className="text-slate-600">xG, Goals, xG/90</span> — the backend generates the SQL live.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function LabPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#1A202C] flex items-center justify-center">
        <Loader2 size={24} className="animate-spin text-[#10B981]" />
      </div>
    }>
      <LabInner />
    </Suspense>
  );
}
