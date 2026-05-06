"use client";

import { useEffect, useRef, useState } from "react";
import ReactECharts from "echarts-for-react";
import { useTranslation } from "react-i18next";
import "../../i18n/config";

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

interface Axis {
  key: keyof RadarData;
  label: string;
  max: number;
}

const ALL_AXES: Axis[] = [
  { key: "xG_p90",         label: "xG/90",      max: 0.80 },
  { key: "xA_p90",         label: "xA/90",      max: 0.50 },
  { key: "goals_p90",      label: "Goals/90",   max: 0.70 },
  { key: "assists_p90",    label: "Assist/90",  max: 0.45 },
  { key: "shots_p90",      label: "Shots/90",   max: 5.00 },
  { key: "key_passes_p90", label: "KP/90",      max: 3.50 },
  { key: "xGChain_p90",    label: "Chain/90",   max: 1.50 },
  { key: "xGBuildup_p90",  label: "Build/90",   max: 1.20 },
];

interface Props {
  data: RadarData;
}

export default function RadarEcharts({ data }: Props) {
  const { t } = useTranslation();
  const [activeAxes, setActiveAxes] = useState<Set<string>>(
    new Set(ALL_AXES.map(a => a.key))
  );

  function toggleAxis(key: string) {
    setActiveAxes(prev => {
      const next = new Set(prev);
      if (next.has(key)) {
        if (next.size <= 3) return prev; // minimum 3 axes
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  const visibleAxes = ALL_AXES.filter(a => activeAxes.has(a.key));

  const indicators = visibleAxes.map(a => ({ name: a.label, max: 100 }));

  const values = visibleAxes.map(a => {
    const raw = (data[a.key] as number) ?? 0;
    return Math.min(100, Math.round((raw / a.max) * 100));
  });

  const option = {
    backgroundColor: "transparent",
    radar: {
      indicator: indicators,
      shape: "polygon",
      splitNumber: 4,
      center: ["50%", "50%"],
      radius: "68%",
      axisName: {
        color: "#64748b",
        fontSize: 11,
        fontWeight: 700,
      },
      splitLine: {
        lineStyle: { color: "#1e2a3a", width: 1 },
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ["#0d1220", "#090c14"],
        },
      },
      axisLine: {
        lineStyle: { color: "#1e2a3a" },
      },
    },
    series: [
      {
        type: "radar",
        data: [
          {
            value: values,
            name: data.name,
            symbol: "circle",
            symbolSize: 5,
            lineStyle: { color: "#10B981", width: 2 },
            areaStyle: {
              color: "rgba(16, 185, 129, 0.18)",
            },
            itemStyle: { color: "#10B981" },
            label: {
              show: false,
            },
          },
        ],
        tooltip: {
          trigger: "item",
          formatter: (params: any) => {
            const vals = params.value as number[];
            return visibleAxes
              .map((a, i) => `${a.label}: <b>${vals[i]}%</b>`)
              .join("<br/>");
          },
        },
      },
    ],
    tooltip: {
      backgroundColor: "#0a0e17",
      borderColor: "#1e293b",
      textStyle: { color: "#cbd5e1", fontSize: 11 },
    },
  };

  return (
    <div className="space-y-4" suppressHydrationWarning>
      {/* Axis toggle buttons */}
      <div>
        <p className="text-[10px] font-black tracking-widest uppercase text-slate-600 mb-2">
          {t("nerd.toggle_axes")}
        </p>
        <div className="flex flex-wrap gap-1.5">
          {ALL_AXES.map(a => {
            const active = activeAxes.has(a.key);
            return (
              <button
                key={a.key}
                onClick={() => toggleAxis(a.key)}
                className={`px-2.5 py-1 rounded-md text-[10px] font-black uppercase tracking-wider border transition-all ${
                  active
                    ? "bg-[#10B981]/15 border-[#10B981]/40 text-[#10B981]"
                    : "bg-[#0d1220] border-slate-800 text-slate-600 hover:text-slate-400"
                }`}
              >
                {a.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Chart */}
      <div className="bg-[#0a0e17] border border-slate-800/60 rounded-2xl p-4">
        <ReactECharts
          option={option}
          style={{ height: 340 }}
          notMerge
          lazyUpdate
        />
        <p className="text-[10px] text-slate-700 text-right mt-1">
          {t("nerd.radar_normalized")}
        </p>
      </div>
    </div>
  );
}
