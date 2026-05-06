"use client";

import React, { useMemo } from "react";
import { motion } from "framer-motion";

// ─── Types ────────────────────────────────────────────────────────────────────

export type PlayerData = {
  name: string;
  team: string;
  role: string;
  opponent: string;
  next_match_ppda: number;
  next_match_deep_allowed: number;
  next_match_xg_allowed: number;
  form_xG: number;
  form_xA: number;
  total_shots_last_5: number;
  real_goals_last_5: number;
  real_assists_last_5: number;
};

// ─── Math Engine ──────────────────────────────────────────────────────────────

function compute(p: PlayerData) {
  const TREND = p.form_xG * 0.7 + p.form_xA * 0.5;
  const SHOT_QUALITY = p.form_xG / (p.total_shots_last_5 || 1);
  const ATTACK_INDEX = SHOT_QUALITY * 2 + p.total_shots_last_5 * 0.3;
  const MATCHUP =
    p.next_match_xg_allowed * 1.2 +
    p.next_match_deep_allowed * 0.08 -
    p.next_match_ppda * 0.05;
  const LUCK =
    p.form_xG - p.real_goals_last_5 + (p.form_xA - p.real_assists_last_5);
  const START_SCORE_RAW =
    TREND * 40 + ATTACK_INDEX * 25 + MATCHUP * 25 + LUCK * 10;
  const START_SCORE = Math.min(100, Math.max(0, START_SCORE_RAW));
  const EFO = (p.form_xG / 5) * 3 + (p.form_xA / 5) * 2;

  return { TREND, SHOT_QUALITY, ATTACK_INDEX, MATCHUP, LUCK, START_SCORE, EFO };
}

// ─── Verdict ──────────────────────────────────────────────────────────────────

type Verdict = { color: string; glow: string; label: string; tier: "green" | "amber" | "red" };

function verdict(score: number): Verdict {
  if (score >= 75)
    return { color: "#22C55E", glow: "rgba(34,197,94,0.3)", label: "MUST START", tier: "green" };
  if (score >= 50)
    return { color: "#EAB308", glow: "rgba(234,179,8,0.3)", label: "RISCHIO", tier: "amber" };
  return { color: "#EF4444", glow: "rgba(239,68,68,0.3)", label: "IN PANCA", tier: "red" };
}

// ─── Score Ring ───────────────────────────────────────────────────────────────

function ScoreRing({ score }: { score: number }) {
  const v = verdict(score);
  const R = 54;
  const C = 2 * Math.PI * R;
  const target = C - (score / 100) * C;

  return (
    <div className="relative flex items-center justify-center flex-shrink-0" style={{ width: 144, height: 144 }}>
      <svg width="144" height="144" style={{ transform: "rotate(-90deg)", overflow: "visible" }}>
        {/* Outer decorative tick ring */}
        {Array.from({ length: 36 }).map((_, i) => {
          const angle = (i / 36) * 2 * Math.PI;
          const x1 = 72 + 66 * Math.cos(angle);
          const y1 = 72 + 66 * Math.sin(angle);
          const x2 = 72 + 70 * Math.cos(angle);
          const y2 = 72 + 70 * Math.sin(angle);
          return (
            <line key={i} x1={x1} y1={y1} x2={x2} y2={y2}
              stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
          );
        })}
        {/* Track */}
        <circle cx="72" cy="72" r={R} fill="none"
          stroke="rgba(255,255,255,0.04)" strokeWidth="7" />
        {/* Glow duplicate */}
        <motion.circle cx="72" cy="72" r={R} fill="none"
          stroke={v.color} strokeWidth="11" strokeLinecap="round"
          strokeDasharray={C}
          initial={{ strokeDashoffset: C }}
          animate={{ strokeDashoffset: target }}
          transition={{ duration: 1.4, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
          style={{ filter: `blur(4px) drop-shadow(0 0 6px ${v.color})`, opacity: 0.4 }}
        />
        {/* Main stroke */}
        <motion.circle cx="72" cy="72" r={R} fill="none"
          stroke={v.color} strokeWidth="7" strokeLinecap="round"
          strokeDasharray={C}
          initial={{ strokeDashoffset: C }}
          animate={{ strokeDashoffset: target }}
          transition={{ duration: 1.4, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
        />
      </svg>

      {/* Center content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-0.5">
        <motion.span
          initial={{ opacity: 0, scale: 0.7 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.7, type: "spring", stiffness: 300, damping: 20 }}
          className="font-black tabular-nums leading-none"
          style={{
            fontFamily: "'Oswald', var(--font-oswald, sans-serif)",
            fontSize: 40,
            color: v.color,
            textShadow: `0 0 24px ${v.glow}, 0 0 8px ${v.color}60`,
          }}
        >
          {Math.round(score)}
        </motion.span>
        <motion.span
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.9 }}
          className="text-[7px] font-black uppercase tracking-[0.22em]"
          style={{ color: v.color }}
        >
          {v.label}
        </motion.span>
      </div>
    </div>
  );
}

// ─── Metric Bar ───────────────────────────────────────────────────────────────

type BarConfig = {
  label: string;
  rawValue: number;
  displayValue: string;
  pct: number;
  color: string;
  index: number;
};

function MetricBar({ label, rawValue, displayValue, pct, color, index }: BarConfig) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 14 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.15 + index * 0.07, type: "spring", stiffness: 280, damping: 26 }}
    >
      <div className="flex items-center justify-between mb-1">
        <span
          className="text-[8px] font-black uppercase tracking-[0.22em]"
          style={{ color: "rgba(148,163,184,0.6)", letterSpacing: "0.18em" }}
        >
          {label}
        </span>
        <span className="text-[9px] font-black tabular-nums" style={{ color }}>
          {displayValue}
        </span>
      </div>
      <div
        className="relative h-1.5 rounded-full overflow-hidden"
        style={{ background: "rgba(255,255,255,0.04)" }}
      >
        <motion.div
          className="absolute inset-y-0 left-0 rounded-full"
          style={{
            background: `linear-gradient(90deg, ${color}70 0%, ${color} 100%)`,
            boxShadow: `0 0 6px ${color}80`,
          }}
          initial={{ width: "0%" }}
          animate={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
          transition={{ duration: 1.0, ease: [0.16, 1, 0.3, 1], delay: 0.25 + index * 0.07 }}
        />
      </div>
    </motion.div>
  );
}

// ─── Decision Explainer ───────────────────────────────────────────────────────

type ExplainerLine = { dot: string; text: string };

function buildExplainer(p: PlayerData, s: ReturnType<typeof compute>): ExplainerLine[] {
  const lines: ExplainerLine[] = [];

  if (s.LUCK > 0.6) {
    lines.push({
      dot: "#22C55E",
      text: `Underperforming: ha creato ${p.form_xG.toFixed(2)} xG ma segnato solo ${p.real_goals_last_5}. Il gol è statisticamente imminente.`,
    });
  } else if (s.LUCK < -0.6) {
    lines.push({
      dot: "#EF4444",
      text: `Overperforming: ha segnato ${p.real_goals_last_5} gol su appena ${p.form_xG.toFixed(2)} xG. Aspettarsi regressione.`,
    });
  }

  const MATCHUP_AVG = 1.4;
  if (s.MATCHUP > MATCHUP_AVG) {
    lines.push({
      dot: "#22C55E",
      text: `Matchup favorevole: ${p.opponent} concede ${p.next_match_xg_allowed.toFixed(2)} xG/partita e ${p.next_match_deep_allowed} passaggi profondi.`,
    });
  } else {
    lines.push({
      dot: "#EF4444",
      text: `Matchup difficile: ${p.opponent} pressa alto (PPDA ${p.next_match_ppda.toFixed(1)}) e concede poco in zona gol.`,
    });
  }

  if (s.ATTACK_INDEX > 3.5) {
    lines.push({
      dot: "#22C55E",
      text: `Volume d'attacco: ${p.total_shots_last_5} tiri nelle ultime 5 con qualità nel tiro (${(s.SHOT_QUALITY).toFixed(3)} xG/tiro).`,
    });
  } else if (s.TREND < 1.0) {
    lines.push({
      dot: "#EAB308",
      text: `Forma opaca: appena ${p.form_xG.toFixed(2)} xG e ${p.form_xA.toFixed(2)} xA nelle ultime 5 gare. Profilo di rischio.`,
    });
  }

  return lines.slice(0, 3);
}

// ─── Role badge color ─────────────────────────────────────────────────────────

const ROLE_COLOR: Record<string, string> = {
  FW: "#FF2A6D", MF: "#007AFF", DF: "#00D4AA", GK: "#F59E0B",
};

// ─── Main Component ───────────────────────────────────────────────────────────

export function FantasyPlayerCard({ playerData }: { playerData: PlayerData }) {
  const scores = useMemo(() => compute(playerData), [playerData]);
  const v = useMemo(() => verdict(scores.START_SCORE), [scores.START_SCORE]);
  const lines = useMemo(() => buildExplainer(playerData, scores), [playerData, scores]);
  const roleColor = ROLE_COLOR[playerData.role] ?? "#64748b";

  // Metric bar configs — normalized to display %
  const bars: BarConfig[] = [
    {
      label: "Trend",
      rawValue: scores.TREND,
      displayValue: scores.TREND.toFixed(2),
      pct: (scores.TREND / 3.5) * 100,
      color: "#FF2A6D",
      index: 0,
    },
    {
      label: "Attack",
      rawValue: scores.ATTACK_INDEX,
      displayValue: scores.ATTACK_INDEX.toFixed(2),
      pct: (scores.ATTACK_INDEX / 7.0) * 100,
      color: "#007AFF",
      index: 1,
    },
    {
      label: "Matchup",
      rawValue: scores.MATCHUP,
      displayValue: scores.MATCHUP.toFixed(2),
      pct: (scores.MATCHUP / 4.0) * 100,
      color: "#10B981",
      index: 2,
    },
    {
      label: "Luck Δ",
      rawValue: scores.LUCK,
      displayValue: (scores.LUCK >= 0 ? "+" : "") + scores.LUCK.toFixed(2),
      // Luck: map [-3, +3] → [0, 100], centre at 50
      pct: ((scores.LUCK + 3) / 6) * 100,
      color: scores.LUCK > 0.1 ? "#22C55E" : scores.LUCK < -0.1 ? "#EF4444" : "#64748b",
      index: 3,
    },
  ];

  return (
    <motion.article
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 260, damping: 26 }}
      className="relative overflow-hidden rounded-2xl w-full"
      style={{
        maxWidth: 500,
        background: "linear-gradient(150deg, #0e1228 0%, #070a18 55%, #0b0e20 100%)",
        border: "1px solid rgba(255,255,255,0.06)",
        boxShadow: `
          0 0 0 1px rgba(255,255,255,0.02),
          0 24px 64px rgba(0,0,0,0.7),
          0 0 48px ${v.glow},
          inset 0 1px 0 rgba(255,255,255,0.04)
        `,
      }}
    >
      {/* Grid texture overlay */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.025]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,1) 1px, transparent 1px)," +
            "linear-gradient(90deg, rgba(255,255,255,1) 1px, transparent 1px)",
          backgroundSize: "28px 28px",
        }}
      />

      {/* Top ambient glow */}
      <div
        className="pointer-events-none absolute -top-12 left-1/2 -translate-x-1/2 w-72 h-28 rounded-full blur-3xl"
        style={{ background: v.color, opacity: 0.08 }}
      />

      {/* Corner accent line */}
      <div
        className="absolute top-0 left-0 w-16 h-[2px] rounded-full"
        style={{ background: `linear-gradient(90deg, ${v.color}, transparent)` }}
      />

      {/* ── HEADER ───────────────────────────────────────────────────── */}
      <header className="relative px-6 pt-5 pb-4" style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <div className="flex items-start justify-between gap-4">

          {/* Player identity */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1.5">
              <span
                className="text-[8px] font-black uppercase tracking-[0.22em] px-2 py-0.5 rounded border"
                style={{
                  color: roleColor,
                  borderColor: `${roleColor}35`,
                  background: `${roleColor}12`,
                }}
              >
                {playerData.role}
              </span>
              <span
                className="text-[8px] font-black uppercase tracking-[0.18em]"
                style={{ color: "rgba(148,163,184,0.5)" }}
              >
                {playerData.team}
              </span>
            </div>
            <h2
              className="text-white leading-none truncate"
              style={{
                fontFamily: "'Oswald', var(--font-oswald, sans-serif)",
                fontSize: "clamp(1.3rem, 4vw, 1.7rem)",
                fontWeight: 700,
                letterSpacing: "-0.02em",
              }}
            >
              {playerData.name}
            </h2>
          </div>

          {/* Opponent pill */}
          <div
            className="flex-shrink-0 flex flex-col items-end gap-0.5"
          >
            <span
              className="text-[7px] font-black uppercase tracking-[0.3em]"
              style={{ color: "rgba(148,163,184,0.4)" }}
            >
              Prossima
            </span>
            <div
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg"
              style={{ background: "rgba(255,42,109,0.08)", border: "1px solid rgba(255,42,109,0.18)" }}
            >
              <span
                className="text-[8px] font-black uppercase tracking-widest"
                style={{ color: "rgba(148,163,184,0.5)" }}
              >
                vs
              </span>
              <span
                className="font-black uppercase leading-none"
                style={{
                  fontFamily: "'Oswald', var(--font-oswald, sans-serif)",
                  fontSize: "0.85rem",
                  color: "#FF2A6D",
                  letterSpacing: "-0.01em",
                }}
              >
                {playerData.opponent}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* ── BODY ─────────────────────────────────────────────────────── */}
      <div className="relative px-6 py-5 flex items-center gap-6">

        {/* LEFT: Score Ring */}
        <div className="flex flex-col items-center gap-2 flex-shrink-0">
          <ScoreRing score={scores.START_SCORE} />

          {/* Raw form chips */}
          <div className="flex gap-1.5 mt-0.5">
            {[
              { label: "xG", val: playerData.form_xG.toFixed(2), color: "#FF2A6D" },
              { label: "xA", val: playerData.form_xA.toFixed(2), color: "#007AFF" },
            ].map(c => (
              <div
                key={c.label}
                className="flex flex-col items-center px-2 py-1 rounded-lg"
                style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}
              >
                <span className="font-black tabular-nums text-[11px]" style={{ color: c.color }}>
                  {c.val}
                </span>
                <span
                  className="text-[7px] font-black uppercase tracking-widest"
                  style={{ color: "rgba(148,163,184,0.4)" }}
                >
                  {c.label}
                </span>
              </div>
            ))}
            <div
              className="flex flex-col items-center px-2 py-1 rounded-lg"
              style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}
            >
              <span className="font-black tabular-nums text-[11px] text-slate-300">
                {playerData.total_shots_last_5}
              </span>
              <span className="text-[7px] font-black uppercase tracking-widest text-slate-600">
                Tiri
              </span>
            </div>
          </div>
        </div>

        {/* RIGHT: Metric Bars */}
        <div className="flex-1 min-w-0 space-y-3.5">
          {bars.map(b => <MetricBar key={b.label} {...b} />)}
        </div>
      </div>

      {/* ── FOOTER ───────────────────────────────────────────────────── */}
      <footer
        className="relative px-6 pb-6 pt-4"
        style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}
      >
        {/* EFO hero */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="flex items-baseline gap-2 mb-4"
        >
          <span
            className="text-[7px] font-black uppercase tracking-[0.3em]"
            style={{ color: "rgba(148,163,184,0.4)" }}
          >
            EFO
          </span>
          <span
            className="font-black tabular-nums leading-none"
            style={{
              fontFamily: "'Oswald', var(--font-oswald, sans-serif)",
              fontSize: "2.1rem",
              color: "#F59E0B",
              textShadow: "0 0 28px rgba(245,158,11,0.45), 0 0 8px rgba(245,158,11,0.2)",
            }}
          >
            +{scores.EFO.toFixed(2)}
          </span>
          <span
            className="text-[8px] font-black uppercase tracking-[0.15em]"
            style={{ color: "rgba(148,163,184,0.45)" }}
          >
            pt bonus attesi
          </span>
        </motion.div>

        {/* Decision lines */}
        <div className="space-y-2.5">
          {lines.map((l, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.65 + i * 0.1 }}
              className="flex items-start gap-2.5"
            >
              <div
                className="mt-[4px] w-[5px] h-[5px] rounded-full flex-shrink-0"
                style={{
                  background: l.dot,
                  boxShadow: `0 0 7px ${l.dot}`,
                }}
              />
              <p
                className="text-[10px] leading-relaxed font-medium"
                style={{ color: "rgba(148,163,184,0.75)" }}
              >
                {l.text}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Bottom stat strip */}
        <div
          className="flex items-center gap-4 mt-4 pt-4"
          style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}
        >
          {[
            { label: "Gol (5g)", val: playerData.real_goals_last_5, color: "#FF2A6D" },
            { label: "Assist (5g)", val: playerData.real_assists_last_5, color: "#007AFF" },
            { label: "PPDA avv.", val: playerData.next_match_ppda.toFixed(1), color: "#94a3b8" },
            { label: "xG conc.", val: playerData.next_match_xg_allowed.toFixed(2), color: "#94a3b8" },
          ].map(s => (
            <div key={s.label} className="flex flex-col gap-0.5">
              <span
                className="font-black tabular-nums text-[12px]"
                style={{ color: s.color, fontFamily: "'Oswald', var(--font-oswald, sans-serif)" }}
              >
                {s.val}
              </span>
              <span
                className="text-[7px] font-black uppercase tracking-widest"
                style={{ color: "rgba(148,163,184,0.35)" }}
              >
                {s.label}
              </span>
            </div>
          ))}
        </div>
      </footer>
    </motion.article>
  );
}

// ─── Mock Data — Kevin De Bruyne ──────────────────────────────────────────────

export const KDB_MOCK: PlayerData = {
  name: "Kevin De Bruyne",
  team: "Manchester City",
  role: "MF",
  opponent: "Arsenal",
  next_match_ppda: 8.2,
  next_match_deep_allowed: 12,
  next_match_xg_allowed: 1.4,
  form_xG: 1.85,
  form_xA: 2.1,
  total_shots_last_5: 14,
  real_goals_last_5: 1,
  real_assists_last_5: 2,
};

// ─── Isolated Preview Page (default export) ───────────────────────────────────

export default function FantasyCardPreview() {
  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center gap-8 p-8"
      style={{ background: "radial-gradient(ellipse at top, #0d1228 0%, #030508 70%)" }}
    >
      {/* Header */}
      <div className="text-center mb-2">
        <p
          className="text-[9px] font-black uppercase tracking-[0.4em] mb-2"
          style={{ color: "rgba(148,163,184,0.35)" }}
        >
          Start / Sit Engine · Preview
        </p>
        <h1
          className="text-white font-black uppercase leading-none"
          style={{
            fontFamily: "'Oswald', var(--font-oswald, sans-serif)",
            fontSize: "clamp(1.5rem, 4vw, 2.2rem)",
            letterSpacing: "-0.02em",
          }}
        >
          Fantasy <span style={{ color: "#FF2A6D" }}>Intelligence</span>
        </h1>
      </div>

      <FantasyPlayerCard playerData={KDB_MOCK} />

      {/* Score breakdown legend */}
      <div
        className="flex gap-6 text-[8px] font-black uppercase tracking-[0.2em]"
        style={{ color: "rgba(148,163,184,0.3)" }}
      >
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-[#22C55E] inline-block" />
          ≥ 75 Must Start
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-[#EAB308] inline-block" />
          50–74 Rischio
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-[#EF4444] inline-block" />
          &lt; 50 In Panca
        </span>
      </div>
    </div>
  );
}
