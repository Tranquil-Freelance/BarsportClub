"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { useTranslation } from "react-i18next";
import "../../i18n/config";
import ShotMap from "./ShotMap";

const RadarEcharts = dynamic(() => import("./RadarEcharts"), { ssr: false });

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const HISTORY_TABS = [
  { id: "season",    labelKey: "nerd.drilldown_season"    },
  { id: "position",  labelKey: "nerd.drilldown_position"  },
  { id: "situation", labelKey: "nerd.drilldown_situation" },
] as const;

type HistoryTab = typeof HISTORY_TABS[number]["id"];

interface HistoryRow {
  label: string;
  [key: string]: number | string;
}

interface Shot {
  x: number;
  y: number;
  xg: number;
  result: string;
  situation: string;
  minute: number;
}

interface RadarData {
  name: string;
  xG_p90: number;
  xA_p90: number;
  shots_p90: number;
  key_passes_p90: number;
  xGChain_p90: number;
  xGBuildup_p90: number;
  goals_p90: number;
  assists_p90: number;
}

interface Props {
  player: string;
  leagueIds: number[];
  season: string;
  onClose: () => void;
}

const SEASON_HISTORY_COLS = [
  { key: "label",   label: "Season"  },
  { key: "matches", label: "MP"      },
  { key: "minutes", label: "Min"     },
  { key: "goals",   label: "G"       },
  { key: "assists", label: "A"       },
  { key: "shots",   label: "Sh"      },
  { key: "xg",      label: "xG"      },
  { key: "xa",      label: "xA"      },
  { key: "xg90",    label: "xG90"    },
  { key: "xa90",    label: "xA90"    },
];

const SITUATION_COLS = [
  { key: "label",          label: "Situation"  },
  { key: "shots",          label: "Shots"      },
  { key: "goals",          label: "Goals"      },
  { key: "xg",             label: "xG"         },
  { key: "xg_per_shot",    label: "xG/Shot"    },
  { key: "conversion_pct", label: "Conv%"      },
];

function historyColsFor(tab: HistoryTab) {
  return tab === "situation" ? SITUATION_COLS : SEASON_HISTORY_COLS;
}

function cellVal(val: number | string, key: string): string {
  if (key === "label") return String(val);
  if (key === "minutes") return Number(val).toLocaleString();
  if (typeof val === "number") {
    if (["matches", "goals", "assists", "shots"].includes(key)) return String(val);
    if (key === "conversion_pct") return `${val.toFixed(1)}%`;
    if (["xg90", "xa90", "xg_per_shot"].includes(key)) return val.toFixed(3);
    return val.toFixed(2);
  }
  return String(val);
}

export default function PlayerDrilldown({ player, leagueIds, season, onClose }: Props) {
  const { t } = useTranslation();
  const [historyTab, setHistoryTab] = useState<HistoryTab>("season");
  const [history, setHistory]       = useState<HistoryRow[]>([]);
  const [shots, setShots]           = useState<Shot[]>([]);
  const [radar, setRadar]           = useState<RadarData | null>(null);
  const [loadingH, setLoadingH]     = useState(false);
  const [loadingS, setLoadingS]     = useState(false);

  // Fetch history whenever player/tab/filters change
  useEffect(() => {
    if (!player) return;
    setLoadingH(true);
    const p = new URLSearchParams({ player, tab: historyTab });
    leagueIds.forEach(id => p.append("league_ids", String(id)));
    fetch(`${API_BASE}/api/nerd-zone/player-history?${p}`)
      .then(r => r.json())
      .then(setHistory)
      .finally(() => setLoadingH(false));
  }, [player, historyTab, leagueIds.join(",")]);

  // Fetch shots & radar on player/filters change
  useEffect(() => {
    if (!player) return;
    setLoadingS(true);
    const p = new URLSearchParams({ player, season });
    leagueIds.forEach(id => p.append("league_ids", String(id)));

    Promise.all([
      fetch(`${API_BASE}/api/nerd-zone/player-shots?${p}`).then(r => r.json()),
      fetch(`${API_BASE}/api/nerd-zone/player-radar?${p}`).then(r => r.json()),
    ])
      .then(([s, r]) => {
        setShots(s);
        setRadar(r);
      })
      .finally(() => setLoadingS(false));
  }, [player, leagueIds.join(","), season]);

  const cols = historyColsFor(historyTab);

  return (
    <div className="border-t border-slate-800/60 bg-[#06080e] pt-6 pb-8 px-4 md:px-6" suppressHydrationWarning>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="font-black text-xl tracking-tight text-white">{player}</h2>
          <p className="text-[10px] text-slate-600 uppercase tracking-[0.2em]">{t("nerd.drilldown_title")}</p>
        </div>
        <button
          onClick={onClose}
          className="text-slate-600 hover:text-white transition-colors text-sm px-3 py-1.5 border border-slate-800 rounded-lg"
        >
          ✕ {t("common.close")}
        </button>
      </div>

      {/* 3-column grid: History | Radar | Shot Map */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

        {/* A — Historical Table */}
        <div className="xl:col-span-1 space-y-3">
          <div className="flex border-b border-slate-800/60">
            {HISTORY_TABS.map(tab => (
              <button
                key={tab.id}
                onClick={() => setHistoryTab(tab.id)}
                className={`relative px-4 py-2.5 text-[10px] font-black uppercase tracking-widest transition-colors ${
                  historyTab === tab.id ? "text-white" : "text-slate-600 hover:text-slate-400"
                }`}
              >
                {t(tab.labelKey)}
                {historyTab === tab.id && (
                  <span className="absolute bottom-0 left-0 w-full h-0.5 bg-[#10B981] rounded-t" />
                )}
              </button>
            ))}
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800/60">
            {loadingH ? (
              <div className="flex items-center justify-center h-28 text-slate-700 text-xs">{t("common.loading")}</div>
            ) : !history.length ? (
              <div className="flex items-center justify-center h-28 text-slate-800 text-xs">{t("common.no_data")}</div>
            ) : (
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-[#0d1220]">
                    {cols.map(c => (
                      <th
                        key={c.key}
                        className={`px-3 py-2.5 font-black uppercase tracking-widest text-slate-500 text-[10px] whitespace-nowrap ${
                          c.key === "label" ? "text-left" : "text-right"
                        }`}
                      >
                        {c.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {history.map((row, i) => (
                    <tr key={i} className="border-t border-slate-800/40 hover:bg-[#0d1220] transition-colors">
                      {cols.map(c => (
                        <td
                          key={c.key}
                          className={`px-3 py-2 font-mono text-[11px] whitespace-nowrap ${
                            c.key === "label"
                              ? "text-left text-white font-semibold"
                              : "text-right text-slate-400"
                          }`}
                        >
                          {cellVal(row[c.key], c.key)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* B — Radar Chart */}
        <div className="xl:col-span-1">
          <p className="text-[10px] font-black tracking-widest uppercase text-slate-600 mb-3">{t("nerd.radar_profile")}</p>
          {loadingS || !radar ? (
            <div className="flex items-center justify-center h-64 text-slate-800 text-xs bg-[#0a0e17] border border-slate-800/60 rounded-2xl">
              {loadingS ? t("common.loading") : t("nerd.no_radar")}
            </div>
          ) : (
            <RadarEcharts data={radar} />
          )}
        </div>

        {/* C — Shot Map */}
        <div className="xl:col-span-1">
          <p className="text-[10px] font-black tracking-widest uppercase text-slate-600 mb-3">{t("nerd.shot_map")}</p>
          {loadingS ? (
            <div className="flex items-center justify-center h-64 text-slate-800 text-xs bg-[#0a0e17] border border-slate-800/60 rounded-2xl">
              {t("common.loading")}
            </div>
          ) : !shots.length ? (
            <div className="flex items-center justify-center h-64 text-slate-800 text-xs bg-[#0a0e17] border border-slate-800/60 rounded-2xl">
              {t("nerd.no_shots_season")}
            </div>
          ) : (
            <ShotMap shots={shots} />
          )}
        </div>
      </div>
    </div>
  );
}
