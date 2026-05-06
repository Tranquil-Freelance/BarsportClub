"use client";

import React from "react";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import "../../i18n/config";

// ─── Types ────────────────────────────────────────────────────────────────────

export type PlayerData = {
  name: string;
  team: string;
  role: string;
  efo: number;
  luck_index: number;
  titolarita_pct: number;
};

// ─── Role colors ─────────────────────────────────────────────────────────────

const ROLE_COLOR: Record<string, string> = {
  FW: "#ef4444", MF: "#3b82f6", DF: "#10b981", GK: "#f59e0b",
};

// ─── Main component ───────────────────────────────────────────────────────────

export function PremiumPlayerCard({ data }: { data: PlayerData }) {
  const { t } = useTranslation();
  const roleColor = ROLE_COLOR[data.role] ?? "#64748b";

  // Luck Index: Green if negative (underperforming, due for regression up),
  // Red if positive (overperforming, due for regression down)
  const luckColor  = data.luck_index < 0 ? "#22c55e" : "#ef4444";
  const luckLabel  = data.luck_index < 0 ? t("fanta.underperform") : t("fanta.overperform");
  const luckIcon   = data.luck_index < 0 ? "↓" : "↑";

  // Format EFO
  const efoInt     = Math.round(data.efo);

  return (
    <motion.article
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 280, damping: 26 }}
      className="group relative overflow-hidden flex flex-col"
      style={{
        background: "rgba(255,255,255,0.03)",
        border: "1px solid rgba(255,255,255,0.06)",
        borderRadius: 12,
        transition: "border-color 200ms, box-shadow 200ms",
      }}
      whileHover={{ borderColor: "rgba(255,42,109,0.4)", boxShadow: "0 4px 24px rgba(255,42,109,0.08)" } as any}
    >
      {/* Pink accent bar */}
      <div style={{ height: 3, background: "linear-gradient(90deg, #FF2A6D, rgba(255,42,109,0.15))" }} />

      {/* ── HEADER ── */}
      <div className="flex items-center gap-3 px-4 pt-3.5 pb-3" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <span
          className="font-mono text-[8px] font-black uppercase tracking-widest flex-shrink-0"
          style={{
            color: roleColor,
            border: `1px solid ${roleColor}40`,
            background: `${roleColor}12`,
            padding: "2px 6px",
            borderRadius: 4,
          }}
        >
          {data.role}
        </span>
        <span
          className="flex-1 min-w-0 font-black uppercase tracking-tighter truncate leading-none"
          style={{ fontFamily: "'Oswald', var(--font-oswald, sans-serif)", fontSize: "1rem", color: "#f1f5f9" }}
        >
          {data.name}
        </span>
        <span
          className="flex-shrink-0 text-[9px] font-mono font-bold uppercase tracking-wider"
          style={{ color: "#64748b" }}
        >
          {data.team}
        </span>
      </div>

      {/* ── BODY: EFO HERO ── */}
      <div className="flex flex-col items-center justify-center px-4 py-6 gap-1">
        {/* EFO big number */}
        <motion.span
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="font-mono font-black leading-none"
          style={{ fontSize: "3.5rem", color: "#f1f5f9", lineHeight: 1 }}
        >
          {efoInt}
        </motion.span>
        <motion.span
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.15 }}
          className="font-mono text-[9px] font-black uppercase tracking-[0.25em]"
          style={{ color: "#64748b" }}
        >
          {t("fanta.efo_label")}
        </motion.span>
        <motion.span
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.25 }}
          className="font-mono text-[10px] font-bold"
          style={{ color: "#94a3b8" }}
        >
          {data.efo.toFixed(2)} pts/90'
        </motion.span>
      </div>

      {/* ── METRICS STRIP ── */}
      <div className="grid grid-cols-2 gap-px" style={{ background: "rgba(255,255,255,0.06)" }}>
        {/* Luck Index */}
        <div
          className="flex flex-col items-center justify-center gap-1 py-4"
          style={{ background: "rgba(255,255,255,0.02)" }}
        >
          <div className="flex items-center gap-1.5">
            <span
              className="font-mono text-[10px] font-black"
              style={{ color: luckColor }}
            >
              {luckIcon}
            </span>
            <span
              className="font-mono text-lg font-black leading-none"
              style={{ color: luckColor }}
            >
              {data.luck_index >= 0 ? "+" : ""}{data.luck_index.toFixed(2)}
            </span>
          </div>
          <span
            className="font-mono text-[7px] font-black uppercase tracking-[0.2em]"
            style={{ color: "#64748b" }}
          >
            {t("fanta.luck_index")}
          </span>
          <span
            className="font-mono text-[7px] font-black uppercase tracking-[0.15em]"
            style={{ color: luckColor }}
          >
            {luckLabel}
          </span>
        </div>

        {/* Titolarità */}
        <div
          className="flex flex-col items-center justify-center gap-1 py-4"
          style={{ background: "rgba(255,255,255,0.02)" }}
        >
          <span
            className="font-mono text-lg font-black leading-none"
            style={{ color: "#f1f5f9" }}
          >
            {Math.round(data.titolarita_pct)}%
          </span>
          <span
            className="font-mono text-[7px] font-black uppercase tracking-[0.2em]"
            style={{ color: "#64748b" }}
          >
            {t("fanta.titolarita")}
          </span>
          <div
            className="w-20 h-1 rounded-full overflow-hidden"
            style={{ background: "rgba(255,255,255,0.08)" }}
          >
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(100, data.titolarita_pct)}%` }}
              transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1], delay: 0.3 }}
              className="h-full rounded-full"
              style={{
                background:
                  data.titolarita_pct >= 70
                    ? "#22c55e"
                    : data.titolarita_pct >= 40
                    ? "#f59e0b"
                    : "#ef4444",
              }}
            />
          </div>
        </div>
      </div>
    </motion.article>
  );
}
