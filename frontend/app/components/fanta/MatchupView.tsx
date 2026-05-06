"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Crosshair, Search, X, ChevronUp, ChevronDown,
  ArrowUpDown, AlertTriangle, Loader2, Shield,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslation } from "react-i18next";
import "../../i18n/config";
import type { LeagueId } from "@/app/fanta-draft/page";

const FANTA_API = "http://localhost:8000/api/fanta";

// ─── Types ────────────────────────────────────────────────────────────────────

type Pos      = "GK" | "DF" | "MF" | "FW" | "N/D";
type Verdict  = "green" | "amber" | "red";
type ViewMode = "base" | "advanced";
type SortKeyBase = "schierabilita" | "xg" | "xa" | "minutes";
type SortKeyAdv  = "schierabilita" | "efo" | "luck_index" | "titolarita_pct";
type SortKey = SortKeyBase | SortKeyAdv;

type FantaPlayer = {
  player: string;
  player_id: string;
  team: string;
  position: Pos;
  goals: number;
  assists: number;
  minutes: number;
  xg_p90: number;
  xa_p90: number;
  xgchain_p90: number;
  keypasses_p90: number;
  value_score: number;
  max_bid_pct: number;
  efo: number;
  luck_index: number;
  titolarita_pct: number;
  is_breakout: boolean;
  // aliases for legacy calc
  xg: number;
  xa: number;
  xgchain: number;
};

type TeamDef = { ppda: number; xg_conceded: number; deep_allowed: number; cs_pct: number };

// ─── Static defensive data ────────────────────────────────────────────────────

const TEAM_DEF_ALL: Record<string, TeamDef> = {
  "Inter":                { ppda: 4.5,  xg_conceded: 0.52, deep_allowed: 4,  cs_pct: 58 },
  "Napoli":               { ppda: 9.2,  xg_conceded: 1.20, deep_allowed: 10, cs_pct: 30 },
  "Juventus":             { ppda: 7.8,  xg_conceded: 0.95, deep_allowed: 8,  cs_pct: 42 },
  "Milan":                { ppda: 8.1,  xg_conceded: 1.10, deep_allowed: 9,  cs_pct: 35 },
  "AC Milan":             { ppda: 8.1,  xg_conceded: 1.10, deep_allowed: 9,  cs_pct: 35 },
  "Lazio":                { ppda: 10.2, xg_conceded: 1.35, deep_allowed: 11, cs_pct: 25 },
  "Atalanta":             { ppda: 6.2,  xg_conceded: 0.88, deep_allowed: 7,  cs_pct: 45 },
  "Roma":                 { ppda: 9.5,  xg_conceded: 1.28, deep_allowed: 10, cs_pct: 28 },
  "Fiorentina":           { ppda: 11.0, xg_conceded: 1.40, deep_allowed: 13, cs_pct: 22 },
  "Torino":               { ppda: 6.8,  xg_conceded: 0.90, deep_allowed: 7,  cs_pct: 40 },
  "Bologna":              { ppda: 10.5, xg_conceded: 1.45, deep_allowed: 14, cs_pct: 18 },
  "Genoa":                { ppda: 12.5, xg_conceded: 1.85, deep_allowed: 16, cs_pct: 14 },
  "Como":                 { ppda: 10.8, xg_conceded: 1.55, deep_allowed: 13, cs_pct: 22 },
  "Parma":                { ppda: 12.0, xg_conceded: 1.80, deep_allowed: 15, cs_pct: 15 },
  "Manchester City":      { ppda: 5.2,  xg_conceded: 0.60, deep_allowed: 5,  cs_pct: 52 },
  "Liverpool":            { ppda: 6.5,  xg_conceded: 0.78, deep_allowed: 6,  cs_pct: 48 },
  "Arsenal":              { ppda: 7.0,  xg_conceded: 0.82, deep_allowed: 7,  cs_pct: 44 },
  "Chelsea":              { ppda: 8.5,  xg_conceded: 1.10, deep_allowed: 10, cs_pct: 30 },
  "Manchester United":    { ppda: 9.0,  xg_conceded: 1.25, deep_allowed: 11, cs_pct: 28 },
  "Tottenham":            { ppda: 8.0,  xg_conceded: 1.15, deep_allowed: 9,  cs_pct: 32 },
  "Aston Villa":          { ppda: 9.5,  xg_conceded: 1.30, deep_allowed: 12, cs_pct: 24 },
  "Newcastle United":     { ppda: 7.5,  xg_conceded: 0.95, deep_allowed: 8,  cs_pct: 38 },
  "Brighton":             { ppda: 10.5, xg_conceded: 1.40, deep_allowed: 13, cs_pct: 22 },
  "Brentford":            { ppda: 11.0, xg_conceded: 1.55, deep_allowed: 14, cs_pct: 18 },
  "Real Madrid":          { ppda: 5.5,  xg_conceded: 0.58, deep_allowed: 5,  cs_pct: 54 },
  "Barcelona":            { ppda: 6.8,  xg_conceded: 0.75, deep_allowed: 6,  cs_pct: 46 },
  "Atletico Madrid":      { ppda: 4.8,  xg_conceded: 0.50, deep_allowed: 4,  cs_pct: 60 },
  "Athletic Club":        { ppda: 7.5,  xg_conceded: 0.90, deep_allowed: 8,  cs_pct: 40 },
  "Real Sociedad":        { ppda: 8.2,  xg_conceded: 1.05, deep_allowed: 9,  cs_pct: 34 },
  "Girona":               { ppda: 9.5,  xg_conceded: 1.30, deep_allowed: 12, cs_pct: 26 },
  "Real Betis":           { ppda: 10.0, xg_conceded: 1.40, deep_allowed: 13, cs_pct: 22 },
  "Villarreal":           { ppda: 11.0, xg_conceded: 1.60, deep_allowed: 15, cs_pct: 18 },
  "Bayern Munich":        { ppda: 4.8,  xg_conceded: 0.52, deep_allowed: 4,  cs_pct: 56 },
  "Bayer Leverkusen":     { ppda: 5.5,  xg_conceded: 0.65, deep_allowed: 5,  cs_pct: 50 },
  "Borussia Dortmund":    { ppda: 7.0,  xg_conceded: 0.88, deep_allowed: 7,  cs_pct: 42 },
  "RB Leipzig":           { ppda: 6.2,  xg_conceded: 0.78, deep_allowed: 6,  cs_pct: 46 },
  "Eintracht Frankfurt":  { ppda: 8.5,  xg_conceded: 1.15, deep_allowed: 10, cs_pct: 32 },
  "VfB Stuttgart":        { ppda: 9.0,  xg_conceded: 1.25, deep_allowed: 11, cs_pct: 28 },
  "Paris Saint Germain":  { ppda: 5.0,  xg_conceded: 0.55, deep_allowed: 4,  cs_pct: 54 },
  "Monaco":               { ppda: 6.5,  xg_conceded: 0.80, deep_allowed: 6,  cs_pct: 44 },
  "Marseille":            { ppda: 7.8,  xg_conceded: 1.00, deep_allowed: 9,  cs_pct: 36 },
  "Lille":                { ppda: 8.0,  xg_conceded: 1.05, deep_allowed: 9,  cs_pct: 34 },
  "Lyon":                 { ppda: 9.5,  xg_conceded: 1.30, deep_allowed: 12, cs_pct: 26 },
  "Nice":                 { ppda: 7.5,  xg_conceded: 0.92, deep_allowed: 7,  cs_pct: 38 },
  "Lens":                 { ppda: 8.5,  xg_conceded: 1.10, deep_allowed: 10, cs_pct: 30 },
  "Rennes":               { ppda: 10.0, xg_conceded: 1.35, deep_allowed: 13, cs_pct: 24 },
};

interface MatchupViewProps {
  league: LeagueId;
  year?: number;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const ROLE_COLOR: Record<string, string> = {
  GK: "#f59e0b", DF: "#10b981", MF: "#3b82f6", FW: "#ef4444",
};

function getVerdictCfg(t: (k: string) => string): Record<Verdict, { color: string; label: string }> {
  return {
    green: { color: "#22c55e", label: t("matchup.verdict_deploy") },
    amber: { color: "#f59e0b", label: t("matchup.verdict_risk")   },
    red:   { color: "#ef4444", label: t("matchup.verdict_bench")  },
  };
}

function sf(v: unknown, d = 2): string {
  const n = typeof v === "number" ? v : parseFloat(String(v ?? 0));
  return isNaN(n) ? "---" : n.toFixed(d);
}

function luckColor(li: number): string {
  if (li > 1.0)  return "#ef4444";
  if (li < -1.0) return "#22c55e";
  return "#94a3b8";
}

function teamDefLookup(teamName: string): TeamDef | null {
  if (!teamName) return null;
  const direct = TEAM_DEF_ALL[teamName];
  if (direct) return direct;
  const lower = teamName.toLowerCase();
  for (const [k, v] of Object.entries(TEAM_DEF_ALL)) {
    if (lower.includes(k.toLowerCase()) || k.toLowerCase().includes(lower)) return v;
  }
  return null;
}

function calcSchierabilita(p: FantaPlayer): { score: number; verdict: Verdict; matchupIdx: number } {
  const oppDef     = teamDefLookup(p.team);
  const matchupIdx = oppDef
    ? (oppDef.xg_conceded * 1.2) + (oppDef.deep_allowed * 0.08) - (oppDef.ppda * 0.05)
    : 1.2;
  const formScore = (p.xg ?? 0) * 0.7 + (p.xa ?? 0) * 0.5;
  const raw       = formScore * 40 + matchupIdx * 25;
  const score     = Math.min(100, Math.max(0, raw));
  const verdict: Verdict = score >= 75 ? "green" : score >= 50 ? "amber" : "red";
  return { score, verdict, matchupIdx };
}

// ─── ModeToggle ───────────────────────────────────────────────────────────────

function ModeToggle({ mode, onChange }: { mode: ViewMode; onChange: (m: ViewMode) => void }) {
  return (
    <div className="flex items-center gap-0.5 p-1 rounded-xl" style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)" }}>
      {(["base", "advanced"] as ViewMode[]).map(m => {
        const active = mode === m;
        const accent = m === "base" ? "#3b82f6" : "#FF2A6D";
        return (
          <button key={m} onClick={() => onChange(m)} className="relative px-3 py-1.5 rounded-lg overflow-hidden">
            {active && (
              <motion.div layoutId="matchup-mode-pill" className="absolute inset-0 rounded-lg"
                style={{ background: "rgba(255,255,255,0.06)", border: `1px solid ${accent}30`, boxShadow: "0 1px 4px rgba(0,0,0,0.3)" }}
                transition={{ type: "spring", stiffness: 420, damping: 30 }}
              />
            )}
            <span className="relative z-10 text-[8px] font-mono font-black uppercase tracking-widest"
              style={{ color: active ? accent : "#64748b" }}>
              {m === "base" ? "Base" : "⚗ Advanced"}
            </span>
          </button>
        );
      })}
    </div>
  );
}

// ─── MiniBar ─────────────────────────────────────────────────────────────────

function MiniBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = Math.min(100, Math.max(0, ((value ?? 0) / Math.max(max, 0.001)) * 100));
  return (
    <div className="relative overflow-hidden" style={{ height: 4, background: "rgba(255,255,255,0.08)", borderRadius: 2 }}>
      <motion.div className="absolute inset-y-0 left-0" style={{ background: color }}
        initial={{ width: "0%" }} animate={{ width: `${pct}%` }} transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }} />
    </div>
  );
}

// ─── LuckTag ─────────────────────────────────────────────────────────────────

function LuckTag({ li }: { li: number }) {
  const { t } = useTranslation();
  const v = li ?? 0;
  if (v > 1.0) return (
    <span className="text-[6px] font-mono font-black uppercase tracking-widest px-1 py-0.5 rounded-sm whitespace-nowrap"
      style={{ color: "#ef4444", background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)" }}>
      {t("matchup.overperformer")}
    </span>
  );
  if (v < -1.0) return (
    <span className="text-[6px] font-mono font-black uppercase tracking-widest px-1 py-0.5 rounded-sm whitespace-nowrap"
      style={{ color: "#22c55e", background: "rgba(34,197,94,0.08)", border: "1px solid rgba(34,197,94,0.2)" }}>
      {t("matchup.underperformer")}
    </span>
  );
  return null;
}

// ─── OpponentPanel ────────────────────────────────────────────────────────────

function OpponentPanel({ teamName }: { teamName: string | null }) {
  const { t } = useTranslation();
  if (!teamName) {
    return (
      <div className="rounded-xl flex flex-col items-center justify-center py-16 gap-3 h-full"
        style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}>
        <Shield size={24} style={{ color: "#475569" }} />
        <p className="text-[9px] font-mono uppercase tracking-[0.2em]" style={{ color: "#64748b" }}>{t("common.team")}</p>
      </div>
    );
  }
  const def = teamDefLookup(teamName);
  if (!def) return null;

  const defMetrics = [
    { label: t("matchup.ppda"),          val: def.ppda,        max: 15,  color: "#3b82f6", note: "" },
    { label: t("matchup.xg_conceded"),   val: def.xg_conceded, max: 2.5, color: "#ef4444", note: "" },
    { label: t("matchup.clean_sheet_pct"), val: def.cs_pct,    max: 100, color: "#22c55e", note: "" },
  ];

  return (
    <div className="rounded-xl overflow-hidden h-full" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}>
      <div className="px-4 py-3" style={{ background: "rgba(255,255,255,0.04)", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="text-[8px] font-mono font-black uppercase tracking-[0.25em]" style={{ color: "#64748b" }}>{t("matchup.opponent_defense")}</div>
        <div className="font-black uppercase tracking-tighter mt-0.5" style={{ fontFamily: "'Oswald', sans-serif", fontSize: "1.1rem", color: "#f1f5f9" }}>{teamName}</div>
      </div>
      <div className="p-4 space-y-5">
        <div className="space-y-2.5">
          {defMetrics.map(m => (
            <div key={m.label}>
              <div className="flex justify-between mb-1">
                <span className="text-[8px] font-mono" style={{ color: "#64748b" }}>{m.label}</span>
                <span className="font-mono font-black text-[9px]" style={{ color: m.color }}>{sf(m.val, 1)}</span>
              </div>
              <MiniBar value={m.val} max={m.max} color={m.color} />
              <div className="text-[7px] font-mono mt-0.5" style={{ color: "#475569" }}>{m.note}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── MatchupTable ─────────────────────────────────────────────────────────────

function MatchupTable({ players, onTeamChange, viewMode }: {
  players: FantaPlayer[];
  onTeamChange: (t: string) => void;
  viewMode: ViewMode;
}) {
  const { t } = useTranslation();
  const VERDICT_CFG = getVerdictCfg(t);
  const [sortKey, setSortKey] = useState<SortKey>("schierabilita");
  const [asc, setAsc]         = useState(false);

  const enriched = useMemo(
    () => players.map(p => ({ ...p, ...calcSchierabilita(p) })),
    [players],
  );

  const sorted = useMemo(() => {
    return [...enriched].sort((a, b) => {
      let av: number, bv: number;
      switch (sortKey) {
        case "schierabilita":  av = a.score;              bv = b.score;              break;
        case "xg":             av = a.xg ?? 0;            bv = b.xg ?? 0;            break;
        case "xa":             av = a.xa ?? 0;            bv = b.xa ?? 0;            break;
        case "minutes":        av = a.minutes ?? 0;       bv = b.minutes ?? 0;       break;
        case "efo":            av = a.efo ?? 0;           bv = b.efo ?? 0;           break;
        case "luck_index":     av = a.luck_index ?? 0;    bv = b.luck_index ?? 0;    break;
        case "titolarita_pct": av = a.titolarita_pct ?? 0; bv = b.titolarita_pct ?? 0; break;
        default:               av = 0; bv = 0;
      }
      return asc ? av - bv : bv - av;
    });
  }, [enriched, sortKey, asc]);

  const toggle = (k: SortKey) => {
    if (k === sortKey) setAsc(v => !v);
    else { setSortKey(k); setAsc(false); }
  };

  const SortIcon = ({ k }: { k: SortKey }) =>
    k !== sortKey
      ? <ArrowUpDown size={8} style={{ color: "#475569" }} />
      : asc
        ? <ChevronUp   size={8} style={{ color: "#FF2A6D" }} />
        : <ChevronDown size={8} style={{ color: "#FF2A6D" }} />;

  if (!sorted.length) {
    return (
      <div className="flex flex-col items-center py-16 gap-3" style={{ color: "#64748b" }}>
        <Crosshair size={22} />
        <span className="text-[9px] font-mono uppercase tracking-[0.2em]">{t("matchup.no_results")}</span>
      </div>
    );
  }

  const baseCols:  { k: SortKey; l: string }[] = [
    { k: "xg",            l: "xG/90"   },
    { k: "xa",            l: "xA/90"   },
    { k: "minutes",       l: "Min"     },
    { k: "schierabilita", l: "Rating"  },
  ];
  const advCols: { k: SortKey; l: string }[] = [
    { k: "efo",            l: "EFO"      },
    { k: "titolarita_pct", l: "Titol.%"  },
    { k: "luck_index",     l: "Luck Idx" },
    { k: "schierabilita",  l: "Rating"   },
  ];
  const cols = viewMode === "base" ? baseCols : advCols;

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr style={{ background: "rgba(255,255,255,0.04)", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
            <th className="py-2.5 pl-4 pr-3 text-left">
              <span className="text-[8px] font-mono font-black uppercase tracking-wider" style={{ color: "#64748b" }}>{t("common.player")}</span>
            </th>
            {cols.map(c => (
              <th key={c.k} className="py-2.5 px-3 text-right">
                <button onClick={() => toggle(c.k)} className="flex items-center gap-1 ml-auto"
                  style={{ color: sortKey === c.k ? "#FF2A6D" : "#64748b" }}>
                  <span className="text-[8px] font-mono font-black uppercase tracking-wider">{c.l}</span>
                  <SortIcon k={c.k} />
                </button>
              </th>
            ))}
            {viewMode === "advanced" && (
              <th className="py-2.5 px-3 text-right">
                <span className="text-[8px] font-mono font-black uppercase tracking-wider" style={{ color: "#64748b" }}>Tag</span>
              </th>
            )}
            <th className="py-2.5 pl-3 pr-4 text-right">
              <span className="text-[8px] font-mono font-black uppercase tracking-wider" style={{ color: "#64748b" }}>{t("matchup.schierabilita")}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((p, i) => {
            const rc     = ROLE_COLOR[p.position] ?? "#64748b";
            const v      = VERDICT_CFG[p.verdict];
            const rowBg  = i % 2 !== 0 ? "rgba(255,255,255,0.02)" : "transparent";
            const li     = p.luck_index ?? 0;

            return (
              <motion.tr
                key={p.player_id ?? `${p.player}-${i}`}
                initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                transition={{ delay: Math.min(i * 0.012, 0.3) }}
                style={{ background: rowBg, borderBottom: "1px solid rgba(255,255,255,0.04)" }}
                className="cursor-default"
                onClick={() => onTeamChange(p.team)}
              >
                <td className="py-2.5 pl-4 pr-3">
                  <div className="flex items-center gap-2">
                    <span className="text-[7px] font-mono font-black px-1.5 py-0.5 rounded flex-shrink-0"
                      style={{ color: rc, background: `${rc}15`, border: `1px solid ${rc}30` }}>
                      {p.position ?? "—"}
                    </span>
                    <div>
                      <div className="text-[11px] font-black leading-none" style={{ fontFamily: "'Oswald', sans-serif", color: "#f1f5f9" }}>{p.player ?? "—"}</div>
                      <div className="text-[8px] font-mono mt-0.5" style={{ color: "#64748b" }}>{p.team ?? "—"}</div>
                    </div>
                  </div>
                </td>

                {viewMode === "base" && <>
                  <td className="py-2.5 px-3 text-right"><span className="font-mono text-[10px] font-black" style={{ color: "#94a3b8" }}>{sf(p.xg, 3)}</span></td>
                  <td className="py-2.5 px-3 text-right"><span className="font-mono text-[10px] font-black" style={{ color: "#94a3b8" }}>{sf(p.xa, 3)}</span></td>
                  <td className="py-2.5 px-3 text-right"><span className="font-mono text-[10px]" style={{ color: "#64748b" }}>{p.minutes ?? 0}</span></td>
                  <td className="py-2.5 px-3 text-right"><span className="font-mono font-black text-[11px]" style={{ color: v.color }}>{Math.round(p.score)}</span></td>
                </>}

                {viewMode === "advanced" && <>
                  <td className="py-2.5 px-3 text-right">
                    <span className="font-mono text-[10px] font-black" style={{ color: "#FF2A6D" }}>{sf(p.efo, 2)}</span>
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <span className="font-mono text-[10px] font-black" style={{ color: "#94a3b8" }}>{sf(p.titolarita_pct, 1)}%</span>
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <span className="font-mono text-[10px] font-black" style={{ color: luckColor(li) }}>
                      {li >= 0 ? "+" : ""}{sf(li, 2)}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-right"><span className="font-mono font-black text-[11px]" style={{ color: v.color }}>{Math.round(p.score)}</span></td>
                  <td className="py-2.5 px-3 text-right"><LuckTag li={li} /></td>
                </>}

                <td className="py-2.5 pl-3 pr-4 text-right">
                  <span className="text-[7px] font-mono font-black uppercase tracking-[0.15em] px-2 py-1 rounded"
                    style={{ color: v.color, background: `${v.color}0f`, border: `1px solid ${v.color}28` }}>
                    {v.label}
                  </span>
                </td>
              </motion.tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ─── Main view ────────────────────────────────────────────────────────────────

export default function MatchupView({ league, year }: MatchupViewProps) {
  const [allPlayers,  setAllPlayers]  = useState<FantaPlayer[]>([]);
  const [loading,     setLoading]     = useState(true);
  const [error,       setError]       = useState<string | null>(null);
  const [search,      setSearch]      = useState("");
  const [teamFilter,  setTeamFilter]  = useState<string>("ALL");
  const [roleFilter,  setRoleFilter]  = useState<string>("ALL");
  const [focusedTeam, setFocusedTeam] = useState<string | null>(null);
  const [teamOpen,    setTeamOpen]    = useState(false);
  const [viewMode,    setViewMode]    = useState<ViewMode>("base");

  useEffect(() => {
    const ctrl = new AbortController();
    setLoading(true);
    setError(null);
    setAllPlayers([]);

    const params = new URLSearchParams({ league, filter: "current" });
    if (year) params.set("year", String(year));
    fetch(`${FANTA_API}/players?${params}`, { signal: ctrl.signal })
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then((d: unknown) => {
        const rows = Array.isArray(d) ? (d as any[]) : [];
        setAllPlayers(rows.map(p => ({
          ...p,
          xg:      p.xg_p90      ?? 0,
          xa:      p.xa_p90      ?? 0,
          xgchain: p.xgchain_p90 ?? 0,
        })));
        setLoading(false);
      })
      .catch(e => {
        if ((e as Error).name !== "AbortError") {
          setError((e as Error).message);
          setLoading(false);
        }
      });

    return () => ctrl.abort();
  }, [league, year]);

  const teams = useMemo(() => {
    const s = new Set(allPlayers.map(p => p.team).filter(Boolean));
    return ["ALL", ...Array.from(s).sort()];
  }, [allPlayers]);

  const filtered = useMemo(() => allPlayers.filter(p => {
    const q = search.toLowerCase();
    if (q && !p.player?.toLowerCase().includes(q) && !p.team?.toLowerCase().includes(q)) return false;
    if (teamFilter !== "ALL" && p.team !== teamFilter) return false;
    if (roleFilter !== "ALL" && p.position !== roleFilter) return false;
    return true;
  }), [allPlayers, search, teamFilter, roleFilter]);

  useEffect(() => {
    if (teamFilter !== "ALL") setFocusedTeam(teamFilter);
  }, [teamFilter]);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ background: "rgba(59,130,246,0.1)", border: "1px solid rgba(59,130,246,0.2)" }}>
          <Crosshair size={15} style={{ color: "#3b82f6" }} />
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="font-black uppercase tracking-tighter leading-none"
            style={{ fontFamily: "'Oswald', sans-serif", fontSize: "1.15rem", color: "#f1f5f9" }}>
            Matchup Intelligence
          </h2>
          <p className="text-[8px] font-mono uppercase tracking-[0.2em] mt-0.5" style={{ color: "#64748b" }}>
            {loading ? "Caricamento dati reali…" : `${filtered.length} giocatori · ${league} · 2025/26 · click riga → profilo squadra`}
          </p>
        </div>
        <ModeToggle mode={viewMode} onChange={setViewMode} />
      </div>

      {/* Search + Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl flex-1 min-w-0 max-w-xs"
          style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}>
          <Search size={12} style={{ color: "#64748b", flexShrink: 0 }} />
          <input type="text" value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Cerca giocatore o squadra…"
            className="flex-1 bg-transparent outline-none text-[10px] font-mono placeholder:text-slate-500"
            style={{ color: "#f1f5f9" }}
          />
          {search && <button onClick={() => setSearch("")}><X size={11} style={{ color: "#64748b" }} /></button>}
        </div>

        <div className="relative">
          <button onClick={() => setTeamOpen(v => !v)}
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-[9px] font-mono font-black uppercase tracking-widest"
            style={{
              background: teamFilter !== "ALL" ? "rgba(59,130,246,0.1)" : "rgba(255,255,255,0.03)",
              border: `1px solid ${teamFilter !== "ALL" ? "rgba(59,130,246,0.3)" : "rgba(255,255,255,0.06)"}`,
              color: teamFilter !== "ALL" ? "#3b82f6" : "#64748b",
            }}>
            <span className="max-w-[100px] truncate">{teamFilter === "ALL" ? "Squadra" : teamFilter}</span>
            <ChevronDown size={10} style={{ transform: teamOpen ? "rotate(180deg)" : "none", transition: "transform 150ms", flexShrink: 0 }} />
          </button>
          <AnimatePresence>
            {teamOpen && (
              <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.12 }}
                className="absolute left-0 top-full mt-1 rounded-xl overflow-y-auto z-50 border shadow-2xl"
                style={{ background: "#141b2d", borderColor: "rgba(255,255,255,0.06)", maxHeight: 220, width: 180 }}>
                {teams.map(t => (
                  <button key={t} onClick={() => { setTeamFilter(t); setTeamOpen(false); }}
                    className="w-full text-left px-3 py-2 text-[9px] font-mono font-black uppercase tracking-widest transition-colors"
                    style={{ color: t === teamFilter ? "#3b82f6" : "#94a3b8", background: t === teamFilter ? "rgba(59,130,246,0.08)" : "transparent" }}
                    onMouseEnter={e => { if (t !== teamFilter) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)"; }}
                    onMouseLeave={e => { if (t !== teamFilter) (e.currentTarget as HTMLElement).style.background = "transparent"; }}>
                    {t}
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="flex gap-1.5">
          {(["ALL", "FW", "MF", "DF", "GK"] as const).map(r => (
            <button key={r} onClick={() => setRoleFilter(r)}
              className="px-2.5 py-1.5 rounded-lg text-[8px] font-mono font-black uppercase tracking-widest transition-all"
              style={{
                background: roleFilter === r ? `${ROLE_COLOR[r] ?? "#3b82f6"}15` : "rgba(255,255,255,0.03)",
                border: `1px solid ${roleFilter === r ? `${ROLE_COLOR[r] ?? "#3b82f6"}40` : "rgba(255,255,255,0.06)"}`,
                color: roleFilter === r ? (ROLE_COLOR[r] ?? "#3b82f6") : "#64748b",
              }}>
              {r}
            </button>
          ))}
        </div>
      </div>

      {/* Bento grid */}
      <div className="grid grid-cols-12 gap-4 items-start">
        <div className="col-span-12 lg:col-span-8">
          <div className="rounded-xl overflow-hidden" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}>
            {loading ? (
              <div className="flex items-center justify-center py-20 gap-3" style={{ color: "#3b82f6" }}>
                <Loader2 size={20} className="animate-spin" />
                <span className="text-[9px] font-mono uppercase tracking-[0.2em]">Caricamento dati reali…</span>
              </div>
            ) : error ? (
              <div className="flex flex-col items-center py-16 gap-2">
                <AlertTriangle size={20} className="text-red-400" />
                <span className="text-[9px] font-mono text-red-400 uppercase tracking-widest">{error}</span>
                <span className="text-[8px] font-mono" style={{ color: "#64748b" }}>Backend non raggiungibile (porta 8000)</span>
              </div>
            ) : (
              <MatchupTable players={filtered} onTeamChange={t => setFocusedTeam(t)} viewMode={viewMode} />
            )}
          </div>
        </div>

        <div className="col-span-12 lg:col-span-4">
          <OpponentPanel teamName={focusedTeam} />
        </div>
      </div>
    </div>
  );
}
