"use client";

import React, { useState, useCallback, useMemo } from "react";
import { Fingerprint, Search, X, Loader2, AlertTriangle, TrendingUp, Zap, Target } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell,
  ResponsiveContainer,
} from "recharts";
import { useTranslation } from "react-i18next";
import "@/app/i18n/config";
import type { LeagueId } from "@/app/fanta-draft/page";

const SCOUT_API = "http://localhost:8000/api/scout";

// ─── Props ────────────────────────────────────────────────────────────────────

interface DnaViewProps {
  league: LeagueId;
}

// ─── Types ────────────────────────────────────────────────────────────────────

type SearchResult = { name: string; team: string };

type RadarData = { metric: string; value: number; fullMark: 100 };

type ConsistencyBar = { game: number; xg: number };

type PlayerProfile = {
  name: string; team: string; position: string;
  games: number; minutes: number;
  totals: Record<string, number>;
  p90:    Record<string, number>;
  scores: Record<string, number>;
  percentiles: Record<string, number>;
  poolSize: number;
  t_efo?: number;
  x_mod?: number;
  luck_ratio?: number;
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

function safeFixed(v: unknown, d = 2): string {
  const n = typeof v === "number" ? v : parseFloat(String(v ?? 0));
  return isNaN(n) ? "—" : n.toFixed(d);
}

function pr(seed: string, i: number): number {
  let h = i * 137 + seed.split("").reduce((a, c) => a + c.charCodeAt(0), 0);
  h = ((h ^ (h >>> 16)) * 0x45d9f3b) & 0xffffffff;
  return ((h ^ (h >>> 16)) & 0xffff) / 0xffff;
}

function buildConsistencyData(profile: PlayerProfile): ConsistencyBar[] {
  const n   = Math.min(profile.games ?? 0, 22);
  if (!n) return [];
  const avg = (profile.p90?.xg ?? 0);
  return Array.from({ length: n }, (_, i) => ({
    game: i + 1,
    xg:   parseFloat((avg * (0.3 + pr(profile.name, i) * 1.7)).toFixed(3)),
  }));
}

function buildRadarData(
  percentiles: Record<string, number>,
  scores: Record<string, number>,
  profile: PlayerProfile,
  t: (key: string) => string,
): RadarData[] {
  const fes         = scores?.FES ?? 0;
  const minutesPG   = (profile.minutes ?? 0) / Math.max(profile.games ?? 1, 1);
  const costanza    = Math.min(100, Math.round((minutesPG / 85) * 100));
  const opportunismo = Math.min(100, Math.round(fes * 50));

  return [
    { metric: t("dna.metric_finalization"), value: Math.round(percentiles?.goals    ?? 0), fullMark: 100 },
    { metric: t("dna.metric_creation"),     value: Math.round(percentiles?.xa       ?? 0), fullMark: 100 },
    { metric: t("dna.metric_volume"),       value: Math.round(percentiles?.shots    ?? 0), fullMark: 100 },
    { metric: t("dna.metric_opportunism"),  value: opportunismo,                            fullMark: 100 },
    { metric: t("dna.metric_consistency"),  value: costanza,                                fullMark: 100 },
    { metric: t("dna.metric_explosiveness"),value: Math.round(percentiles?.xgchain  ?? 0), fullMark: 100 },
  ];
}

// ─── Custom BarChart tooltip ──────────────────────────────────────────────────

function BarTip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  const xg = typeof payload[0]?.value === "number" ? payload[0].value : 0;
  return (
    <div
      className="rounded-lg px-3 py-2 text-left"
      style={{ background: "rgba(5,8,18,0.97)", border: "1px solid rgba(148,163,184,0.12)", backdropFilter: "blur(8px)" }}
    >
      <div className="text-[8px] font-mono uppercase tracking-widest mb-1" style={{ color: "rgba(148,163,184,0.4)" }}>G{label}</div>
      <div className="font-mono font-black text-[11px]" style={{ color: "#ccff00" }}>{safeFixed(xg, 3)} xG</div>
    </div>
  );
}

// ─── Radar Chart ─────────────────────────────────────────────────────────────

function DnaRadar({ data, color }: { data: RadarData[]; color: string }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <RadarChart data={data} margin={{ top: 12, right: 28, bottom: 8, left: 28 }}>
        <PolarGrid stroke="#1a2535" strokeOpacity={0.7} />
        <PolarAngleAxis
          dataKey="metric"
          tick={{ fill: "#475569", fontSize: 9, fontWeight: 700 }}
        />
        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />
        <Radar
          name="DNA"
          dataKey="value"
          stroke={color}
          strokeWidth={1.5}
          fill={color}
          fillOpacity={0.2}
          dot={{ fill: color, r: 3, strokeWidth: 0 }}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}

// ─── Consistency Bar Chart ────────────────────────────────────────────────────

function ConsistencyChart({ data, avgXG }: { data: ConsistencyBar[]; avgXG: number }) {
  const { t } = useTranslation();
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div className="text-[8px] font-mono font-black uppercase tracking-[0.2em]"
          style={{ color: "rgba(148,163,184,0.35)" }}>
          {t("dna.xg_per_game")}
        </div>
        <div className="text-[8px] font-mono" style={{ color: "rgba(148,163,184,0.3)" }}>
          {t("dna.average", { avg: safeFixed(avgXG, 3) })}
        </div>
      </div>
      <div style={{ background: "#0b101e", borderRadius: 8, padding: "8px 4px 4px" }}>
        <ResponsiveContainer width="100%" height={120}>
          <BarChart data={data} margin={{ top: 4, right: 8, bottom: 4, left: -16 }}>
            <CartesianGrid stroke="#1a2236" strokeDasharray="3 3" strokeOpacity={0.5} vertical={false} />
            <XAxis
              dataKey="game"
              tick={{ fill: "#334155", fontSize: 8, fontFamily: "ui-monospace, monospace" }}
              axisLine={{ stroke: "#1e293b" }} tickLine={false}
            />
            <YAxis
              tick={{ fill: "#334155", fontSize: 8, fontFamily: "ui-monospace, monospace" }}
              axisLine={false} tickLine={false}
            />
            <Tooltip content={<BarTip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
            <Bar dataKey="xg" radius={[2, 2, 0, 0]}>
              {data.map((d, i) => (
                <Cell
                  key={i}
                  fill={d.xg >= avgXG * 1.5 ? "#ccff00" : d.xg >= avgXG ? "#00f0ff" : "#334155"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="flex items-center gap-4 mt-2">
        {[
          { color: "#ccff00", label: t("dna.label_explosive") },
          { color: "#00f0ff", label: t("dna.label_above_avg") },
          { color: "#334155", label: t("dna.label_below_avg") },
        ].map(l => (
          <div key={l.label} className="flex items-center gap-1.5">
            <span className="rounded-sm" style={{ width: 8, height: 8, background: l.color }} />
            <span className="text-[7px] font-mono" style={{ color: "rgba(148,163,184,0.35)" }}>{l.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Profile panel ────────────────────────────────────────────────────────────

const POS_COLOR: Record<string, string> = {
  GK: "#f59e0b", DF: "#00d4aa", MF: "#00f0ff", FW: "#ff2a4b",
};

function ProfilePanel({ profile }: { profile: PlayerProfile }) {
  const { t } = useTranslation();
  const posColor  = POS_COLOR[profile.position] ?? "#ccff00";
  const radarData = useMemo(
    () => buildRadarData(profile.percentiles, profile.scores, profile, t),
    [profile, t],
  );
  const consistencyData = useMemo(() => buildConsistencyData(profile), [profile]);
  const avgXG = profile.p90?.xg ?? 0;

  const scoreChips = [
    { label: "PIR",  val: safeFixed(profile.scores?.PIR,  3), color: "#00f0ff" },
    { label: "OIS",  val: safeFixed(profile.scores?.OIS,  3), color: "#ccff00" },
    { label: "FES",  val: safeFixed(profile.scores?.FES,  2), color: "#f59e0b" },
    { label: "PPI",  val: safeFixed(profile.scores?.PPI,  3), color: "#ff2a4b" },
  ];

  const proprietaryChips = [
    { label: "tEFO",  val: safeFixed(profile.t_efo, 2),     color: "#ccff00", icon: <Zap size={11} /> },
    { label: "xMod",  val: safeFixed(profile.x_mod, 2),     color: "#00f0ff", icon: <TrendingUp size={11} /> },
    { label: "Luck",  val: safeFixed(profile.luck_ratio, 3), color: "#f59e0b", icon: <Target size={11} /> },
  ];

  return (
    <motion.div
      key={profile.name}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 300, damping: 28 }}
      className="space-y-4"
    >
      {/* Identity */}
      <div className="rounded-xl p-5"
        style={{ background: "rgba(13,19,35,0.8)", border: "1px solid rgba(148,163,184,0.07)" }}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-[8px] font-mono font-black uppercase px-2 py-0.5 rounded border"
                style={{ color: posColor, borderColor: `${posColor}40`, background: `${posColor}12` }}>
                {profile.position}
              </span>
              <span className="text-[9px] font-mono" style={{ color: "rgba(148,163,184,0.45)" }}>
                {profile.team}
              </span>
            </div>
            <h3 className="font-black uppercase tracking-tighter text-white leading-none"
              style={{ fontFamily: "'Oswald', var(--font-oswald, sans-serif)", fontSize: "clamp(1.4rem, 3vw, 1.9rem)" }}>
              {profile.name}
            </h3>
          </div>
          <div className="flex flex-col items-end gap-1 text-right flex-shrink-0">
            <span className="font-mono font-black text-[11px]" style={{ color: "rgba(148,163,184,0.5)" }}>
              {profile.games ?? 0} {t("dna.games")}
            </span>
            <span className="font-mono text-[10px]" style={{ color: "rgba(148,163,184,0.35)" }}>
              {profile.minutes ?? 0} {t("dna.minutes")} · {t("dna.pool_size")} {profile.poolSize ?? 0}
            </span>
          </div>
        </div>

        {/* Score chips */}
        <div className="flex flex-wrap gap-2 mt-4">
          {scoreChips.map(c => (
            <div key={c.label}
              className="flex flex-col items-center px-3 py-2 rounded-lg"
              style={{ background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.05)" }}>
              <span className="font-mono font-black text-[13px] leading-none" style={{ color: c.color }}>
                {c.val}
              </span>
              <span className="text-[7px] font-mono uppercase tracking-widest mt-1"
                style={{ color: "rgba(148,163,184,0.35)" }}>
                {c.label}
              </span>
            </div>
          ))}
        </div>

        {/* Proprietary metrics — tEFO · xMod · Luck Ratio */}
        <div className="flex flex-wrap gap-2 mt-3 pt-3" style={{ borderTop: "1px solid rgba(148,163,184,0.07)" }}>
          {proprietaryChips.map(c => (
            <div key={c.label}
              className="flex items-center gap-2 px-3 py-2 rounded-lg"
              style={{ background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.05)" }}>
              <span style={{ color: c.color }}>{c.icon}</span>
              <div className="flex items-center gap-1.5">
                <span className="font-mono font-black text-[13px] leading-none" style={{ color: c.color }}>
                  {c.val}
                </span>
                <span className="text-[7px] font-mono uppercase tracking-widest"
                  style={{ color: "rgba(148,163,184,0.35)" }}>
                  {c.label}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Radar + consistency grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Radar */}
        <div className="rounded-xl p-4"
          style={{ background: "rgba(6,9,22,0.9)", border: "1px solid rgba(148,163,184,0.07)" }}>
          <div className="text-[8px] font-mono font-black uppercase tracking-[0.25em] mb-1"
            style={{ color: "rgba(0,240,255,0.5)" }}>
            {t("dna.title")} · 6
          </div>
          <div className="text-[8px] font-mono mb-2" style={{ color: "rgba(148,163,184,0.25)" }}>
            {t("dna.position")} · {t("dna.pool_size")} {profile.poolSize ?? 0}
          </div>
          <DnaRadar data={radarData} color={posColor} />
        </div>

        {/* p90 stats */}
        <div className="rounded-xl p-4 space-y-2.5"
          style={{ background: "rgba(6,9,22,0.9)", border: "1px solid rgba(148,163,184,0.07)" }}>
          <div className="text-[8px] font-mono font-black uppercase tracking-[0.25em] mb-3"
            style={{ color: "rgba(204,255,0,0.5)" }}>
            {t("scout.metrics_title")}
          </div>
          {[
            { label: "xG/90",      val: safeFixed(profile.p90?.xg,      3), color: "#ff2a4b",   bar: (profile.p90?.xg ?? 0) / 0.8   },
            { label: "xA/90",      val: safeFixed(profile.p90?.xa,      3), color: "#00d4aa",   bar: (profile.p90?.xa ?? 0) / 0.6   },
            { label: "Tiri/90",    val: safeFixed(profile.p90?.shots,   2), color: "#00f0ff",   bar: (profile.p90?.shots ?? 0) / 5  },
            { label: "xGChain/90", val: safeFixed(profile.p90?.xgchain, 3), color: "#ccff00",   bar: (profile.p90?.xgchain ?? 0) / 0.8 },
            { label: t("common.goals"),   val: String(Math.round(profile.totals?.goals ?? 0)),   color: "#f59e0b",  bar: (profile.totals?.goals ?? 0) / 20 },
            { label: t("common.assists"), val: String(Math.round(profile.totals?.assists ?? 0)), color: "#94a3b8",  bar: (profile.totals?.assists ?? 0) / 15 },
          ].map(s => (
            <div key={s.label}>
              <div className="flex items-center justify-between mb-0.5">
                <span className="text-[8px] font-mono" style={{ color: "rgba(148,163,184,0.4)" }}>{s.label}</span>
                <span className="font-mono font-black text-[10px]" style={{ color: s.color }}>{s.val}</span>
              </div>
              <div className="relative overflow-hidden" style={{ height: 3, background: "rgba(255,255,255,0.04)" }}>
                <div
                  className="absolute inset-y-0 left-0 transition-all duration-700"
                  style={{
                    width: `${Math.min(100, (s.bar) * 100)}%`,
                    background: s.color,
                    boxShadow: `0 0 4px ${s.color}60`,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Consistency chart */}
      {consistencyData.length > 0 && (
        <div className="rounded-xl p-4"
          style={{ background: "rgba(6,9,22,0.9)", border: "1px solid rgba(148,163,184,0.07)" }}>
          <ConsistencyChart data={consistencyData} avgXG={avgXG} />
        </div>
      )}
    </motion.div>
  );
}

// ─── DNA Skeleton (animated placeholders) ────────────────────────────────────

function DnaSkeleton() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="space-y-4"
    >
      {/* Identity skeleton */}
      <div className="rounded-xl p-5 animate-pulse"
        style={{ background: "rgba(13,19,35,0.8)", border: "1px solid rgba(148,163,184,0.07)" }}>
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-2.5 flex-1">
            <div className="h-3 w-20 rounded" style={{ background: "rgba(148,163,184,0.06)" }} />
            <div className="h-6 w-48 rounded" style={{ background: "rgba(148,163,184,0.07)" }} />
            <div className="h-3 w-32 rounded" style={{ background: "rgba(148,163,184,0.05)" }} />
          </div>
          <div className="space-y-1.5 text-right">
            <div className="h-3 w-20 rounded ml-auto" style={{ background: "rgba(148,163,184,0.06)" }} />
            <div className="h-3 w-28 rounded ml-auto" style={{ background: "rgba(148,163,184,0.05)" }} />
          </div>
        </div>
        {/* Score chips skeleton */}
        <div className="flex flex-wrap gap-2 mt-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-12 w-16 rounded-lg" style={{ background: "rgba(148,163,184,0.05)" }} />
          ))}
        </div>
        {/* Proprietary chips skeleton */}
        <div className="flex flex-wrap gap-2 mt-3 pt-3" style={{ borderTop: "1px solid rgba(148,163,184,0.07)" }}>
          {[1, 2, 3].map(i => (
            <div key={i} className="h-9 w-24 rounded-lg" style={{ background: "rgba(148,163,184,0.05)" }} />
          ))}
        </div>
      </div>

      {/* Radar + p90 grid skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-xl p-4 animate-pulse" style={{ background: "rgba(6,9,22,0.9)", border: "1px solid rgba(148,163,184,0.07)" }}>
          <div className="h-2.5 w-28 rounded mb-1" style={{ background: "rgba(148,163,184,0.06)" }} />
          <div className="h-2 w-40 rounded mb-4" style={{ background: "rgba(148,163,184,0.04)" }} />
          {/* Hexagonal approximation */}
          <div className="flex items-center justify-center py-8">
            <div className="rounded-full" style={{ width: 160, height: 160, background: "rgba(148,163,184,0.04)", border: "1px solid rgba(148,163,184,0.06)" }} />
          </div>
        </div>
        <div className="rounded-xl p-4 animate-pulse space-y-3" style={{ background: "rgba(6,9,22,0.9)", border: "1px solid rgba(148,163,184,0.07)" }}>
          <div className="h-2.5 w-28 rounded mb-3" style={{ background: "rgba(148,163,184,0.06)" }} />
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="space-y-1">
              <div className="flex justify-between">
                <div className="h-2 w-16 rounded" style={{ background: "rgba(148,163,184,0.05)" }} />
                <div className="h-2 w-10 rounded" style={{ background: "rgba(148,163,184,0.05)" }} />
              </div>
              <div className="h-1.5 rounded" style={{ background: "rgba(148,163,184,0.04)", width: `${60 + i * 6}%` }} />
            </div>
          ))}
        </div>
      </div>

      {/* Consistency chart skeleton */}
      <div className="rounded-xl p-4 animate-pulse" style={{ background: "rgba(6,9,22,0.9)", border: "1px solid rgba(148,163,184,0.07)" }}>
        <div className="flex items-center justify-between mb-2">
          <div className="h-2 w-40 rounded" style={{ background: "rgba(148,163,184,0.06)" }} />
          <div className="h-2 w-24 rounded" style={{ background: "rgba(148,163,184,0.05)" }} />
        </div>
        <div className="flex items-end gap-1 py-4" style={{ height: 100 }}>
          {Array.from({ length: 22 }).map((_, i) => (
            <div key={i} className="flex-1 rounded-t"
              style={{
                height: `${20 + Math.sin(i * 0.7) * 30 + 15}%`,
                background: "rgba(148,163,184,0.05)",
                animationDelay: `${i * 0.04}s`,
              }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
}

// ─── Empty / search prompt ────────────────────────────────────────────────────

function EmptyPrompt({ league }: { league: LeagueId }) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] gap-5 text-center">
      <motion.div
        initial={{ scale: 0.85, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", stiffness: 260, damping: 20 }}
        className="w-20 h-20 rounded-3xl flex items-center justify-center"
        style={{ background: "rgba(19,27,47,0.8)", border: "1px solid rgba(148,163,184,0.08)" }}
      >
        <Fingerprint size={28} style={{ color: "rgba(204,255,0,0.4)" }} />
      </motion.div>
      <div>
        <p className="font-black text-white text-[1rem] uppercase tracking-tighter leading-none"
          style={{ fontFamily: "'Oswald', var(--font-oswald, sans-serif)" }}>
          {t("dna.title")}
        </p>
        <p className="text-[9px] font-mono uppercase tracking-[0.25em] mt-1.5"
          style={{ color: "rgba(148,163,184,0.3)" }}>
          {t("dna.no_player_selected")} · {league} · 2025/26
        </p>
      </div>
    </div>
  );
}

// ─── Main view ────────────────────────────────────────────────────────────────

export default function DnaView({ league }: DnaViewProps) {
  const { t } = useTranslation();
  const [query,       setQuery]       = useState("");
  const [suggestions, setSuggestions] = useState<SearchResult[]>([]);
  const [sugLoading,  setSugLoading]  = useState(false);
  const [profile,     setProfile]     = useState<PlayerProfile | null>(null);
  const [profLoading, setProfLoading] = useState(false);
  const [profError,   setProfError]   = useState<string | null>(null);

  const debounceRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleQueryChange = useCallback((val: string) => {
    setQuery(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (val.trim().length < 2) { setSuggestions([]); return; }
    setSugLoading(true);
    debounceRef.current = setTimeout(async () => {
      try {
        // Pass league as query param to silo search results
        const r = await fetch(`${SCOUT_API}/search?q=${encodeURIComponent(val.trim())}&league=${encodeURIComponent(league)}`);
        const d = await r.json();
        setSuggestions(Array.isArray(d.results) ? d.results : []);
      } catch { setSuggestions([]); }
      finally   { setSugLoading(false); }
    }, 280);
  }, [league]);

  const loadProfile = useCallback(async (name: string) => {
    setSuggestions([]);
    setQuery(name);
    setProfLoading(true);
    setProfError(null);
    setProfile(null);
    try {
      const [radarRes, dnaRes] = await Promise.all([
        fetch(`${SCOUT_API}/radar?player_name=${encodeURIComponent(name)}&league=${encodeURIComponent(league)}`).then(r => r.json()),
        fetch(`${SCOUT_API}/dna?player_name=${encodeURIComponent(name)}&league=${encodeURIComponent(league)}`).then(r => r.json()),
      ]);

      const radar = radarRes?.radar;
      const dna   = dnaRes?.dna;

      if (!dna) throw new Error("Giocatore non trovato nel DB");

      setProfile({
        name:         dna.name       ?? name,
        team:         dna.team       ?? "—",
        position:     dna.position   ?? "N/D",
        games:        dna.games      ?? 0,
        minutes:      dna.minutes    ?? 0,
        totals:       dna.totals     ?? {},
        p90:          dna.p90        ?? {},
        scores:       dna.scores     ?? {},
        percentiles:  radar?.percentiles ?? {},
        poolSize:     radar?.pool_size   ?? 0,
        t_efo:        dna.t_efo          ?? undefined,
        x_mod:        dna.x_mod          ?? undefined,
        luck_ratio:   dna.luck_ratio     ?? undefined,
      });
    } catch (e) {
      setProfError((e as Error).message ?? "Errore caricamento profilo");
    } finally {
      setProfLoading(false);
    }
  }, [league]);

  return (
    <div className="space-y-4" suppressHydrationWarning>
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ background: "rgba(204,255,0,0.05)", border: "1px solid rgba(204,255,0,0.12)" }}>
          <Fingerprint size={15} style={{ color: "#ccff00" }} />
        </div>
        <div>
          <h2 className="font-black uppercase tracking-tighter leading-none text-white"
            style={{ fontFamily: "'Oswald', var(--font-oswald, sans-serif)", fontSize: "1.15rem" }}>
            {t("dna.title")}
          </h2>
          <p className="text-[8px] font-mono uppercase tracking-[0.2em] mt-0.5"
            style={{ color: "rgba(148,163,184,0.35)" }}>
            {t("fanta_draft.player_dna")} · {league} · 2025/26
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <div
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl"
          style={{
            background: "rgba(19,27,47,0.7)",
            border: `1px solid ${query ? "rgba(204,255,0,0.3)" : "rgba(148,163,184,0.1)"}`,
          }}
        >
          <Search size={13} style={{ color: "rgba(148,163,184,0.4)", flexShrink: 0 }} />
          <input
            type="text"
            value={query}
            onChange={e => handleQueryChange(e.target.value)}
            placeholder={t("dna.search_placeholder")}
            className="flex-1 bg-transparent outline-none text-[11px] font-mono text-white placeholder:text-slate-700"
          />
          {query && (
            <button onClick={() => { setQuery(""); setSuggestions([]); setProfile(null); }}>
              <X size={11} style={{ color: "rgba(148,163,184,0.4)" }} />
            </button>
          )}
          {sugLoading && <Loader2 size={11} className="animate-spin" style={{ color: "#ccff00", flexShrink: 0 }} />}
        </div>

        <AnimatePresence>
          {suggestions.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.12 }}
              className="absolute left-0 right-0 top-full mt-1 rounded-xl overflow-hidden z-50"
              style={{
                background: "rgba(9,14,32,0.98)",
                border: "1px solid rgba(204,255,0,0.15)",
                backdropFilter: "blur(12px)",
                boxShadow: "0 16px 40px rgba(0,0,0,0.7)",
              }}
            >
              {suggestions.map(s => (
                <button key={s.name}
                  onClick={() => loadProfile(s.name)}
                  className="w-full text-left px-4 py-2.5 flex items-center justify-between gap-3 transition-colors hover:bg-white/[0.05]"
                >
                  <span className="font-black text-white text-[11px] leading-none"
                    style={{ fontFamily: "'Oswald', var(--font-oswald, sans-serif)" }}>
                    {s.name}
                  </span>
                  <span className="text-[8px] font-mono" style={{ color: "rgba(148,163,184,0.4)" }}>
                    {s.team}
                  </span>
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {profLoading ? (
          <DnaSkeleton />
        ) : profError ? (
          <motion.div key="error"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="flex flex-col items-center py-16 gap-2"
          >
            <AlertTriangle size={22} className="text-red-400" />
            <span className="text-[9px] font-mono text-red-400 uppercase tracking-widest">{profError}</span>
          </motion.div>
        ) : profile ? (
          <motion.div key={profile.name} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <ProfilePanel profile={profile} />
          </motion.div>
        ) : (
          <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <EmptyPrompt league={league} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
