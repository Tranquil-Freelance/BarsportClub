"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Download, ArrowUpDown } from "lucide-react";
import { useTranslation } from "react-i18next";
import "../i18n/config";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const LEAGUES = [
  { id: 2, name: "Premier League" },
  { id: 1, name: "Serie A" },
  { id: 3, name: "La Liga" },
  { id: 4, name: "Bundesliga" },
  { id: 5, name: "Ligue 1" },
];
const SEASONS = ["2025/26", "2024/25", "2023/24"];

interface StandingRow {
  id: number; name: string;
  mp: number; w: number; d: number; l: number;
  gf: number; ga: number; gd: number; pts: number;
  xg: number; xga: number; xpts: number; xgd: number;
}

type SortKey = keyof StandingRow;

function Delta({ base, actual }: { base: number; actual: number }) {
  const d = actual - base;
  if (Math.abs(d) < 0.01) return null;
  const color = d >= 0 ? "#10B981" : "#EF4444";
  return <sup style={{ color, fontSize: "9px", marginLeft: "2px", fontWeight: 700 }}>{d >= 0 ? "+" : ""}{d.toFixed(2)}</sup>;
}

function downloadCSV(rows: StandingRow[], season: string, leagueName: string) {
  const headers = ["#","Team","MP","W","D","L","GF","GA","GD","Pts","xG","xGA","xPTS","xGD"];
  const csvRows = rows.map((r, i) =>
    [i+1, r.name, r.mp, r.w, r.d, r.l, r.gf, r.ga, r.gd, r.pts,
     r.xg, r.xga, r.xpts, r.xgd].join(",")
  );
  const blob = new Blob([headers.join(",") + "\n" + csvRows.join("\n")], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${leagueName}_${season.replace("/","_")}_standings.csv`;
  a.click();
}

export default function NerdZonePage() {
  const router = useRouter();
  const { t } = useTranslation();
  const [leagueId, setLeagueId] = useState(2);
  const [season,   setSeason]   = useState("2025/26");
  const [rows,     setRows]     = useState<StandingRow[]>([]);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState<string | null>(null);
  const [sortKey,  setSortKey]  = useState<SortKey>("pts");
  const [sortDir,  setSortDir]  = useState<"asc"|"desc">("desc");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `${API_BASE}/api/nerd-zone/league-table?league_id=${leagueId}&season=${encodeURIComponent(season)}`,
        { cache: "no-store" }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setRows(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      setRows([]);
    } finally { setLoading(false); }
  }, [leagueId, season]);

  useEffect(() => { load(); }, [load]);

  function handleSort(key: SortKey) {
    if (key === sortKey) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortKey(key); setSortDir(key === "name" ? "asc" : "desc"); }
  }

  const sorted = [...rows].sort((a, b) => {
    const av = a[sortKey], bv = b[sortKey];
    const diff = av < bv ? -1 : av > bv ? 1 : 0;
    return sortDir === "asc" ? diff : -diff;
  });

  const leagueName = LEAGUES.find(l => l.id === leagueId)?.name ?? "League";

  const COLS: { key: SortKey; label: string; note?: string }[] = [
    { key: "mp",   label: "MP"   },
    { key: "w",    label: "W"    },
    { key: "d",    label: "D"    },
    { key: "l",    label: "L"    },
    { key: "gf",   label: "GF"   },
    { key: "ga",   label: "GA"   },
    { key: "gd",   label: "GD"   },
    { key: "pts",  label: "Pts"  },
    { key: "xg",   label: "xG",   note: "Expected Goals" },
    { key: "xga",  label: "xGA",  note: "Expected Goals Against" },
    { key: "xgd",  label: "xGD",  note: "xG Difference" },
    { key: "xpts", label: "xPTS", note: "Expected Points" },
  ];

  return (
    <div className="min-h-screen bg-[#1A202C] text-white" suppressHydrationWarning>
      <div className="border-b border-slate-800/60 bg-[#080b12] px-4 md:px-6 py-4 sticky top-0 z-30 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-black text-xl tracking-tight">NERD ZONE</h1>
          <p className="text-[10px] text-slate-600 uppercase tracking-[0.2em]">{t("nerd.subtitle_alt")}</p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          <select
            value={leagueId}
            onChange={e => setLeagueId(Number(e.target.value))}
            className="bg-[#0d1220] border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-[#10B981]"
          >
            {LEAGUES.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
          </select>
          <select
            value={season}
            onChange={e => setSeason(e.target.value)}
            className="bg-[#0d1220] border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-[#10B981]"
          >
            {SEASONS.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <button
            onClick={() => downloadCSV(sorted, season, leagueName)}
            className="p-2 rounded-lg border border-slate-800 bg-[#0d1220] text-slate-500 hover:text-white transition-colors"
            title={t("nerd.download_csv")}
          >
            <Download size={14} />
          </button>
          {loading && <Loader2 size={16} className="animate-spin text-[#10B981]" />}
        </div>
      </div>

      <div className="px-4 md:px-6 py-6 max-w-7xl mx-auto">
        <p className="text-[10px] text-slate-700 uppercase tracking-widest mb-4">
          Home / {leagueName} / {season}
        </p>

        <div className="overflow-x-auto rounded-xl border border-slate-800/60">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-[#0d1220] border-b border-slate-800/60">
                <th className="px-3 py-3 text-left text-[10px] font-black uppercase tracking-widest text-slate-600 w-8">#</th>
                <th
                  onClick={() => handleSort("name")}
                  className={`px-3 py-3 text-left text-[10px] font-black uppercase tracking-widest cursor-pointer select-none transition-colors hover:text-white ${sortKey === "name" ? "text-white" : "text-slate-500"}`}
                >
                  Club {sortKey === "name" ? (sortDir === "asc" ? "↑" : "↓") : <ArrowUpDown size={8} className="inline ml-0.5 opacity-30" />}
                </th>
                {COLS.map(c => (
                  <th
                    key={c.key}
                    title={c.note}
                    onClick={() => handleSort(c.key)}
                    className={`px-3 py-3 text-right text-[10px] font-black uppercase tracking-widest cursor-pointer select-none whitespace-nowrap transition-colors hover:text-white ${
                      sortKey === c.key ? "text-white" : ["xg","xga","xgd","xpts"].includes(c.key) ? "text-[#60a5fa]" : "text-slate-500"
                    }`}
                  >
                    {c.label}
                    {sortKey === c.key ? (sortDir === "asc" ? " ↑" : " ↓") : ""}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((row, i) => (
                <tr
                  key={row.id}
                  onClick={() => router.push(`/nerd-zone/team/${row.id}?season=${encodeURIComponent(season)}`)}
                  className="border-t border-slate-800/40 hover:bg-[#0d1220] cursor-pointer transition-colors group"
                >
                  <td className="px-3 py-2.5 text-slate-700 font-mono">{i + 1}</td>
                  <td className="px-3 py-2.5 font-semibold text-[#60a5fa] group-hover:text-white transition-colors whitespace-nowrap">{row.name}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-slate-400">{row.mp}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-[#10B981]">{row.w}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-slate-400">{row.d}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-[#EF4444]">{row.l}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-slate-300">{row.gf}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-slate-400">{row.ga}</td>
                  <td className={`px-3 py-2.5 text-right font-mono font-bold ${row.gd >= 0 ? "text-[#10B981]" : "text-[#EF4444]"}`}>
                    {row.gd >= 0 ? "+" : ""}{row.gd}
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono font-bold text-white">{row.pts}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-[#60a5fa] whitespace-nowrap">
                    {row.xg.toFixed(2)}<Delta base={row.xg} actual={row.gf} />
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono text-[#f87171] whitespace-nowrap">
                    {row.xga.toFixed(2)}<Delta base={row.xga} actual={row.ga} />
                  </td>
                  <td className={`px-3 py-2.5 text-right font-mono font-bold ${row.xgd >= 0 ? "text-[#10B981]" : "text-[#EF4444]"}`}>
                    {row.xgd >= 0 ? "+" : ""}{row.xgd.toFixed(2)}
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono text-[#818cf8]">{row.xpts.toFixed(2)}</td>
                </tr>
              ))}
              {!loading && !sorted.length && (
                <tr>
                  <td colSpan={15} className="px-3 py-10 text-center text-xs uppercase tracking-widest" style={{ color: error ? "#ef4444" : undefined }}>
                    {error ? `Error: ${error}` : t("nerd.no_league_data")}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={() => router.push("/nerd-zone/lab")}
            className="text-[10px] text-slate-700 hover:text-[#10B981] uppercase tracking-widest transition-colors"
          >
            {t("nerd.advanced_lab")}
          </button>
        </div>
      </div>
    </div>
  );
}
