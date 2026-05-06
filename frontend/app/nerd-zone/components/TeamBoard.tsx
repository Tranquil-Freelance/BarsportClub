"use client";

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import "../../i18n/config";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const TABS = [
  { id: "situation", labelKey: "nerd.tab_situation"  },
  { id: "timing",    labelKey: "nerd.tab_timing"     },
  { id: "zones",     labelKey: "nerd.tab_shot_zones" },
  { id: "result",    labelKey: "nerd.tab_result"     },
] as const;

type TabId = typeof TABS[number]["id"];

interface BoardRow {
  dimension: string;
  shots: number;
  goals: number;
  xg: number;
  xg_per_shot: number;
  conversion_pct: number;
}

interface BoardData {
  dim_label: string;
  rows: BoardRow[];
}

interface Props {
  tab: TabId;
  onTabChange: (t: TabId) => void;
  leagueIds: number[];
  season: string;
}

function Delta({ xg, goals }: { xg: number; goals: number }) {
  const delta = goals - xg;
  const sign  = delta >= 0 ? "+" : "";
  const color = delta >= 0 ? "#10B981" : "#EF4444";
  return (
    <sup
      className="ml-0.5 text-[9px] font-black"
      style={{ color }}
      title={`Goals − xG = ${sign}${delta.toFixed(2)}`}
    >
      {sign}{delta.toFixed(2)}
    </sup>
  );
}

export default function TeamBoard({ tab, onTabChange, leagueIds, season }: Props) {
  const { t } = useTranslation();
  const [data, setData] = useState<BoardData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!leagueIds.length) return;
    setLoading(true);
    const p = new URLSearchParams({ tab, season });
    leagueIds.forEach(id => p.append("league_ids", String(id)));
    fetch(`${API_BASE}/api/nerd-zone/team-board?${p}`)
      .then(r => r.json())
      .then(setData)
      .finally(() => setLoading(false));
  }, [tab, leagueIds.join(","), season]);

  return (
    <div className="bg-[#08090f] border border-slate-800/60 rounded-2xl overflow-hidden" suppressHydrationWarning>
      {/* Tab bar */}
      <div className="flex border-b border-slate-800/60 overflow-x-auto">
        {TABS.map(tabObj => (
          <button
            key={tabObj.id}
            onClick={() => onTabChange(tabObj.id)}
            className={`relative px-5 py-3.5 text-[11px] font-black uppercase tracking-widest transition-colors whitespace-nowrap ${
              tab === tabObj.id ? "text-white" : "text-slate-600 hover:text-slate-400"
            }`}
          >
            {t(tabObj.labelKey)}
            {tab === tabObj.id && (
              <span className="absolute bottom-0 left-0 w-full h-0.5 bg-[#10B981] rounded-t shadow-[0_0_8px_#10B981]" />
            )}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="overflow-x-auto min-h-[140px]">
        {loading ? (
          <div className="flex items-center justify-center h-32 text-slate-700 text-xs uppercase tracking-widest">
            {t("common.loading")}
          </div>
        ) : !data?.rows.length ? (
          <div className="flex items-center justify-center h-32 text-slate-800 text-xs uppercase tracking-widest">
            {t("common.no_data")}
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[#0d1220]">
                <th className="px-4 py-2.5 text-left text-[10px] font-black uppercase tracking-widest text-slate-500">
                  {data.dim_label.toUpperCase()}
                </th>
                <th className="px-4 py-2.5 text-right text-[10px] font-black uppercase tracking-widest text-slate-500">Shots</th>
                <th className="px-4 py-2.5 text-right text-[10px] font-black uppercase tracking-widest text-slate-500">Goals</th>
                <th className="px-4 py-2.5 text-right text-[10px] font-black uppercase tracking-widest text-slate-500">xG</th>
                <th className="px-4 py-2.5 text-right text-[10px] font-black uppercase tracking-widest text-slate-500">xG/Shot</th>
                <th className="px-4 py-2.5 text-right text-[10px] font-black uppercase tracking-widest text-slate-500">Conv%</th>
              </tr>
            </thead>
            <tbody>
              {data.rows.map((row, i) => (
                <tr
                  key={row.dimension}
                  className="border-t border-slate-800/40 hover:bg-[#0d1220] transition-colors"
                >
                  <td className="px-4 py-2.5 font-semibold text-white text-sm whitespace-nowrap">{row.dimension}</td>
                  <td className="px-4 py-2.5 text-right font-mono text-[11px] text-slate-400">{row.shots.toLocaleString()}</td>
                  <td className="px-4 py-2.5 text-right font-mono text-[11px] text-slate-300">{row.goals}</td>
                  <td className="px-4 py-2.5 text-right font-mono text-[11px] text-[#60a5fa]">
                    {row.xg.toFixed(1)}
                    <Delta xg={row.xg} goals={row.goals} />
                  </td>
                  <td className="px-4 py-2.5 text-right font-mono text-[11px] text-slate-400">{row.xg_per_shot.toFixed(3)}</td>
                  <td className="px-4 py-2.5 text-right font-mono text-[11px] text-slate-400">{row.conversion_pct.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
