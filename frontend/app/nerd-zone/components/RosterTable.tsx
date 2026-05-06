"use client";

import { useMemo, useState } from "react";
import { Download } from "lucide-react";
import { useTranslation } from "react-i18next";
import "../../i18n/config";

export interface RosterRow {
  player:     string;
  position:   string;
  team_name:  string;
  apps:       number;
  minutes:    number;
  goals:      number;
  assists:    number;
  sh90:       number;
  kp90:       number;
  xg:         number;
  xa:         number;
  xg90:       number;
  xa90:       number;
  xgchain:    number;
  xgbuildup:  number;
}

type SortKey = keyof RosterRow;

const ROLE_COLOR: Record<string, string> = {
  FW: "#FF2A6D",
  AM: "#f97316",
  MF: "#eab308",
  DM: "#22c55e",
  DF: "#60a5fa",
  GK: "#a78bfa",
};

interface Props {
  rows:           RosterRow[];
  selectedPlayer: string | null;
  onSelectPlayer: (name: string) => void;
  sortKey:        SortKey;
  sortDir:        "asc" | "desc";
  onSort:         (key: SortKey) => void;
}

function Delta({ xg, goals }: { xg: number; goals: number }) {
  const delta = goals - xg;
  const color = delta >= 0 ? "#10B981" : "#EF4444";
  return (
    <sup className="ml-0.5 text-[9px] font-black" style={{ color }}>
      {delta >= 0 ? "+" : ""}{delta.toFixed(2)}
    </sup>
  );
}

export default function RosterTable({
  rows, selectedPlayer, onSelectPlayer, sortKey, sortDir, onSort,
}: Props) {
  const { t } = useTranslation();
  const sorted = useMemo(() => {
    return [...rows].sort((a, b) => {
      const av = a[sortKey] ?? "";
      const bv = b[sortKey] ?? "";
      const diff = av < bv ? -1 : av > bv ? 1 : 0;
      return sortDir === "asc" ? diff : -diff;
    });
  }, [rows, sortKey, sortDir]);

  function handleCSV() {
    const headers = ["#","Player","Pos","Team","Apps","Min","G","A","Sh90","KP90","xG","xA","xG90","xA90","xGChain","xGBuild"];
    const csvRows = sorted.map((r, i) =>
      [i+1, r.player, r.position, r.team_name, r.apps, r.minutes,
       r.goals, r.assists, r.sh90.toFixed(2), r.kp90.toFixed(2),
       r.xg.toFixed(2), r.xa.toFixed(2), r.xg90.toFixed(3), r.xa90.toFixed(3),
       r.xgchain.toFixed(2), r.xgbuildup.toFixed(2)].join(",")
    );
    const blob = new Blob([headers.join(",") + "\n" + csvRows.join("\n")], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "roster.csv";
    a.click();
  }

  if (!sorted.length) {
    return (
      <div className="flex items-center justify-center h-32 text-slate-700 text-xs uppercase tracking-widest" suppressHydrationWarning>
        {t("common.no_data")}
      </div>
    );
  }

  const HEADER_COLS: { key: SortKey; label: string; left?: boolean }[] = [
    { key: "player",    label: "Player",  left: true },
    { key: "position",  label: "Pos"     },
    { key: "team_name", label: "Team",   left: true },
    { key: "apps",      label: "Apps"    },
    { key: "minutes",   label: "Min"     },
    { key: "goals",     label: "G"       },
    { key: "assists",   label: "A"       },
    { key: "sh90",      label: "Sh90"   },
    { key: "kp90",      label: "KP90"   },
    { key: "xg",        label: "xG"      },
    { key: "xa",        label: "xA"      },
    { key: "xg90",      label: "xG90"   },
    { key: "xa90",      label: "xA90"   },
    { key: "xgchain",   label: "xGChain" },
    { key: "xgbuildup", label: "xGBuild" },
  ];

  return (
    <div suppressHydrationWarning>
      <div className="flex justify-end mb-2">
        <button
          onClick={handleCSV}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-800 bg-[#0d1220] text-[10px] text-slate-500 hover:text-white transition-colors"
        >
          <Download size={11} /> {t("nerd.download_csv")}
        </button>
      </div>
      <div className="overflow-x-auto rounded-xl border border-slate-800/60">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-[#0d1220] border-b border-slate-800">
              <th className="px-3 py-3 text-left text-[10px] font-black uppercase tracking-widest text-slate-700 whitespace-nowrap">
                #
              </th>
              {HEADER_COLS.map(col => (
                <th
                  key={col.key}
                  onClick={() => onSort(col.key)}
                  className={`px-3 py-3 text-[10px] font-black uppercase tracking-widest cursor-pointer select-none whitespace-nowrap transition-colors hover:text-white ${
                    sortKey === col.key ? "text-white" : "text-slate-500"
                  } ${col.left ? "text-left" : "text-right"}`}
                >
                  {col.label}
                  {sortKey === col.key ? (sortDir === "asc" ? " ↑" : " ↓") : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, i) => {
              const pos = row.position.toUpperCase();
              const roleColor = ROLE_COLOR[pos];
              const isSelected = row.player === selectedPlayer;
              return (
                <tr
                  key={row.player}
                  onClick={() => onSelectPlayer(row.player)}
                  className={`border-t border-slate-800/40 cursor-pointer transition-colors ${
                    isSelected
                      ? "bg-[#10B981]/8 border-l-2 border-l-[#10B981]"
                      : "hover:bg-[#0d1220]"
                  }`}
                >
                  <td className="px-3 py-2.5 text-slate-700 font-mono text-[11px]">{i + 1}</td>
                  <td className="px-3 py-2.5 font-semibold text-white whitespace-nowrap text-left">
                    {row.player}
                  </td>
                  <td className="px-3 py-2.5 whitespace-nowrap text-right">
                    {pos && (
                      <span
                        className="text-[10px] font-black px-1.5 py-0.5 rounded"
                        style={{
                          background: (roleColor ?? "#64748b") + "28",
                          color: roleColor ?? "#94a3b8",
                        }}
                      >
                        {pos}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-slate-500 text-xs whitespace-nowrap text-left">
                    {row.team_name || "—"}
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono text-[11px] text-slate-400">
                    {row.apps ?? "—"}
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono text-[11px] text-slate-400">
                    {(row.minutes ?? 0).toLocaleString()}
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono text-[11px] text-slate-300">{row.goals}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-[11px] text-slate-400">{row.assists}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-[11px] text-slate-400">{row.sh90.toFixed(2)}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-[11px] text-slate-400">{row.kp90.toFixed(2)}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-[11px] text-[#60a5fa]">
                    {row.xg.toFixed(2)}<Delta xg={row.xg} goals={row.goals} />
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono text-[11px] text-[#818cf8]">
                    {row.xa.toFixed(2)}<Delta xg={row.xa} goals={row.assists} />
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono text-[11px] text-[#60a5fa]">{row.xg90.toFixed(3)}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-[11px] text-[#818cf8]">{row.xa90.toFixed(3)}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-[11px] text-slate-400">{row.xgchain.toFixed(2)}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-[11px] text-slate-400">{row.xgbuildup.toFixed(2)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
