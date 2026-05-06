"use client";

import { useEffect, useState } from "react";
import { Download } from "lucide-react";
import { useTranslation } from "react-i18next";
import "../../i18n/config";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const TABS = [
  { id: "situation",    labelKey: "nerd.tab_situation"    },
  { id: "formation",    labelKey: "nerd.tab_formation"    },
  { id: "game_state",   labelKey: "nerd.tab_game_state"   },
  { id: "timing",       labelKey: "nerd.tab_timing"       },
  { id: "zones",        labelKey: "nerd.tab_shot_zones"   },
  { id: "attack_speed", labelKey: "nerd.tab_attack_speed" },
  { id: "result",       labelKey: "nerd.tab_result"       },
] as const;

export type TabId = typeof TABS[number]["id"];

interface StatRow {
  dimension:   string;
  sh:          number;
  g:           number;
  sha:         number;
  ga:          number;
  xg:          number;
  xga:         number;
  xgd:         number;
  xg_per_sh:   number;
  xga_per_sha: number;
}

interface Props {
  teamId:      number;
  season:      string;
  tab:         TabId;
  onTabChange: (t: TabId) => void;
}

function DeltaSup({ base, actual }: { base: number; actual: number }) {
  const delta = actual - base;
  const color = delta >= 0 ? "#10B981" : "#EF4444";
  return (
    <sup className="ml-0.5 text-[9px] font-black" style={{ color }}>
      {delta >= 0 ? "+" : ""}{delta.toFixed(2)}
    </sup>
  );
}

function downloadCSV(rows: StatRow[], tab: string) {
  const headers = ["Dimension","Sh","G","ShA","GA","xG","xGA","xGD","xG/Sh","xGA/Sh"];
  const csvRows = rows.map(r =>
    [r.dimension, r.sh, r.g, r.sha, r.ga, r.xg, r.xga, r.xgd, r.xg_per_sh, r.xga_per_sha].join(",")
  );
  const blob = new Blob([headers.join(",") + "\n" + csvRows.join("\n")], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `team_stats_${tab}.csv`;
  a.click();
}

export default function TeamSituationTable({ teamId, season, tab, onTabChange }: Props) {
  const { t } = useTranslation();
  const [rows, setRows]       = useState<StatRow[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!teamId) return;
    setLoading(true);
    fetch(
      `${API_BASE}/api/nerd-zone/team-stats?team_id=${teamId}&tab=${tab}&season=${encodeURIComponent(season)}`,
      { cache: "no-store" }
    )
      .then(r => r.json())
      .then(setRows)
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, [teamId, tab, season]);

  const noData = ["formation", "game_state", "attack_speed"].includes(tab);

  const dimLabel =
    tab === "timing" ? "Period" :
    tab === "zones"  ? "Zone"   :
    tab === "result" ? "Result" : "Situation";

  return (
    <div className="bg-[#08090f] border border-slate-800/60 rounded-2xl overflow-hidden" suppressHydrationWarning>
      {/* Tab bar + CSV */}
      <div className="flex items-center border-b border-slate-800/60 justify-between">
        <div className="flex overflow-x-auto">
          {TABS.map(tabObj => (
            <button
              key={tabObj.id}
              onClick={() => onTabChange(tabObj.id)}
              className={`relative px-4 py-3 text-[11px] font-black uppercase tracking-widest whitespace-nowrap transition-colors ${
                tab === tabObj.id ? "text-white" : "text-slate-600 hover:text-slate-400"
              }`}
            >
              {t(tabObj.labelKey)}
              {tab === tabObj.id && (
                <span className="absolute bottom-0 left-0 w-full h-0.5 bg-[#10B981] rounded-t shadow-[0_0_6px_#10B981]" />
              )}
            </button>
          ))}
        </div>
        <button
          onClick={() => downloadCSV(rows, tab)}
          disabled={!rows.length}
          className="p-2 mr-3 rounded-lg border border-slate-800 bg-[#0d1220] text-slate-600 hover:text-white transition-colors disabled:opacity-30"
          title={t("nerd.download_csv")}
        >
          <Download size={13} />
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto min-h-[120px]">
        {loading ? (
          <div className="flex items-center justify-center h-28 text-slate-700 text-xs uppercase tracking-widest">{t("common.loading")}</div>
        ) : noData || !rows.length ? (
          <div className="flex items-center justify-center h-28 text-slate-800 text-xs uppercase tracking-widest">
            {noData ? t("nerd.data_not_available") : t("common.no_data")}
          </div>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-[#0d1220]">
                <th className="px-3 py-2.5 text-left text-[10px] font-black uppercase tracking-widest text-slate-600 w-6">#</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-black uppercase tracking-widest text-slate-500">
                  {dimLabel}
                </th>
                {[
                  ["Sh",      "text-slate-400"],
                  ["G",       "text-slate-300"],
                  ["ShA",     "text-slate-400"],
                  ["GA",      "text-slate-400"],
                  ["xG",      "text-[#60a5fa]"],
                  ["xGA",     "text-[#f87171]"],
                  ["xGD",     "text-slate-300"],
                  ["xG/Sh",   "text-slate-500"],
                  ["xGA/ShA", "text-slate-500"],
                ].map(([label, color]) => (
                  <th key={label} className={`px-3 py-2.5 text-right text-[10px] font-black uppercase tracking-widest whitespace-nowrap ${color}`}>
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={row.dimension} className="border-t border-slate-800/40 hover:bg-[#0d1220] transition-colors">
                  <td className="px-3 py-2 text-slate-700 font-mono">{i + 1}</td>
                  <td className="px-3 py-2 font-semibold text-white whitespace-nowrap">{row.dimension}</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-400">{row.sh}</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-300">{row.g}</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-400">{row.sha}</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-400">{row.ga}</td>
                  <td className="px-3 py-2 text-right font-mono text-[#60a5fa] whitespace-nowrap">
                    {row.xg.toFixed(2)}<DeltaSup base={row.xg} actual={row.g} />
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-[#f87171] whitespace-nowrap">
                    {row.xga.toFixed(2)}<DeltaSup base={row.xga} actual={row.ga} />
                  </td>
                  <td className={`px-3 py-2 text-right font-mono font-bold whitespace-nowrap ${row.xgd >= 0 ? "text-[#10B981]" : "text-[#EF4444]"}`}>
                    {row.xgd >= 0 ? "+" : ""}{row.xgd.toFixed(2)}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-slate-500">{row.xg_per_sh.toFixed(3)}</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-500">{row.xga_per_sha.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
