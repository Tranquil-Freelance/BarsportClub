"use client";

import React, { useState, useEffect } from "react";
import { Activity, Loader2, AlertTriangle, ArrowUp, ArrowDown, Minus } from "lucide-react";
import { useTranslation } from "react-i18next";
import "../../i18n/config";
import type { LeagueId } from "@/app/fanta-draft/page";

const FANTA_API = "http://localhost:8000/api/fanta";

interface StartSitViewProps {
  league: LeagueId;
}

type ApiPlayer = {
  player: string;
  player_id: string;
  position: string;
  team: string;
  matches: number;
  goals: number;
  assists: number;
  minutes: number;
  xg_p90: number;
  xa_p90: number;
  shots_p90: number;
  efo: number;
  luck_index: number;
  titolarita_pct: number;
  is_breakout: boolean;
};

type Verdetto = "TITOLARE" | "SÌ" | "DUBBIO" | "SORVEGLIATO" | "PANCHINA";

interface TableRow {
  player: string;
  team: string;
  position: string;
  titolarita_pct: number;
  efo: number;
  luck_index: number;
  is_breakout: boolean;
  verdetto: Verdetto;
}

function computeVerdetto(p: ApiPlayer): Verdetto {
  if (p.efo >= 4.0) return "TITOLARE";
  if (p.efo >= 2.5) return "SÌ";
  if (p.is_breakout) return "SORVEGLIATO";
  if (p.efo >= 1.5) return "DUBBIO";
  return "PANCHINA";
}

const VERDETTO_STYLES: Record<Verdetto, { bg: string; text: string; icon: React.ReactNode }> = {
  TITOLARE:    { bg: "#dcfce7", text: "#166534", icon: <ArrowUp size={12} /> },
  SÌ:          { bg: "#dcfce7", text: "#166534", icon: <ArrowUp size={12} /> },
  DUBBIO:      { bg: "#fef9c3", text: "#854d0e", icon: <Minus size={12} /> },
  SORVEGLIATO: { bg: "#dbeafe", text: "#1e40af", icon: <ArrowUp size={12} /> },
  PANCHINA:    { bg: "#fee2e2", text: "#991b1b", icon: <ArrowDown size={12} /> },
};

function SkeletonRow() {
  return (
    <tr>
      {[1,2,3,4,5].map(i => (
        <td key={i} className="px-4 py-3">
          <div className="h-3 rounded animate-pulse" style={{ background: "#e2e8f0", width: `${50 + i * 10}%` }} />
        </td>
      ))}
    </tr>
  );
}

export default function StartSitView({ league }: StartSitViewProps) {
  const { t } = useTranslation();
  const [rows,     setRows]     = useState<TableRow[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState<string | null>(null);
  const [sortCol,  setSortCol]  = useState<keyof TableRow>("efo");
  const [sortDir,  setSortDir]  = useState<"asc" | "desc">("desc");

  useEffect(() => {
    const ctrl = new AbortController();
    setLoading(true);
    setError(null);
    setRows([]);

    const params = new URLSearchParams({ league, filter: "current" });
    fetch(`${FANTA_API}/players?${params}`, { signal: ctrl.signal })
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then((d: unknown) => {
        const apiRows = Array.isArray(d) ? (d as ApiPlayer[]) : [];
        const mapped: TableRow[] = apiRows.map(p => ({
          player:         p.player ?? "—",
          team:           p.team   ?? "—",
          position:       p.position ?? "N/D",
          titolarita_pct: p.titolarita_pct ?? 0,
          efo:            p.efo          ?? 0,
          luck_index:     p.luck_index   ?? 0,
          is_breakout:    p.is_breakout  ?? false,
          verdetto:       computeVerdetto(p),
        }));
        setRows(mapped);
        setLoading(false);
      })
      .catch(e => {
        if ((e as Error).name !== "AbortError") {
          setError((e as Error).message);
          setLoading(false);
        }
      });

    return () => ctrl.abort();
  }, [league]);

  function handleSort(col: keyof TableRow) {
    if (sortCol === col) {
      setSortDir(d => (d === "desc" ? "asc" : "desc"));
    } else {
      setSortCol(col);
      setSortDir("desc");
    }
  }

  const sorted = [...rows].sort((a, b) => {
    const aVal = a[sortCol];
    const bVal = b[sortCol];
    if (typeof aVal === "string" && typeof bVal === "string") {
      return sortDir === "desc" ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
    }
    return sortDir === "desc"
      ? (bVal as number) - (aVal as number)
      : (aVal as number) - (bVal as number);
  });

  const SortIcon = ({ col }: { col: keyof TableRow }) => {
    if (sortCol !== col) return <span className="ml-1 opacity-20">↕</span>;
    return <span className="ml-1">{sortDir === "desc" ? "↓" : "↑"}</span>;
  };

  return (
    <div className="space-y-5">
      {/* Section header */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ background: "rgba(0,240,255,0.06)", border: "1px solid rgba(0,240,255,0.15)" }}>
          <Activity size={15} style={{ color: "#00f0ff" }} />
        </div>
        <div>
          <h2 className="font-black uppercase tracking-tighter leading-none"
            style={{ fontFamily: "'Oswald', sans-serif", fontSize: "1.15rem", color: "#1E293B" }}>
            {t("start_sit.title")}
          </h2>
          <p className="text-[9px] font-mono uppercase tracking-[0.2em] mt-0.5" style={{ color: "#64748b" }}>
            {loading ? t("start_sit.loading_data") : error ? t("start_sit.connection_error") : t("start_sit.players_count", { count: rows.length, league })}
          </p>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="rounded-xl overflow-hidden border" style={{ borderColor: "#e2e8f0" }}>
          <table className="w-full" style={{ background: "#ffffff" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #e2e8f0", background: "#f8fafc" }}>
                {[t("common.player"), t("start_sit.col_titolarita"), t("start_sit.col_efo"), t("fanta.luck_index"), t("start_sit.col_advice")].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-[9px] font-black uppercase tracking-widest" style={{ color: "#64748b" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: 8 }).map((_, i) => <SkeletonRow key={i} />)}
            </tbody>
          </table>
        </div>
      ) : error ? (
        <div className="flex flex-col items-center py-16 gap-3" style={{ color: "#64748b" }}>
          <AlertTriangle size={24} className="text-red-400" />
          <span className="text-[9px] font-mono text-red-400 uppercase tracking-widest">{error}</span>
          <span className="text-xs tabular-nums font-mono" style={{ color: "#64748b" }}>{t("start_sit.backend_unreachable")}</span>
        </div>
      ) : rows.length === 0 ? (
        <div className="flex flex-col items-center py-16 gap-3" style={{ color: "#64748b" }}>
          <Loader2 size={24} />
          <span className="text-[9px] font-mono uppercase tracking-widest">{t("start_sit.no_data_season")}</span>
        </div>
      ) : (
        <div className="rounded-xl overflow-hidden border" style={{ borderColor: "#e2e8f0" }}>
          <table className="w-full" style={{ background: "#ffffff" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #e2e8f0", background: "#f8fafc" }}>
                {[
                  { key: "player" as keyof TableRow, label: t("common.player") },
                  { key: "titolarita_pct" as keyof TableRow, label: t("start_sit.col_titolarita") },
                  { key: "efo" as keyof TableRow, label: t("start_sit.col_efo") },
                  { key: "luck_index" as keyof TableRow, label: t("fanta.luck_index") },
                  { key: "verdetto" as keyof TableRow, label: t("start_sit.col_advice") },
                ].map(col => (
                  <th
                    key={col.label}
                    onClick={() => handleSort(col.key)}
                    className="px-4 py-3 text-left text-[9px] font-black uppercase tracking-widest cursor-pointer select-none transition-colors hover:opacity-80"
                    style={{ color: "#64748b" }}
                  >
                    {col.label}
                    <SortIcon col={col.key} />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((row, idx) => {
                const vs = VERDETTO_STYLES[row.verdetto];
                return (
                  <tr
                    key={row.player}
                    style={{
                      borderBottom: idx < sorted.length - 1 ? "1px solid #f1f5f9" : "none",
                      transition: "background 0.1s",
                    }}
                    className="hover:bg-slate-50"
                  >
                    {/* Giocatore (Team) */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span
                          className="w-6 h-6 rounded-md flex items-center justify-center text-[8px] font-black uppercase"
                          style={{
                            background:
                              row.position === "FW" ? "#fee2e2" :
                              row.position === "MF" ? "#dbeafe" :
                              row.position === "DF" ? "#dcfce7" :
                              "#f3e8ff",
                            color:
                              row.position === "FW" ? "#991b1b" :
                              row.position === "MF" ? "#1e40af" :
                              row.position === "DF" ? "#166534" :
                              "#6b21a8",
                          }}
                        >
                          {row.position}
                        </span>
                        <div>
                          <div className="text-sm font-semibold leading-tight" style={{ color: "#1E293B" }}>
                            {row.player}
                          </div>
                          <div className="text-[10px] font-mono" style={{ color: "#94a3b8" }}>
                            {row.team}
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* Titolarità % */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 rounded-full overflow-hidden" style={{ background: "#e2e8f0" }}>
                          <div
                            className="h-full rounded-full transition-all"
                            style={{
                              width: `${Math.min(row.titolarita_pct, 100)}%`,
                              background:
                                row.titolarita_pct >= 70 ? "#22c55e" :
                                row.titolarita_pct >= 40 ? "#eab308" :
                                "#ef4444",
                            }}
                          />
                        </div>
                        <span className="text-xs font-mono font-semibold tabular-nums" style={{ color: "#1E293B" }}>
                          {row.titolarita_pct}%
                        </span>
                      </div>
                    </td>

                    {/* EFO (pts/90) */}
                    <td className="px-4 py-3">
                      <span
                        className="text-sm font-mono font-bold tabular-nums"
                        style={{
                          color:
                            row.efo >= 4.0 ? "#16a34a" :
                            row.efo >= 2.5 ? "#22c55e" :
                            row.efo >= 1.5 ? "#ca8a04" :
                            "#94a3b8",
                        }}
                      >
                        {row.efo.toFixed(2)}
                      </span>
                    </td>

                    {/* Luck Index */}
                    <td className="px-4 py-3">
                      <span
                        className="text-sm font-mono tabular-nums"
                        style={{
                          color: row.luck_index > 0 ? "#16a34a" : row.luck_index < -1 ? "#ef4444" : "#64748b",
                        }}
                      >
                        {row.luck_index > 0 ? "+" : ""}{row.luck_index.toFixed(2)}
                      </span>
                    </td>

                    {/* Consiglio (Verdetto) */}
                    <td className="px-4 py-3">
                      <span
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[9px] font-black uppercase tracking-wider"
                        style={{ background: vs.bg, color: vs.text }}
                      >
                        {vs.icon}
                        {row.verdetto}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
