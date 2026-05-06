"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  TrendingUp, ArrowUpDown, ChevronUp, ChevronDown,
  Plus, Trash2, Wallet, Lightbulb, Loader2, AlertTriangle,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ComposedChart, Scatter, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { useTranslation } from "react-i18next";
import "@/app/i18n/config";
import type { LeagueId } from "@/app/fanta-draft/page";

const FANTA_API = "http://localhost:8000/api/fanta";

// ─── Types ────────────────────────────────────────────────────────────────────

type Role = "FW" | "MF" | "DF" | "GK" | "N/D";
type ViewMode = "base" | "advanced";
type AuctionModeType = "iniziale" | "riparazione";

interface AuctionViewProps {
  season?: string;
  mode?: AuctionModeType;
  league: LeagueId;
  year?: number;
}

type ApiPlayer = {
  player: string;
  player_id: string;
  position: Role;
  team: string;
  matches: number;
  goals: number;
  assists: number;
  minutes: number;
  xg_p90: number;
  xa_p90: number;
  shots_p90: number;
  xgchain_p90: number;
  keypasses_p90: number;
  value_score: number;
  max_bid_pct: number;
  efo: number;
  luck_index: number;
  titolarita_pct: number;
  is_breakout: boolean;
};

type Purchase = { player: ApiPlayer; price: number };
type SortCol = keyof Pick<ApiPlayer, "xg_p90"|"xa_p90"|"value_score"|"max_bid_pct"|"efo"|"luck_index"|"titolarita_pct">;

// ─── Constants ────────────────────────────────────────────────────────────────

const ROLE_COLOR: Record<string, string> = {
  FW: "#ef4444", MF: "#3b82f6", DF: "#10b981", GK: "#f59e0b",
};

// ─── Pure helpers ─────────────────────────────────────────────────────────────

function sf(v: unknown, d = 2): string {
  const n = typeof v === "number" ? v : parseFloat(String(v ?? 0));
  return isNaN(n) ? "---" : n.toFixed(d);
}

function luckColor(li: number): string {
  if (li > 1.0)  return "#ef4444";
  if (li < -1.0) return "#10b981";
  return "#64748b";
}

function realPtsPerGame(p: ApiPlayer): number {
  const m = Math.max(p.matches ?? 1, 1);
  return ((p.goals ?? 0) * 5 + (p.assists ?? 0) * 3) / m;
}

function suggestedPrice(p: ApiPlayer, mode: ViewMode): number {
  const base: Record<string, number> = { FW: 80, MF: 50, DF: 30, GK: 20, "N/D": 25 };
  const b = base[p.position ?? "N/D"] ?? 30;
  const score = mode === "advanced" ? (p.efo ?? 0) : (p.value_score ?? 0);
  return Math.max(1, Math.round(b * ((score || 1) / 5)));
}

function getStrategyAdvice(
  purchases: Purchase[],
  budget: number,
  remaining: number,
  t: (key: string, opts?: Record<string, unknown>) => string,
) {
  const advice: { color: string; text: string }[] = [];
  const spent    = budget - remaining;
  const spentPct = budget > 0 ? spent / budget : 0;
  const byRole   = (r: string) => purchases.filter(p => p.player.position === r).reduce((a, p) => a + p.price, 0);

  if (purchases.length === 0) {
    advice.push({ color: "#22c55e", text: t("auction.advice_start_strong") });
    return advice;
  }
  if (byRole("FW") / budget > 0.55) {
    advice.push({ color: "#f59e0b", text: t("auction.advice_fw_over_60") });
    advice.push({ color: "#ef4444", text: t("auction.advice_avoid_expensive_fw") });
  }
  if (spentPct > 0.75) {
    advice.push({ color: "#ef4444", text: t("auction.advice_budget_exhausted", { remaining }) });
  } else if (spentPct < 0.3 && purchases.length >= 2) {
    advice.push({ color: "#22c55e", text: t("auction.advice_abundant_budget") });
  }
  if (!purchases.some(p => p.player.position === "FW") && purchases.length >= 3) {
    advice.push({ color: "#3b82f6", text: t("auction.advice_no_fw") });
  }
  if (!purchases.some(p => p.player.position === "GK") && purchases.length >= 6) {
    advice.push({ color: "#f59e0b", text: t("auction.advice_no_gk") });
  }
  return advice.slice(0, 3);
}

// ─── Skeleton ─────────────────────────────────────────────────────────────────

function SkeletonTable({ cols }: { cols: number }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr style={{ background: "#f8fafc", borderBottom: "1px solid #e2e8f0" }}>
            {Array.from({ length: cols }).map((_, i) => (
              <th key={i} className="py-2.5 px-3">
                <div className="h-2 rounded animate-pulse" style={{ background: "#e2e8f0", width: i === 0 ? 100 : 48 }} />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: 9 }).map((_, i) => (
            <tr key={i} style={{ borderBottom: "1px solid #e2e8f0" }}>
              {Array.from({ length: cols }).map((_, j) => (
                <td key={j} className="py-2.5 px-3">
                  <div className="h-2.5 rounded animate-pulse"
                    style={{ background: "#f1f5f9", width: j === 0 ? 130 : j === 1 ? 30 : 52, animationDelay: `${i * 0.06 + j * 0.018}s` }} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── ModeToggle ───────────────────────────────────────────────────────────────

function ModeToggle({ mode, onChange }: { mode: ViewMode; onChange: (m: ViewMode) => void }) {
  const { t } = useTranslation();
  return (
    <div className="flex items-center gap-0.5 p-1 rounded-xl" style={{ background: "#f1f5f9", border: "1px solid #e2e8f0" }}>
      {(["base", "advanced"] as ViewMode[]).map(m => {
        const active = mode === m;
        const accent = m === "base" ? "#3b82f6" : "#FF2A6D";
        return (
          <button key={m} onClick={() => onChange(m)} className="relative px-3 py-1.5 rounded-lg overflow-hidden">
            {active && (
              <motion.div layoutId="auction-mode-pill" className="absolute inset-0 rounded-lg"
                style={{ background: "#ffffff", border: `1px solid ${accent}30`, boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}
                transition={{ type: "spring", stiffness: 420, damping: 30 }}
              />
            )}
            <span className="relative z-10 text-xs tabular-nums font-mono font-black uppercase tracking-widest"
              style={{ color: active ? accent : "#94a3b8" }}>
              {m === "base" ? t("auction.view_logica_base") : t("auction.view_advanced")}
            </span>
          </button>
        );
      })}
    </div>
  );
}

// ─── LuckBadge ────────────────────────────────────────────────────────────────

function LuckBadge({ li }: { li: number }) {
  const { t } = useTranslation();
  if ((li ?? 0) > 1.0) {
    return (
      <span className="text-[6px] font-mono font-black uppercase tracking-widest px-1.5 py-0.5 rounded-sm whitespace-nowrap"
        style={{ color: "#ef4444", background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)" }}>
        {t("auction.regression_risk")}
      </span>
    );
  }
  if ((li ?? 0) < -1.0) {
    return (
      <span className="text-[6px] font-mono font-black uppercase tracking-widest px-1.5 py-0.5 rounded-sm whitespace-nowrap"
        style={{ color: "#10b981", background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.2)" }}>
        {t("auction.alpha_value")}
      </span>
    );
  }
  return null;
}

// ─── Scatter dot + tooltip ────────────────────────────────────────────────────

function ScatterDot(props: any) {
  const { cx, cy, payload } = props;
  if (typeof cx !== "number" || typeof cy !== "number") return null;
  const c = luckColor(payload?.luck_index ?? 0);
  return (
    <g>
      <circle cx={cx} cy={cy} r={8} fill={c} fillOpacity={0.08} />
      <circle cx={cx} cy={cy} r={5} fill={c} fillOpacity={0.75} stroke={c} strokeWidth={1} />
    </g>
  );
}

function ScatterTip({ active, payload, viewMode }: any) {
  if (!active || !payload?.length) return null;
  const p: ApiPlayer | undefined = payload[0]?.payload;
  if (!p) return null;
  const rc = ROLE_COLOR[p.position ?? "N/D"] ?? "#64748b";
  return (
    <div className="rounded-xl px-4 py-3" style={{ background: "#ffffff", border: "1px solid #e2e8f0", boxShadow: "0 8px 24px rgba(0,0,0,0.1)", minWidth: 190 }}>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-[7px] font-mono font-black px-1.5 py-0.5 rounded" style={{ color: rc, background: `${rc}12` }}>{p.position ?? "—"}</span>
        <span className="font-black text-[11px]" style={{ fontFamily: "'Oswald', sans-serif", color: "#1E293B" }}>{p.player ?? "—"}</span>
      </div>
      <div className="space-y-1">
        {(viewMode === "base"
          ? [
              { label: "xG/90",   val: sf(p.xg_p90, 3),         color: "#ef4444" },
              { label: "xA/90",   val: sf(p.xa_p90, 3),         color: "#10b981" },
              { label: "Pt/g",    val: sf(realPtsPerGame(p), 2), color: "#64748b" },
              { label: "Val.",    val: sf(p.value_score, 2),     color: "#64748b" },
            ]
          : [
              { label: "EFO",      val: sf(p.efo, 2),            color: "#FF2A6D" },
              { label: "Titol.%",  val: sf(p.titolarita_pct, 1) + "%", color: "#3b82f6" },
              { label: "Luck Idx", val: (p.luck_index >= 0 ? "+" : "") + sf(p.luck_index, 2), color: luckColor(p.luck_index ?? 0) },
            ]
        ).map(r => (
          <div key={r.label} className="flex justify-between gap-6">
            <span className="text-xs tabular-nums font-mono uppercase tracking-widest" style={{ color: "#94a3b8" }}>{r.label}</span>
            <span className="font-mono font-black text-sm tabular-nums" style={{ color: r.color }}>{r.val}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Budget sidebar ───────────────────────────────────────────────────────────

function MySidebar({ purchases, budget, onRemove }: {
  purchases: Purchase[];
  budget: number;
  onRemove: (id: string) => void;
}) {
  const { t } = useTranslation();
  const spent     = purchases.reduce((a, p) => a + p.price, 0);
  const remaining = budget - spent;
  const spentPct  = budget > 0 ? (spent / budget) * 100 : 0;
  const advice    = useMemo(() => getStrategyAdvice(purchases, budget, remaining, t), [purchases, budget, remaining, t]);

  return (
    <div className="flex flex-col h-full rounded-xl overflow-hidden" style={{ background: "#ffffff", border: "1px solid #e2e8f0" }}>
      {/* Header */}
      <div className="px-4 py-3 flex-shrink-0" style={{ background: "#f8fafc", borderBottom: "1px solid #e2e8f0" }}>
        <div className="flex items-center gap-2">
          <Wallet size={13} style={{ color: "#22c55e" }} />
          <span className="text-xs tabular-nums font-mono font-black uppercase tracking-[0.25em]" style={{ color: "#64748b" }}>{t("auction.my_squad")}</span>
        </div>
      </div>
      {/* Budget bar */}
      <div className="px-4 py-3 flex-shrink-0" style={{ borderBottom: "1px solid #e2e8f0" }}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs tabular-nums font-mono uppercase tracking-widest" style={{ color: "#94a3b8" }}>Budget</span>
          <span className="font-mono font-black text-[12px]" style={{ color: remaining < 50 ? "#ef4444" : "#22c55e" }}>
            {remaining} <span className="text-[9px]" style={{ color: "#94a3b8" }}>cr</span>
          </span>
        </div>
        <div className="h-2 overflow-hidden rounded-full" style={{ background: "#e2e8f0" }}>
          <motion.div className="h-full rounded-full"
            style={{ background: spentPct > 75 ? "#ef4444" : spentPct > 50 ? "#f59e0b" : "#22c55e" }}
            animate={{ width: `${spentPct}%` }} transition={{ duration: 0.5 }}
          />
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-[7px] font-mono" style={{ color: "#94a3b8" }}>0</span>
          <span className="text-[7px] font-mono" style={{ color: "#94a3b8" }}>{spent}/{budget} cr</span>
          <span className="text-[7px] font-mono" style={{ color: "#94a3b8" }}>{budget}</span>
        </div>
      </div>
      {/* Purchases */}
      <div className="flex-1 overflow-y-auto">
        {purchases.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-2 py-8" style={{ color: "#cbd5e1" }}>
            <Plus size={20} />
            <span className="text-xs tabular-nums font-mono uppercase tracking-[0.2em] text-center">{t("auction.buy_players_hint")}</span>
          </div>
        ) : (
          <div className="p-2 space-y-1">
            <AnimatePresence>
              {purchases.map(pu => {
                const rc = ROLE_COLOR[pu.player.position ?? "N/D"] ?? "#64748b";
                return (
                  <motion.div key={pu.player.player_id}
                    initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 10 }}
                    className="flex items-center gap-2 px-2 py-1.5 rounded-lg group"
                    style={{ background: "#f8fafc", border: "1px solid #e2e8f0" }}
                  >
                    <span className="text-[7px] font-mono font-black px-1 py-0.5 rounded flex-shrink-0" style={{ color: rc, background: `${rc}12` }}>{pu.player.position}</span>
                    <span className="flex-1 min-w-0 text-[9px] font-black truncate leading-none" style={{ fontFamily: "'Oswald', sans-serif", color: "#1E293B" }}>{pu.player.player}</span>
                    <span className="font-mono font-black text-sm tabular-nums flex-shrink-0" style={{ color: "#22c55e" }}>{pu.price}</span>
                    <button onClick={() => onRemove(pu.player.player_id)} className="opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" style={{ color: "#ef4444" }}>
                      <Trash2 size={11} />
                    </button>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        )}
      </div>
      {/* Strategy */}
      {advice.length > 0 && (
        <div className="px-3 py-3 flex-shrink-0 space-y-2" style={{ borderTop: "1px solid #e2e8f0" }}>
          <div className="flex items-center gap-1.5 mb-1">
            <Lightbulb size={11} style={{ color: "#f59e0b" }} />
            <span className="text-[7px] font-mono uppercase tracking-[0.2em]" style={{ color: "#94a3b8" }}>{t("auction.strategy_advice")}</span>
          </div>
          <AnimatePresence>
            {advice.map((a, i) => (
              <motion.div key={a.text.slice(0, 20)} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }} transition={{ delay: i * 0.06 }}
                className="flex items-start gap-1.5">
                <span className="rounded-full mt-1 flex-shrink-0" style={{ width: 4, height: 4, background: a.color }} />
                <span className="text-xs tabular-nums font-mono leading-snug" style={{ color: "#64748b" }}>{a.text}</span>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}

// ─── Auction table ────────────────────────────────────────────────────────────

function AuctionTable({ data, purchases, onBuy, budget, viewMode }: {
  data: ApiPlayer[];
  purchases: Purchase[];
  onBuy: (p: ApiPlayer, price: number) => void;
  budget: number;
  viewMode: ViewMode;
}) {
  const { t } = useTranslation();
  const defaultSort: SortCol = viewMode === "base" ? "value_score" : "efo";
  const [sortKey, setSortKey] = useState<SortCol>(defaultSort);
  const [asc, setAsc]         = useState(false);
  const [prices, setPrices]   = useState<Record<string, number>>({});

  useEffect(() => { setSortKey(viewMode === "base" ? "value_score" : "efo"); }, [viewMode]);

  const sorted = useMemo(
    () => [...data].sort((a, b) => {
      const av = (a[sortKey] as number) ?? 0;
      const bv = (b[sortKey] as number) ?? 0;
      return asc ? av - bv : bv - av;
    }),
    [data, sortKey, asc],
  );

  const toggle = (k: SortCol) => {
    if (k === sortKey) setAsc(v => !v);
    else { setSortKey(k); setAsc(false); }
  };

  const SortIcon = ({ k }: { k: SortCol }) =>
    k !== sortKey
      ? <ArrowUpDown size={8} style={{ color: "#cbd5e1" }} />
      : asc
        ? <ChevronUp   size={8} style={{ color: "#3b82f6" }} />
        : <ChevronDown size={8} style={{ color: "#3b82f6" }} />;

  const purchasedIds = new Set(purchases.map(p => p.player.player_id));

  const baseCols = [
    { key: "xg_p90"      as SortCol, label: "xG/90",   color: "#ef4444" },
    { key: "xa_p90"      as SortCol, label: "xA/90",   color: "#10b981" },
    { key: "value_score" as SortCol, label: "Pt.Att.",  color: "#64748b" },
    { key: "max_bid_pct" as SortCol, label: "Max Bid%", color: "#64748b" },
  ];
  const advCols = [
    { key: "efo"            as SortCol, label: "EFO",      color: "#FF2A6D" },
    { key: "titolarita_pct" as SortCol, label: "Titol.%",  color: "#3b82f6" },
    { key: "luck_index"     as SortCol, label: "Luck Idx", color: "#f59e0b" },
    { key: "max_bid_pct"    as SortCol, label: "Max Bid%", color: "#64748b" },
  ];
  const cols = viewMode === "base" ? baseCols : advCols;

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr style={{ background: "#f8fafc", borderBottom: "1px solid #e2e8f0" }}>
            <th className="py-2.5 pl-4 pr-2 text-left">
              <span className="text-xs tabular-nums font-mono font-black uppercase tracking-wider" style={{ color: "#94a3b8" }}>{t("common.player")}</span>
            </th>
            <th className="py-2.5 px-2 text-left">
              <span className="text-xs tabular-nums font-mono font-black uppercase tracking-wider" style={{ color: "#94a3b8" }}>{t("common.position").slice(0, 1)}</span>
            </th>
            {cols.map(c => (
              <th key={c.key} className="py-2.5 px-2 text-right">
                <button onClick={() => toggle(c.key)} className="flex items-center gap-1 ml-auto"
                  style={{ color: sortKey === c.key ? "#3b82f6" : "#94a3b8" }}>
                  <span className="text-xs tabular-nums font-mono font-black uppercase tracking-wider">{c.label}</span>
                  <SortIcon k={c.key} />
                </button>
              </th>
            ))}
            {viewMode === "advanced" && (
              <th className="py-2.5 px-2 text-right">
                <span className="text-xs tabular-nums font-mono font-black uppercase tracking-wider" style={{ color: "#94a3b8" }}>Tag</span>
              </th>
            )}
            <th className="py-2.5 pl-2 pr-4 text-right">
              <span className="text-xs tabular-nums font-mono font-black uppercase tracking-wider" style={{ color: "#94a3b8" }}>{t("auction.buy_players_hint")}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((p, i) => {
            const rc       = ROLE_COLOR[p.position ?? "N/D"] ?? "#64748b";
            const isBought = purchasedIds.has(p.player_id);
            const defPrice = prices[p.player_id] ?? suggestedPrice(p, viewMode);
            const rowBg    = i % 2 !== 0 ? "#f8fafc" : "#ffffff";
            const li       = p.luck_index ?? 0;

            return (
              <motion.tr key={p.player_id}
                initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                transition={{ delay: Math.min(i * 0.007, 0.25) }}
                style={{ background: isBought ? "rgba(34,197,94,0.04)" : rowBg, borderBottom: "1px solid #e2e8f0", opacity: isBought ? 0.45 : 1 }}
              >
                {/* Name */}
                <td className="py-2 pl-4 pr-2">
                  <div>
                    <div className="text-sm tabular-nums font-black leading-none" style={{ fontFamily: "'Oswald', sans-serif", color: "#1E293B" }}>{p.player ?? "—"}</div>
                    <div className="text-[7px] font-mono mt-0.5" style={{ color: "#94a3b8" }}>{p.team ?? "—"}</div>
                  </div>
                </td>
                {/* Role */}
                <td className="py-2 px-2">
                  <span className="text-[7px] font-mono font-black px-1 py-0.5 rounded" style={{ color: rc, background: `${rc}12`, border: `1px solid ${rc}25` }}>{p.position ?? "—"}</span>
                </td>

                {/* Base columns */}
                {viewMode === "base" && <>
                  <td className="py-2 px-2 text-right"><span className="font-mono text-sm tabular-nums font-black" style={{ color: "#ef4444" }}>{sf(p.xg_p90, 3)}</span></td>
                  <td className="py-2 px-2 text-right"><span className="font-mono text-sm tabular-nums font-black" style={{ color: "#10b981" }}>{sf(p.xa_p90, 3)}</span></td>
                  <td className="py-2 px-2 text-right"><span className="font-mono text-sm tabular-nums" style={{ color: "#64748b" }}>{sf(p.value_score, 1)}</span></td>
                  <td className="py-2 px-2 text-right"><span className="font-mono text-sm tabular-nums" style={{ color: "#64748b" }}>{sf(p.max_bid_pct, 1)}%</span></td>
                </>}

                {/* Advanced columns */}
                {viewMode === "advanced" && <>
                  <td className="py-2 px-2 text-right">
                    <span className="font-mono text-sm tabular-nums font-black" style={{ color: "#FF2A6D" }}>{sf(p.efo, 2)}</span>
                  </td>
                  <td className="py-2 px-2 text-right">
                    <span className="font-mono text-sm tabular-nums font-black" style={{ color: "#3b82f6" }}>{sf(p.titolarita_pct, 1)}%</span>
                  </td>
                  <td className="py-2 px-2 text-right">
                    <span className="font-mono text-sm tabular-nums font-black" style={{ color: luckColor(li) }}>
                      {li >= 0 ? "+" : ""}{sf(li, 2)}
                    </span>
                  </td>
                  <td className="py-2 px-2 text-right"><span className="font-mono text-sm tabular-nums" style={{ color: "#64748b" }}>{sf(p.max_bid_pct, 1)}%</span></td>
                  <td className="py-2 px-2 text-right"><LuckBadge li={li} /></td>
                </>}

                {/* Buy */}
                <td className="py-2 pl-2 pr-4">
                  {isBought ? (
                    <span className="text-[7px] font-mono font-black uppercase tracking-widest px-2 py-1 rounded"
                      style={{ color: "#22c55e", background: "rgba(34,197,94,0.08)", border: "1px solid rgba(34,197,94,0.2)" }}>✓</span>
                  ) : (
                    <div className="flex items-center gap-1.5 justify-end">
                      <input type="number" value={defPrice} min={1} max={budget}
                        onChange={e => setPrices(prev => ({ ...prev, [p.player_id]: parseInt(e.target.value) || 1 }))}
                        className="w-12 outline-none text-[9px] font-mono font-black text-right rounded px-1 py-0.5"
                        style={{ border: "1px solid #e2e8f0", color: "#1E293B", background: "#f8fafc" }}
                      />
                      <button onClick={() => onBuy(p, defPrice)}
                        className="px-2 py-1 rounded text-[7px] font-mono font-black transition-all hover:opacity-80 flex-shrink-0"
                        style={{ background: "rgba(34,197,94,0.08)", border: "1px solid rgba(34,197,94,0.25)", color: "#22c55e" }}>
                        <Plus size={9} />
                      </button>
                    </div>
                  )}
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

export default function AuctionView({ season = "2025", mode: aMode = "iniziale", league, year }: AuctionViewProps) {
  const [players,   setPlayers]   = useState<ApiPlayer[]>([]);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState<string | null>(null);
  const [budget,    setBudget]    = useState(500);
  const [purchases, setPurchases] = useState<Purchase[]>([]);
  const [viewMode,  setViewMode]  = useState<ViewMode>("base");

  useEffect(() => {
    const ctrl = new AbortController();
    setLoading(true);
    setError(null);
    setPlayers([]);

    const params = new URLSearchParams({ league, filter: "current" });
    if (year) params.set("year", String(year));
    fetch(`${FANTA_API}/players?${params}`, { signal: ctrl.signal })
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then((d: unknown) => {
        setPlayers(Array.isArray(d) ? (d as ApiPlayer[]) : []);
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

  const remaining = budget - purchases.reduce((a, p) => a + p.price, 0);

  const scatterData = useMemo(() => players.map(p => ({
    ...p,
    _x: viewMode === "base" ? (p.value_score ?? 0) : (p.efo ?? 0),
    _y: viewMode === "base" ? realPtsPerGame(p)     : (p.titolarita_pct ?? 0),
  })), [players, viewMode]);

  const diagMax = useMemo(() => {
    if (viewMode !== "base" || !players.length) return 5;
    return Math.max(...players.map(p => p.value_score ?? 0), 5);
  }, [players, viewMode]);

  const diagonal = viewMode === "base"
    ? [{ x: 0, y: 0 }, { x: diagMax, y: diagMax }]
    : [];

  const overperformers  = players.filter(p => (p.luck_index ?? 0) > 1.0).length;
  const underperformers = players.filter(p => (p.luck_index ?? 0) < -1.0).length;

  const handleBuy = (player: ApiPlayer, price: number) => {
    if (purchases.find(p => p.player.player_id === player.player_id)) return;
    if (price > remaining) return;
    setPurchases(prev => [...prev, { player, price }]);
  };

  const handleRemove = (id: string) => {
    setPurchases(prev => prev.filter(p => p.player.player_id !== id));
  };

  const { t } = useTranslation();

  return (
    <div className="space-y-4" suppressHydrationWarning>
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ background: "rgba(255,42,109,0.06)", border: "1px solid rgba(255,42,109,0.18)" }}>
          <TrendingUp size={15} style={{ color: "#FF2A6D" }} />
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="font-black uppercase tracking-tighter leading-none"
            style={{ fontFamily: "'Oswald', sans-serif", fontSize: "1.15rem", color: "#1E293B" }}>
            {t("auction.title")}
          </h2>
          <p className="text-xs tabular-nums font-mono uppercase tracking-[0.2em] mt-0.5" style={{ color: "#94a3b8" }}>
            {loading ? t("auction.loading_data") : error ? t("auction.connection_error")
              : t("auction.players_count", { count: players.length, league, mode: aMode })}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {!loading && !error && (
            <>
              <span className="px-2.5 py-1 rounded-full text-xs tabular-nums font-mono font-black uppercase tracking-widest"
                style={{ color: "#10b981", background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.2)" }}>
                {underperformers} {t("auction.alpha_value")}
              </span>
              <span className="px-2.5 py-1 rounded-full text-xs tabular-nums font-mono font-black uppercase tracking-widest"
                style={{ color: "#ef4444", background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)" }}>
                {overperformers} {t("auction.risk")}
              </span>
            </>
          )}
          <div className="flex items-center gap-1.5 pl-2" style={{ borderLeft: "1px solid #e2e8f0" }}>
            <span className="text-[7px] font-mono uppercase tracking-widest" style={{ color: "#94a3b8" }}>Budget</span>
            <input type="number" value={budget} min={100} max={5000} step={50}
              onChange={e => setBudget(parseInt(e.target.value) || 500)}
              className="w-16 outline-none text-center text-sm tabular-nums font-mono font-black rounded px-1.5 py-1"
              style={{ border: "1px solid #e2e8f0", color: "#22c55e", background: "#f8fafc" }}
            />
          </div>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="flex gap-4 items-start">

        {/* Main */}
        <div className="flex-1 min-w-0 space-y-4">

          {/* Scatter chart */}
          <div className="rounded-xl p-5" style={{ background: "#ffffff", border: "1px solid #e2e8f0" }}>
            <div className="flex items-center justify-between mb-1">
              <div>
                <div className="text-xs tabular-nums font-mono font-black uppercase tracking-[0.28em]" style={{ color: "#3b82f6" }}>
                  {viewMode === "base" ? t("auction.chart_tvi") : t("auction.chart_tefo")}
                </div>
                <div className="text-[9px] font-mono mt-0.5" style={{ color: "#94a3b8" }}>
                  {viewMode === "base" ? t("auction.chart_tvi_sub") : t("auction.chart_tefo_sub")}
                </div>
              </div>
              <ModeToggle mode={viewMode} onChange={setViewMode} />
            </div>
            <div className="flex items-center gap-5 mt-3 mb-3 flex-wrap">
              {[
                { color: "#10b981", label: t("auction.alpha_value") },
                { color: "#64748b", label: t("auction.fair_value")  },
                { color: "#ef4444", label: t("auction.risk")        },
              ].map(l => (
                <div key={l.label} className="flex items-center gap-1.5">
                  <span className="rounded-full" style={{ width: 7, height: 7, background: l.color }} />
                  <span className="text-xs tabular-nums font-mono uppercase tracking-widest" style={{ color: "#94a3b8" }}>{l.label}</span>
                </div>
              ))}
            </div>
            <div style={{ background: "#f8fafc", borderRadius: 8, padding: "12px 4px 4px", border: "1px solid #e2e8f0" }}>
              <ResponsiveContainer width="100%" height={220}>
                <ComposedChart margin={{ top: 8, right: 20, bottom: 20, left: 0 }}>
                  <CartesianGrid stroke="#e2e8f0" strokeDasharray="4 4" strokeOpacity={0.8} />
                  <XAxis dataKey="_x" type="number" domain={[0, "auto"]} tickCount={6}
                    tick={{ fill: "#94a3b8", fontSize: 9, fontFamily: "ui-monospace, monospace", fontWeight: 700 }}
                    axisLine={{ stroke: "#e2e8f0" }} tickLine={{ stroke: "#e2e8f0" }}
                  />
                  <YAxis dataKey="_y" type="number" domain={[0, "auto"]} tickCount={6}
                    tick={{ fill: "#94a3b8", fontSize: 9, fontFamily: "ui-monospace, monospace", fontWeight: 700 }}
                    axisLine={{ stroke: "#e2e8f0" }} tickLine={{ stroke: "#e2e8f0" }}
                  />
                  <Tooltip content={<ScatterTip viewMode={viewMode} />} cursor={{ stroke: "rgba(59,130,246,0.2)", strokeDasharray: "4 4" }} />
                  {diagonal.length > 0 && (
                    <Line data={diagonal} dataKey="y" type="linear" dot={false} stroke="#e2e8f0" strokeDasharray="6 4" strokeWidth={1} />
                  )}
                  <Scatter data={scatterData} shape={<ScatterDot />} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Table */}
          <div className="rounded-xl overflow-hidden" style={{ background: "#ffffff", border: "1px solid #e2e8f0" }}>
            <div className="px-4 py-3 flex items-center justify-between" style={{ background: "#f8fafc", borderBottom: "1px solid #e2e8f0" }}>
              <div className="text-xs tabular-nums font-mono font-black uppercase tracking-[0.28em]" style={{ color: "#94a3b8" }}>
                {t("auction.base_value")} · {league} · {t("auction.suggested_price")}
              </div>
              <ModeToggle mode={viewMode} onChange={setViewMode} />
            </div>

            {loading ? (
              <SkeletonTable cols={viewMode === "base" ? 7 : 8} />
            ) : error ? (
              <div className="flex flex-col items-center py-16 gap-2">
                <AlertTriangle size={20} className="text-red-400" />
                <span className="text-[9px] font-mono text-red-400 uppercase tracking-widest">{error}</span>
                <span className="text-xs tabular-nums font-mono" style={{ color: "#94a3b8" }}>{t("auction.connection_error")}</span>
              </div>
            ) : players.length === 0 ? (
              <div className="flex flex-col items-center py-16 gap-2" style={{ color: "#94a3b8" }}>
                <Loader2 size={20} className="animate-spin" />
                <span className="text-[9px] font-mono uppercase tracking-widest">{t("common.no_data")}</span>
              </div>
            ) : (
              <AuctionTable data={players} purchases={purchases} onBuy={handleBuy} budget={budget} viewMode={viewMode} />
            )}
          </div>
        </div>

        {/* Budget sidebar */}
        <div className="flex-shrink-0" style={{ width: 220 }}>
          <MySidebar purchases={purchases} budget={budget} onRemove={handleRemove} />
        </div>
      </div>
    </div>
  );
}
