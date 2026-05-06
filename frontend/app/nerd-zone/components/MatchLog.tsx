"use client";

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import "../../i18n/config";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface LogRow {
  date:       string;
  home_team:  string;
  away_team:  string;
  home_goals: number | null;
  away_goals: number | null;
  position:   string;
  minutes:    number;
  shots:      number;
  goals:      number;
  key_passes: number;
  assists:    number;
  xg:         number;
  xa:         number;
  is_home:    boolean;
}

interface LogResp {
  total: number;
  page:  number;
  pages: number;
  rows:  LogRow[];
}

interface Totals {
  minutes: number;
  shots:   number;
  goals:   number;
  kp:      number;
  assists: number;
  xg:      number;
  xa:      number;
}

interface Props {
  player:    string;
  season:    string;
  leagueIds: number[];
}

function Delta({ xg, actual }: { xg: number; actual: number }) {
  const d = actual - xg;
  const sign = d >= 0 ? "+" : "";
  const color = d >= 0 ? "#10B981" : "#EF4444";
  return <sup className="ml-0.5 text-[9px] font-black" style={{ color }}>{sign}{d.toFixed(2)}</sup>;
}

export default function MatchLog({ player, season, leagueIds }: Props) {
  const { t } = useTranslation();
  const [data, setData]   = useState<LogResp | null>(null);
  const [page, setPage]   = useState(1);
  const [loading, setL]   = useState(false);

  useEffect(() => {
    if (!player) return;
    setL(true);
    const p = new URLSearchParams({ player, season, page: String(page) });
    leagueIds.forEach(id => p.append("league_ids", String(id)));
    fetch(`${API_BASE}/api/nerd-zone/player-match-log?${p}`)
      .then(r => r.json())
      .then(setData)
      .finally(() => setL(false));
  }, [player, season, leagueIds.join(","), page]);

  // Reset page when player/season changes
  useEffect(() => { setPage(1); }, [player, season]);

  const rows = data?.rows ?? [];

  const totals: Totals = rows.reduce(
    (acc, r) => ({
      minutes: acc.minutes + r.minutes,
      shots:   acc.shots   + r.shots,
      goals:   acc.goals   + r.goals,
      kp:      acc.kp      + r.key_passes,
      assists: acc.assists  + r.assists,
      xg:      acc.xg      + r.xg,
      xa:      acc.xa      + r.xa,
    }),
    { minutes: 0, shots: 0, goals: 0, kp: 0, assists: 0, xg: 0, xa: 0 }
  );

  const pages = data?.pages ?? 1;

  function pageButtons() {
    const btns: (number | "…")[] = [];
    if (pages <= 7) {
      for (let i = 1; i <= pages; i++) btns.push(i);
    } else {
      [1, 2, 3, 4, 5].forEach(n => btns.push(n));
      btns.push("…");
      btns.push(pages);
    }
    return btns;
  }

  return (
    <div className="space-y-3" suppressHydrationWarning>
      <div className="overflow-x-auto rounded-xl border border-slate-800/60">
        {loading ? (
          <div className="flex items-center justify-center h-28 text-slate-700 text-xs uppercase tracking-widest">{t("common.loading")}</div>
        ) : !rows.length ? (
          <div className="flex items-center justify-center h-28 text-slate-800 text-xs uppercase tracking-widest">{t("nerd.no_match_data")}</div>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-[#0d1220]">
                {["#","Date","Home","Score","Away","Pos","Min","Sh","G","KP","A","xG","xA"].map(h => (
                  <th key={h} className={`px-3 py-2.5 font-black uppercase tracking-widest text-[10px] text-slate-500 whitespace-nowrap ${
                    ["#","Pos","Min","Sh","G","KP","A","xG","xA"].includes(h) ? "text-right" : "text-left"
                  }`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => {
                const scoreStr = row.home_goals != null && row.away_goals != null
                  ? `${row.home_goals}–${row.away_goals}`
                  : "–";
                const teamGoals = row.is_home ? row.home_goals : row.away_goals;
                const oppGoals  = row.is_home ? row.away_goals : row.home_goals;
                const outcome   = teamGoals != null && oppGoals != null
                  ? teamGoals > oppGoals ? "W" : teamGoals < oppGoals ? "L" : "D"
                  : null;
                const outColor  = outcome === "W" ? "#10B981" : outcome === "L" ? "#EF4444" : "#f59e0b";
                return (
                  <tr key={i} className="border-t border-slate-800/40 hover:bg-[#0d1220] transition-colors">
                    <td className="px-3 py-2 text-right text-slate-700 font-mono">{(page - 1) * 10 + i + 1}</td>
                    <td className="px-3 py-2 text-left text-slate-400 whitespace-nowrap font-mono text-[11px]">{row.date}</td>
                    <td className="px-3 py-2 text-left whitespace-nowrap">
                      <span className={`font-semibold ${row.is_home ? "text-white" : "text-slate-400"}`}>{row.home_team}</span>
                    </td>
                    <td className="px-3 py-2 text-left font-mono font-bold whitespace-nowrap" style={{ color: outColor }}>
                      {scoreStr}
                    </td>
                    <td className="px-3 py-2 text-left whitespace-nowrap">
                      <span className={`font-semibold ${!row.is_home ? "text-white" : "text-slate-400"}`}>{row.away_team}</span>
                    </td>
                    <td className="px-3 py-2 text-right">
                      <span className="text-[10px] font-black text-slate-400 bg-slate-800/50 px-1.5 py-0.5 rounded">
                        {row.position}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-slate-400">{row.minutes}</td>
                    <td className="px-3 py-2 text-right font-mono text-slate-400">{row.shots}</td>
                    <td className="px-3 py-2 text-right font-mono text-slate-300">{row.goals}</td>
                    <td className="px-3 py-2 text-right font-mono text-slate-400">{row.key_passes}</td>
                    <td className="px-3 py-2 text-right font-mono text-slate-400">{row.assists}</td>
                    <td className="px-3 py-2 text-right font-mono text-[#60a5fa] whitespace-nowrap">
                      {row.xg.toFixed(2)}
                      <Delta xg={row.xg} actual={row.goals} />
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-[#818cf8] whitespace-nowrap">
                      {row.xa.toFixed(2)}
                      <Delta xg={row.xa} actual={row.assists} />
                    </td>
                  </tr>
                );
              })}

              {/* Totals row */}
              <tr className="border-t-2 border-slate-700 bg-[#0d1220] font-bold">
                <td colSpan={6} className="px-3 py-2 text-slate-600 text-[10px] uppercase tracking-widest">{t("nerd.total")}</td>
                <td className="px-3 py-2 text-right font-mono text-slate-300">{totals.minutes.toLocaleString()}</td>
                <td className="px-3 py-2 text-right font-mono text-slate-300">{totals.shots}</td>
                <td className="px-3 py-2 text-right font-mono text-white">{totals.goals}</td>
                <td className="px-3 py-2 text-right font-mono text-slate-300">{totals.kp}</td>
                <td className="px-3 py-2 text-right font-mono text-slate-300">{totals.assists}</td>
                <td className="px-3 py-2 text-right font-mono text-[#60a5fa] whitespace-nowrap">
                  {totals.xg.toFixed(2)}
                  <Delta xg={totals.xg} actual={totals.goals} />
                </td>
                <td className="px-3 py-2 text-right font-mono text-[#818cf8] whitespace-nowrap">
                  {totals.xa.toFixed(2)}
                  <Delta xg={totals.xa} actual={totals.assists} />
                </td>
              </tr>
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex items-center justify-end gap-1.5">
          {pageButtons().map((btn, i) =>
            btn === "…" ? (
              <span key={`ellipsis-${i}`} className="text-slate-700 px-1 text-sm">…</span>
            ) : (
              <button
                key={btn}
                onClick={() => setPage(btn as number)}
                className={`w-8 h-8 rounded-lg text-xs font-black transition-all ${
                  page === btn
                    ? "bg-[#10B981] text-white shadow-[0_0_8px_#10B98160]"
                    : "bg-[#0d1220] border border-slate-800 text-slate-500 hover:text-white"
                }`}
              >
                {btn}
              </button>
            )
          )}
        </div>
      )}
    </div>
  );
}
