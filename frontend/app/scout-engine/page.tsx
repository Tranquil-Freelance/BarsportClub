"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import dynamic from "next/dynamic";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslation } from "react-i18next";
import "../i18n/config";
import {
  Search, Flame, Sparkles, Target, Repeat, Scale,
  Zap, Activity, X, Users, TrendingUp, ChevronRight,
} from "lucide-react";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─── Types ────────────────────────────────────────────────────────────────────
interface Scores {
  OIS: number; CII: number; AIR: number; BCS: number;
  FES: number; PIR: number; MVGI: number; PPI: number;
}
interface PlayerDNA {
  name: string; team: string; position: string;
  games: number; minutes: number;
  age?: number | string;
  image_url?: string | null;
  totals: Record<string, number>;
  p90: Record<string, number>;
  scores: Scores;
}
interface AxisData { label: string; value: number; percentile: number; }
interface RadarData {
  player: PlayerDNA;
  percentiles: Record<string, number>;
  axes: Record<string, AxisData>;
  pool_size: number;
}
interface Replacement extends PlayerDNA { similarity: number; similarity_pct: number; }
interface ReplacementData { target: PlayerDNA; substitutes: Replacement[]; }
interface Leader { name: string; team: string; value: number; stat: string; }
interface Leaders { scorers: Leader[]; architects: Leader[]; }
interface Suggestion { name: string; team: string; }
interface Shot {
  X: number; Y: number; xG: number;
  result: string; minute: number; situation: string; shotType?: string;
}

type Tab = "home" | "target" | "replace" | "h2h" | "discover";

const TAB_DEFS: { id: Tab; key: string; Icon: React.ElementType }[] = [
  { id: "home",     key: "scout.home_tab",    Icon: Flame },
  { id: "target",   key: "scout.target_tab",  Icon: Target },
  { id: "replace",  key: "scout.replace_tab", Icon: Repeat },
  { id: "h2h",      key: "scout.h2h_tab",     Icon: Scale },
  { id: "discover", key: "scout.discover_tab",Icon: Zap },
];

const SCORE_CFG = [
  { key: "PIR",  label: "Player Impact Rating",    max: 0.5,  accent: "#FF2A6D" },
  { key: "OIS",  label: "Offensive Impact Score",  max: 0.6,  accent: "#FF2A6D" },
  { key: "CII",  label: "Creative Influence Index",max: 0.4,  accent: "#007AFF" },
  { key: "FES",  label: "Finishing Efficiency",    max: 2.0,  accent: "#10B981" },
  { key: "AIR",  label: "Attacking Involvement",   max: 0.02, accent: "#007AFF" },
  { key: "BCS",  label: "Buildup Contribution",    max: 0.015,accent: "#F59E0B" },
  { key: "PPI",  label: "Player Potential Index",  max: 0.5,  accent: "#F59E0B" },
  { key: "MVGI", label: "Market Value Gap",        max: 1.0,  accent: "#6B7280" },
];

const scoreColor = (pct: number, accent: string) => {
  if (pct > 0.7) return accent;
  if (pct > 0.4) return accent + "BB";
  return "#64748B";
};

const SERIE_A_PILLS: { name: string; team: string }[] = [
  { name: "Rafael Leão",      team: "Milan"      },
  { name: "Lautaro Martínez", team: "Inter"      },
  { name: "Kenan Yıldız",     team: "Juventus"   },
  { name: "Paulo Dybala",     team: "Roma"       },
  { name: "Ademola Lookman",  team: "Atalanta"   },
  { name: "Mateo Retegui",    team: "Atalanta"   },
  { name: "Marcus Thuram",    team: "Inter"      },
  { name: "Romelu Lukaku",    team: "Napoli"     },
  { name: "Moise Kean",       team: "Fiorentina" },
  { name: "Gudmundsson",      team: "Fiorentina" },
  { name: "Artem Dovbyk",     team: "Roma"       },
  { name: "Nicolò Barella",   team: "Inter"      },
];

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function ScoutEnginePage() {
  const { t } = useTranslation();
  const TABS = TAB_DEFS.map(d => ({ ...d, label: t(d.key) }));
  const [tab, setTab] = useState<Tab>("home");
  const [search, setSearch] = useState("");
  const [sugg, setSugg] = useState<Suggestion[]>([]);
  const [showSugg, setShowSugg] = useState(false);
  const [loading, setLoading] = useState(false);

  const [leaders, setLeaders] = useState<Leaders>({ scorers: [], architects: [] });
  const [dna, setDna] = useState<PlayerDNA | null>(null);
  const [radar, setRadar] = useState<RadarData | null>(null);
  const [shots, setShots] = useState<Shot[]>([]);
  const [hoveredShot, setHoveredShot] = useState<(Shot & { cx: number; cy: number }) | null>(null);
  const [replaceData, setReplaceData] = useState<ReplacementData | null>(null);
  const [p1, setP1] = useState<PlayerDNA | null>(null);
  const [p1Radar, setP1Radar] = useState<RadarData | null>(null);
  const [p2, setP2] = useState<PlayerDNA | null>(null);
  const [p2Radar, setP2Radar] = useState<RadarData | null>(null);
  const [talents, setTalents] = useState<PlayerDNA[]>([]);
  const [talentPos, setTalentPos] = useState("ALL");

  const debounce = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    fetch(`${API}/api/scout/leaders`)
      .then(r => r.json()).then(d => { if (!d.error) setLeaders(d); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (debounce.current) clearTimeout(debounce.current);
    if (search.length < 2) { setSugg([]); setShowSugg(false); return; }
    debounce.current = setTimeout(async () => {
      try {
        const r = await fetch(`${API}/api/scout/search?q=${encodeURIComponent(search)}`);
        const d = await r.json();
        const toSuggestion = (x: any): Suggestion => ({
          name: typeof x === "string" ? x : x.name ?? String(x),
          team: typeof x === "string" ? "" : x.team ?? "",
        });
        const results: Suggestion[] = d.results
          ? d.results.map(toSuggestion)
          : Array.isArray(d) ? d.map(toSuggestion) : [];
        setSugg(results);
        setShowSugg(results.length > 0);
      } catch { /* silently fail */ }
    }, 300);
  }, [search]);

  const loadPlayer = async (name: string, dest: "target" | "replace" | "h2h") => {
    setLoading(true); setShowSugg(false); setSearch("");
    if (dest === "target") { setDna(null); setRadar(null); setShots([]); setTab("target"); }
    else if (dest === "replace") { setReplaceData(null); setTab("replace"); }
    try {
      if (dest === "target") {
        const [dR, raR, shR] = await Promise.allSettled([
          fetch(`${API}/api/scout/dna?player_name=${encodeURIComponent(name)}`).then(r => r.json()),
          fetch(`${API}/api/scout/radar?player_name=${encodeURIComponent(name)}`).then(r => r.json()),
          fetch(`${API}/api/shots/${encodeURIComponent(name)}`).then(r => r.json()),
        ]);
        if (dR.status === "fulfilled" && dR.value.dna) setDna(dR.value.dna);
        if (raR.status === "fulfilled" && raR.value.radar) setRadar(raR.value.radar);
        setShots(shR.status === "fulfilled" && Array.isArray(shR.value) ? shR.value : []);
      } else if (dest === "replace") {
        const r = await fetch(`${API}/api/scout/replacement?player_name=${encodeURIComponent(name)}`);
        const d = await r.json();
        if (d && d.target) {
          setReplaceData(d);
        }
      } else {
        const [dR, raR] = await Promise.allSettled([
          fetch(`${API}/api/scout/dna?player_name=${encodeURIComponent(name)}`).then(r => r.json()),
          fetch(`${API}/api/scout/radar?player_name=${encodeURIComponent(name)}`).then(r => r.json()),
        ]);
        const dn = dR.status === "fulfilled" ? dR.value.dna : null;
        const rd = raR.status === "fulfilled" ? raR.value.radar : null;
        if (!p1) { setP1(dn); setP1Radar(rd); }
        else     { setP2(dn); setP2Radar(rd); }
      }
    } finally { setLoading(false); }
  };

  const loadDiscover = useCallback(async (pos: string) => {
    setTalentPos(pos); setLoading(true);
    try {
      const r = await fetch(`${API}/api/scout/discover?pos=${pos}&limit=24`);
      const d = await r.json();
      if (d.talents) setTalents(d.talents);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => {
    if (tab === "discover" && talents.length === 0) loadDiscover("ALL");
  }, [tab, loadDiscover, talents.length]);

  const dest: "target" | "replace" | "h2h" =
    tab === "replace" ? "replace" : tab === "h2h" ? "h2h" : "target";

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A]" suppressHydrationWarning>
      <style>{`
        @keyframes sc-spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
        .sc-spin { animation: sc-spin 1s linear infinite; }
        .sc-sugg:hover { background: #F1F5F9; }
        .sc-card-hover:hover { border-color: #FF2A6D !important; transform: translateY(-3px); box-shadow: 0 8px 30px rgba(255,42,109,0.18); }
        .sc-leader-row:hover { background: rgba(255,42,109,0.06); }
        .sc-talent-card:hover { border-color: #FF2A6D !important; transform: translateY(-3px); }
      `}</style>

      {/* PAGE HERO HEADER */}
      <div className="bg-[#0A192F] border-b-4 border-[#FF2A6D]">
        <div className="max-w-[1600px] mx-auto px-4 md:px-6">

          {/* Title row */}
          <div className="pt-6 md:pt-8 pb-4 flex items-end justify-between">
            <div>
              <p className="text-[#FF2A6D] text-[10px] font-black uppercase tracking-[0.3em] mb-1">
                {t("scout.subtitle")}
              </p>
              <h1 className="text-white font-black text-4xl uppercase tracking-tighter leading-none" style={{ fontFamily: "var(--font-oswald)" }}>
                {t("scout.page_title")}
              </h1>
            </div>
          </div>

          {/* Tab + Search row */}
          <div className="flex items-stretch justify-between border-t border-white/5">
            <div className="flex-1 overflow-x-auto min-w-0">
            <nav className="flex shrink-0">
              {TABS.map(({ id, label, Icon }) => (
                <button
                  key={id}
                  onClick={() => {
                    setTab(id);
                    // Se clicchi su Cloni e hai già un giocatore nel DNA, caricalo in automatico!
                    if (id === "replace" && dna && (!replaceData || replaceData.target.name !== dna.name)) {
                      loadPlayer(dna.name, "replace");
                    }
                    // Se clicchi su H2H e hai già un giocatore nel DNA, mettilo come Sfidante 1!
                    if (id === "h2h" && dna && !p1) {
                      loadPlayer(dna.name, "h2h");
                    }
                  }}
                  className="relative flex items-center gap-2 px-5 py-4 text-[11px] font-black uppercase tracking-[0.15em] transition-all"
                  style={{
                    fontFamily: "var(--font-oswald)",
                    color: tab === id ? "#FF2A6D" : "#64748B",
                    background: "none",
                    border: "none",
                    borderBottom: tab === id ? "2px solid #FF2A6D" : "2px solid transparent",
                    cursor: "pointer",
                    letterSpacing: "0.15em",
                  }}
                >
                  <Icon size={13} />
                  {label}
                </button>
              ))}
            </nav>
            </div>

            {/* Search */}
            <div className="hidden md:flex items-center py-3 relative shrink-0">
              <div className="flex items-center bg-white/5 border border-white/10 rounded-lg px-3 py-2 gap-2 w-72 focus-within:border-[#FF2A6D] transition-colors">
                <Search size={14} className="text-slate-500 shrink-0" />
                <input
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  onKeyDown={e => { if (e.key === "Enter" && sugg.length) loadPlayer(sugg[0].name, dest); }}
                  placeholder={t("scout.search_placeholder")}
                  className="bg-transparent outline-none text-white text-[12px] font-black uppercase w-full placeholder:text-slate-600"
                  style={{ fontFamily: "var(--font-oswald)" }}
                />
                {loading && <Activity size={13} className="text-[#FF2A6D] shrink-0 sc-spin" />}
              </div>

              <AnimatePresence>
                {showSugg && (
                  <motion.div
                    initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                    className="absolute top-full right-0 w-72 bg-white border border-slate-200 rounded-lg shadow-2xl overflow-hidden z-50 max-h-72 overflow-y-auto"
                    style={{ top: "calc(100% + 4px)" }}
                  >
                    {sugg.map((s, i) => (
                      <div
                        key={i}
                        onClick={() => loadPlayer(s.name, dest)}
                        className="sc-sugg flex justify-between items-center px-4 py-3 cursor-pointer border-b border-white/10 last:border-0"
                      >
                        <span className="font-black text-[13px] uppercase text-[#0A192F]" style={{ fontFamily: "var(--font-oswald)" }}>{s.name}</span>
                        {s.team && <span className="text-[10px] text-slate-400 font-medium">{s.team}</span>}
                      </div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <main className="max-w-[1600px] mx-auto px-4 md:px-6 py-6 md:py-8">
        <AnimatePresence mode="wait">
          <motion.div
            key={tab}
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.22 }}
          >
            {tab === "home"    && <HomeTab leaders={leaders} onLoad={n => loadPlayer(n, "target")} />}
            {tab === "target"  && <TargetTab dna={dna} radar={radar} shots={shots} hoveredShot={hoveredShot} setHoveredShot={setHoveredShot} onLoad={n => loadPlayer(n, "target")} loading={loading} />}
            {tab === "replace" && <ReplaceTab data={replaceData} onLoad={n => loadPlayer(n, "replace")} />}
            {tab === "h2h"     && <H2HTab p1={p1} p2={p2} r1={p1Radar} r2={p2Radar} onClear1={() => { setP1(null); setP1Radar(null); }} onClear2={() => { setP2(null); setP2Radar(null); }} />}
            {tab === "discover"&& <DiscoverTab talents={talents} loading={loading} pos={talentPos} onPos={loadDiscover} onLoad={n => loadPlayer(n, "target")} />}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// HOME TAB
// ═══════════════════════════════════════════════════════════════════════════════
function HomeTab({ leaders, onLoad }: { leaders: Leaders; onLoad: (n: string) => void }) {
  const { t } = useTranslation();
  return (
    <div>
      <div className="mb-8">
        <h2 className="text-3xl font-black uppercase tracking-tighter text-[#0A192F] mb-1" style={{ fontFamily: "var(--font-oswald)" }}>
          {t("scout.european_intel")}
        </h2>
        <p className="text-slate-400 text-[11px] uppercase tracking-[0.2em]">{t("scout.top_performers_desc")}</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LeaderList title={t("scout.top_scorers")} subtitle={t("scout.scorers_subtitle")} Icon={Flame} accent="#FF2A6D" leaders={leaders.scorers} onLoad={onLoad} />
        <LeaderList title={t("scout.top_architects")} subtitle={t("scout.architects_subtitle")} Icon={Sparkles} accent="#007AFF" leaders={leaders.architects} onLoad={onLoad} />
      </div>
    </div>
  );
}

function LeaderList({ title, subtitle, Icon, accent, leaders, onLoad }: {
  title: string; subtitle: string; Icon: React.ElementType;
  accent: string; leaders: Leader[]; onLoad: (n: string) => void;
}) {
  const { t } = useTranslation();
  return (
    <div className="bg-[#0A192F] border border-white/10 rounded-2xl overflow-hidden">
      <div className="bg-[#0A192F] px-6 py-4 flex items-center gap-3">
        <Icon size={16} style={{ color: accent }} />
        <div>
          <h3 className="text-white font-black text-[14px] uppercase tracking-wider" style={{ fontFamily: "var(--font-oswald)" }}>{title}</h3>
          <p className="text-slate-500 text-[10px] uppercase tracking-widest">{subtitle}</p>
        </div>
      </div>
      {leaders.length === 0 ? (
        <div className="py-12 text-center text-slate-300 text-[12px] font-bold uppercase tracking-widest">
          {t("scout.backend_offline")}
        </div>
      ) : (
        leaders.map((l, i) => (
          <div
            key={i}
            onClick={() => onLoad(l.name)}
            className="sc-leader-row flex items-center gap-4 px-6 py-4 border-b border-white/10 last:border-0 cursor-pointer transition-colors"
          >
            <div className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-black"
              style={{ background: i === 0 ? accent : "rgba(255,255,255,0.08)", color: i === 0 ? "#fff" : "#94A3B8" }}>
              {i + 1}
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-black text-[14px] uppercase text-white truncate" style={{ fontFamily: "var(--font-oswald)" }}>{l.name}</div>
              <div className="text-[10px] text-slate-400 uppercase tracking-wide font-medium">{l.team}</div>
            </div>
            <div className="text-right shrink-0">
              <div className="font-black text-[20px] leading-none" style={{ color: accent, fontFamily: "var(--font-oswald)" }}>
                {typeof l.value === "number" ? (l.value < 10 ? l.value.toFixed(2) : l.value) : l.value}
              </div>
              <div className="text-[9px] text-slate-400 uppercase tracking-wide">{l.stat}</div>
            </div>
            <ChevronRight size={14} className="text-slate-300 shrink-0" />
          </div>
        ))
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TARGET TAB
// ═══════════════════════════════════════════════════════════════════════════════
function TargetTab({ dna, radar, shots, hoveredShot, setHoveredShot, onLoad, loading }: {
  dna: PlayerDNA | null; radar: RadarData | null; shots: Shot[];
  hoveredShot: any; setHoveredShot: (s: any) => void; onLoad: (n: string) => void;
  loading?: boolean;
}) {
  const { t } = useTranslation();
  if (!dna) {
    if (loading) return <SkeletonTargetTab />;
    return <SearchHub onLoad={onLoad} context={t("scout.dna_title")} />;
  }

  const radarOpt = radar ? buildRadarOption(radar.axes, "#FF2A6D") : null;

  return (
    <div className="space-y-6">
      {/* HERO ROW */}
      <div className="bg-[#0A192F] rounded-2xl px-8 py-6 flex flex-wrap items-center gap-8 border-l-[6px] border-[#FF2A6D]">
        <div className="flex-1 min-w-0">
          <p className="text-[#FF2A6D] text-[10px] font-black uppercase tracking-[0.3em] mb-1">{dna.position}</p>
          <h2 className="text-white font-black text-5xl uppercase tracking-tighter leading-none truncate" style={{ fontFamily: "var(--font-oswald)" }}>
            {dna.name}
          </h2>
          <p className="text-slate-400 text-[12px] uppercase tracking-widest mt-1 font-bold">{dna.team}</p>
        </div>
        <div className="flex gap-8 shrink-0">
          {[
            { l: "AGE", v: dna.age && dna.age !== "N/D" ? dna.age : "—" },
            { l: t("scout.appearances"), v: dna.games },
            { l: t("common.minutes"), v: `${dna.minutes}'` },
            { l: t("common.goals"), v: Math.round(dna.totals.goals ?? 0) },
            { l: t("common.assists"), v: Math.round(dna.totals.assists ?? 0) },
          ].map(({ l, v }) => (
            <div key={l} className="text-center">
              <div className="text-white font-black text-2xl leading-none" style={{ fontFamily: "var(--font-oswald)" }}>{v}</div>
              <div className="text-slate-500 text-[9px] uppercase tracking-widest mt-1">{l}</div>
            </div>
          ))}
        </div>
        <div className="text-center border-l border-white/10 pl-8 shrink-0">
          <p className="text-[#FF2A6D] text-[10px] font-black uppercase tracking-[0.3em] mb-1">PIR</p>
          <div className="text-[#FF2A6D] font-black text-4xl leading-none" style={{ fontFamily: "var(--font-oswald)" }}>
            {dna.scores.PIR.toFixed(3)}
          </div>
          <p className="text-slate-500 text-[9px] uppercase tracking-widest mt-1">Impact Rating</p>
        </div>
      </div>

      {/* SCORE TILES */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        {SCORE_CFG.map(({ key, label, max, accent }) => {
          const val = (dna.scores as any)[key] ?? 0;
          const pct = Math.min(1, Math.max(0, val / max));
          const col = scoreColor(pct, accent);
          return (
            <motion.div
              key={key}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: SCORE_CFG.findIndex(s => s.key === key) * 0.05 }}
              className="bg-[#0A192F] border border-white/10 rounded-xl p-4 text-center"
            >
              <div className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-2">{key}</div>
              <div className="font-black text-xl leading-none mb-2" style={{ color: col, fontFamily: "var(--font-oswald)" }}>
                {val.toFixed(key === "AIR" || key === "BCS" ? 5 : key === "FES" ? 2 : 3)}
              </div>
              <div className="h-1 bg-white/10 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${pct * 100}%` }}
                  transition={{ duration: 0.8, delay: 0.3 }}
                  className="h-full rounded-full"
                  style={{ background: col }}
                />
              </div>
              <div className="text-[8px] text-slate-400 mt-2 leading-tight">{label}</div>
            </motion.div>
          );
        })}
      </div>

      {/* MAIN GRID: Shot map + radar + stats */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* SHOT MAP */}
        <div className="lg:col-span-7 bg-[#0A192F] border border-white/10 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Target size={15} className="text-[#FF2A6D]" />
              <h3 className="font-black text-[11px] uppercase tracking-[0.2em] text-white" style={{ fontFamily: "var(--font-oswald)" }}>
                {t("scout.shot_map_title")}
              </h3>
            </div>
            <div className="flex gap-4 text-[10px] font-bold text-slate-400">
              <span><span className="text-green-500">●</span> {t("common.goals")}</span>
              <span><span className="text-[#FF2A6D]">●</span> {t("scout.shot_missed")}</span>
              <span><span className="text-[#007AFF]">●</span> {t("scout.shot_saved")}</span>
              <span className="bg-white/10 px-2 py-0.5 rounded font-black text-slate-200">{shots.length} tiri</span>
            </div>
          </div>
          <PitchSVG shots={shots} hoveredShot={hoveredShot} setHoveredShot={setHoveredShot} />
        </div>

        {/* RIGHT COLUMN: radar + p90 stats */}
        <div className="lg:col-span-5 flex flex-col gap-5">

          {/* RADAR */}
          <div className="bg-[#0A192F] border border-white/10 rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-black text-[11px] uppercase tracking-[0.2em] text-white" style={{ fontFamily: "var(--font-oswald)" }}>
                {t("scout.radar_title")}
              </h3>
            </div>
            {radar ? (
              <>
                <p className="text-slate-400 text-[9px] uppercase tracking-widest mb-3">
                  {t("scout.radar_desc", { n: radar.pool_size })}
                </p>
                <ReactECharts option={radarOpt} style={{ height: 220 }} />
                <div className="mt-3 space-y-1.5">
                  {Object.entries(radar.axes).map(([k, ax]) => (
                    <div key={k} className="flex justify-between items-center">
                      <span className="text-[10px] text-slate-400 font-medium">{ax.label}</span>
                      <div className="flex items-center gap-3">
                        <span className="text-[10px] text-slate-500">{ax.value.toFixed(3)}</span>
                        <span className="text-[11px] font-black w-9 text-right" style={{ color: ax.percentile > 70 ? "#FF2A6D" : ax.percentile > 40 ? "#007AFF" : "#94A3B8" }}>
                          {ax.percentile}°
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="py-8 text-center text-slate-300 text-[11px] uppercase">{t("scout.radar_no_data")}</div>
            )}
          </div>

          {/* P90 TABLE */}
          <div className="bg-[#0A192F] border border-white/10 rounded-2xl p-6">
            <h3 className="font-black text-[11px] uppercase tracking-[0.2em] text-white mb-4" style={{ fontFamily: "var(--font-oswald)" }}>
              {t("scout.metrics_title")}
            </h3>
            <div className="space-y-2">
              {[
                { l: "xG / 90",       v: dna.p90.xg?.toFixed(3),        c: "#FF2A6D" },
                { l: "xA / 90",       v: dna.p90.xa?.toFixed(3),        c: "#007AFF" },
                { l: "Goals / 90",    v: dna.p90.goals?.toFixed(2),     c: "#10B981" },
                { l: "Shots / 90",    v: dna.p90.shots?.toFixed(2),     c: "#94A3B8" },
                { l: "Key Passes/90", v: dna.p90.key_passes?.toFixed(2),c: "#94A3B8" },
                { l: "xGChain / 90",  v: dna.p90.xgchain?.toFixed(3),   c: "#F59E0B" },
                { l: "xGBuildup/90",  v: dna.p90.xgbuildup?.toFixed(3), c: "#F59E0B" },
              ].map(({ l, v, c }) => (
                <div key={l} className="flex justify-between items-center py-1.5 border-b border-white/10 last:border-0">
                  <span className="text-[11px] text-slate-400 font-medium uppercase tracking-wide">{l}</span>
                  <span className="font-black text-[13px]" style={{ color: c, fontFamily: "var(--font-oswald)" }}>{v ?? "—"}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PITCH SVG — StatsBomb style
// ═══════════════════════════════════════════════════════════════════════════════

// Understat coords → SVG half-pitch (goal at top, viewBox "0 0 100 70")
// X: 0=own goal → 1=opponent goal | Y: 0=left → 1=right
// We show attack half: X from ~0.4 to 1.0
const toSvgCoords = (X: number, Y: number) => ({
  cx: Math.round(Y * 1000) / 10,
  cy: Math.max(-2, Math.min(74, Math.round((1 - X) / 0.6 * 70 * 10) / 10)),
});

// Result → color mapping (StatsBomb palette)
const resultStyle = (result: string): { fill: string; stroke: string; opacity: number } => {
  switch (result) {
    case "Goal":         return { fill: "#FFD700", stroke: "#FFD700", opacity: 1    };
    case "SavedShot":    return { fill: "#3B82F6", stroke: "#60A5FA", opacity: 0.75 };
    case "BlockedShot": return { fill: "#6366F1", stroke: "#818CF8", opacity: 0.70 };
    case "ShotOnPost":  return { fill: "#F59E0B", stroke: "#FCD34D", opacity: 0.85 };
    default:             return { fill: "#EF4444", stroke: "#F87171", opacity: 0.60 }; // MissedShots
  }
};

function PitchSVG({ shots, hoveredShot, setHoveredShot }: {
  shots: Shot[];
  hoveredShot: (Shot & { cx: number; cy: number }) | null;
  setHoveredShot: (s: any) => void;
}) {
  const goals    = shots.filter(s => s.result === "Goal");
  const nonGoals = shots.filter(s => s.result !== "Goal");
  const totalXG  = shots.reduce((acc, s) => acc + (s.xG || 0), 0);
  const avgXG    = shots.length ? totalXG / shots.length : 0;

  return (
    <div>
      {/* ── Stats summary bar ── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
        {[
          { l: "Gol",       v: goals.length,         c: "#FFD700" },
          { l: "xG Totale", v: totalXG.toFixed(2),   c: "#FF2A6D" },
          { l: "Tiri Tot.", v: shots.length,          c: "#E2E8F0" },
          { l: "xG/Tiro",  v: avgXG.toFixed(3),       c: "#94A3B8" },
        ].map(({ l, v, c }) => (
          <div key={l} className="bg-[#0A192F] rounded-lg px-3 py-2 text-center border border-white/5">
            <div className="font-black text-[18px] leading-none" style={{ color: c, fontFamily: "var(--font-oswald)" }}>{v}</div>
            <div className="text-[9px] text-slate-500 uppercase tracking-widest mt-1">{l}</div>
          </div>
        ))}
      </div>

      {/* ── Pitch ── */}
      <div className="relative rounded-xl overflow-hidden" style={{ background: "#163D25" }}>
        <svg
          viewBox="0 0 100 70"
          style={{ width: "100%", display: "block" }}
          preserveAspectRatio="xMidYMid meet"
        >
          <defs>
            {/* Pitch stripe texture */}
            <pattern id="stripes" width="100" height="10" patternUnits="userSpaceOnUse">
              <rect width="100" height="5" fill="rgba(255,255,255,0.018)" />
            </pattern>
            {/* Goal glow filter */}
            <filter id="goal-glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="1.8" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            {/* Soft glow for high-xG non-goals */}
            <filter id="soft-glow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="0.8" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            {/* Danger zone gradient */}
            <radialGradient id="danger" cx="50%" cy="5%" r="45%">
              <stop offset="0%"   stopColor="#FF2A6D" stopOpacity="0.18" />
              <stop offset="100%" stopColor="#FF2A6D" stopOpacity="0"   />
            </radialGradient>
          </defs>

          {/* Pitch green base */}
          <rect x="0" y="0" width="100" height="70" fill="#163D25" />
          {/* Alternating stripes */}
          <rect x="0" y="0" width="100" height="70" fill="url(#stripes)" />

          {/* ── Pitch markings ── */}
          {/* Penalty area: 40.32m wide × 16.5m deep → SVG x:20.4–79.6, y:0–19.2 */}
          <g stroke="rgba(255,255,255,0.45)" strokeWidth="0.45" fill="none">
            {/* Outer border */}
            <rect x="2" y="0" width="96" height="70" />
            {/* Bottom line (center) */}
            <line x1="2" y1="70" x2="98" y2="70" strokeWidth="0.6" stroke="rgba(255,255,255,0.5)" />
            {/* Penalty area */}
            <rect x="20.4" y="0" width="59.2" height="19.2" />
            {/* 6-yard box: 18.32m wide × 5.5m deep → x:36.5–63.5, y:0–6.4 */}
            <rect x="36.5" y="0" width="27" height="6.4" />
            {/* Goal: 7.32m wide → x:44.6–55.4 */}
            <rect x="44.6" y="0" width="10.8" height="2.8"
              stroke="rgba(255,255,255,0.8)" strokeWidth="0.7" />
            {/* Penalty spot: 11m deep → y=12.8 */}
            <circle cx="50" cy="12.8" r="0.7" fill="rgba(255,255,255,0.6)" stroke="none" />
            {/* Penalty arc */}
            <path d="M 33 19.2 A 11 10.5 0 0 1 67 19.2" />
          </g>

          {/* Danger zone overlay */}
          <rect x="20.4" y="0" width="59.2" height="19.2" fill="url(#danger)" />

          {/* ── Non-goal shots (rendered first, below goals) ── */}
          {nonGoals.map((s, i) => {
            const { cx, cy } = toSvgCoords(s.X, s.Y);
            const { fill, stroke, opacity } = resultStyle(s.result);
            // piccoli e in scala contenuta — xG da 0 a 1 → r da 1.0 a 2.5
            const r = 1.0 + s.xG * 1.5;
            return (
              <circle
                key={`ng-${i}`}
                cx={cx} cy={cy} r={r}
                fill={fill}
                fillOpacity={opacity}
                stroke={stroke}
                strokeWidth={0.4}
                strokeOpacity={0.9}
                style={{ cursor: "pointer" }}
                onMouseEnter={() => setHoveredShot({ ...s, cx, cy })}
                onMouseLeave={() => setHoveredShot(null)}
              />
            );
          })}

          {/* ── Goals — pallone da calcio ⚽ ── */}
          {goals.map((s, i) => {
            const { cx, cy } = toSvgCoords(s.X, s.Y);
            return (
              <text
                key={`g-${i}`}
                x={cx} y={cy}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize="5"
                style={{ cursor: "pointer", userSelect: "none" }}
                filter="url(#goal-glow)"
                onMouseEnter={() => setHoveredShot({ ...s, cx, cy })}
                onMouseLeave={() => setHoveredShot(null)}
              >
                ⚽
              </text>
            );
          })}

          {shots.length === 0 && (
            <text x="50" y="38" textAnchor="middle" fontSize="3.2"
              fill="rgba(255,255,255,0.25)" fontFamily="Inter" letterSpacing="0.5">
              SHOT MAP NON DISPONIBILE
            </text>
          )}
        </svg>

        {/* ── Hover tooltip ── */}
        <AnimatePresence>
          {hoveredShot && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="absolute top-3 right-3 rounded-xl p-4 min-w-[210px] pointer-events-none z-20"
              style={{
                background: "rgba(7,13,26,0.97)",
                border: "1px solid rgba(255,255,255,0.1)",
                borderLeft: `3px solid ${hoveredShot.result === "Goal" ? "#FFD700" : "#FF2A6D"}`,
                backdropFilter: "blur(8px)",
              }}
            >
              <div className="flex items-center gap-2 mb-3 pb-2 border-b border-white/10">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ background: resultStyle(hoveredShot.result).fill }}
                />
                <span className="font-black text-[15px] uppercase" style={{
                  color: hoveredShot.result === "Goal" ? "#FFD700" : "#E2E8F0",
                  fontFamily: "var(--font-oswald)",
                }}>
                  {hoveredShot.result === "Goal" ? "⚽ GOAL!" : hoveredShot.result}
                </span>
              </div>
              {[
                { l: "xG",      v: hoveredShot.xG?.toFixed(3),        bold: true  },
                { l: "Minuto",  v: `${hoveredShot.minute}'`,          bold: false },
                { l: "Azione",  v: hoveredShot.situation,             bold: false },
                { l: "Tipo",    v: hoveredShot.shotType || "—",       bold: false },
              ].map(({ l, v, bold }) => (
                <div key={l} className="flex justify-between items-center mb-1.5">
                  <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wide">{l}</span>
                  <span className="text-[11px] font-black" style={{
                    color: l === "xG" ? "#FF2A6D" : "#E2E8F0",
                    fontFamily: bold ? "var(--font-oswald)" : "inherit",
                    fontSize: l === "xG" ? 15 : 11,
                  }}>{v}</span>
                </div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── Legend ── */}
      <div className="flex items-center gap-5 mt-3 flex-wrap">
        {[
          { color: "#FFD700", label: `Gol (${goals.length})`,        ring: true  },
          { color: "#3B82F6", label: "Parato",                       ring: false },
          { color: "#6366F1", label: "Bloccato",                     ring: false },
          { color: "#F59E0B", label: "Palo",                         ring: false },
          { color: "#EF4444", label: "Fuori",                        ring: false },
        ].map(({ color, label, ring }) => (
          <div key={label} className="flex items-center gap-1.5">
            <div className="relative w-4 h-4 flex items-center justify-center">
              {ring && (
                <div className="absolute inset-0 rounded-full border border-current opacity-50"
                  style={{ color, borderColor: color }} />
              )}
              <div className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
            </div>
            <span className="text-[10px] text-slate-400 font-bold uppercase">{label}</span>
          </div>
        ))}
        <span className="text-[10px] text-slate-500 ml-auto">● dimensione = xG</span>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// REPLACE TAB (CON IMPAGINAZIONE 10 PER PAGINA)
// ═══════════════════════════════════════════════════════════════════════════════
function ReplaceTab({ data, onLoad }: { data: ReplacementData | null; onLoad: (n: string) => void }) {
  const { t } = useTranslation();
  const [page, setPage] = useState(1);

  // Resetta la pagina a 1 ogni volta che cerchi un nuovo giocatore
  useEffect(() => {
    setPage(1);
  }, [data?.target?.name]);

  if (!data || !data.target) {
    return <SearchHub onLoad={onLoad} context={t("scout.pse_title")} />;
  }

  const { target, substitutes } = data;
  
  // Logica di impaginazione
  const itemsPerPage = 10;
  const totalPages = Math.ceil(substitutes.length / itemsPerPage);
  const startIndex = (page - 1) * itemsPerPage;
  const currentSubs = substitutes.slice(startIndex, startIndex + itemsPerPage);

  return (
    <div>
      {/* Target bar */}
      <div className="bg-[#0A192F] border-l-[6px] border-[#FF2A6D] rounded-2xl px-8 py-5 mb-8 flex flex-wrap justify-between items-center gap-6">
        <div>
          <p className="text-[#FF2A6D] text-[10px] font-black uppercase tracking-[0.3em] mb-1">{t("scout.pse_algorithm")}</p>
          <h2 className="text-white font-black text-4xl uppercase tracking-tighter" style={{ fontFamily: "var(--font-oswald)" }}>
            {target.name}
          </h2>
          <p className="text-slate-400 text-[11px] uppercase mt-1">{target.team} · {target.position} · PIR {target.scores.PIR.toFixed(4)}</p>
        </div>
        <div className="flex gap-8 text-center">
          {[
            { l: "Algoritmo",   v: t("scout.algo_euclidean"), c: "#FF2A6D" },
            { l: "Vettore",     v: t("scout.algo_metrics"),   c: "#007AFF" },
            { l: "Pool",        v: t("scout.algo_scope"),     c: "#10B981" },
          ].map(({ l, v, c }) => (
            <div key={l}>
              <div className="font-black text-[16px]" style={{ color: c, fontFamily: "var(--font-oswald)" }}>{v}</div>
              <div className="text-slate-500 text-[9px] uppercase tracking-widest">{l}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Clone cards (Solo quelli della pagina corrente) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5">
        {currentSubs.map((s, i) => {
          const globalRank = startIndex + i + 1; // Calcola il rank globale corretto
          return (
            <motion.div
              key={s.name}
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
              onClick={() => onLoad(s.name)}
              className="sc-card-hover bg-[#0A192F] border border-white/10 rounded-2xl p-5 cursor-pointer transition-all flex flex-col"
            >
              {/* Rank + similarity */}
              <div className="flex justify-between items-start mb-4">
                <span className="text-[10px] text-slate-400 font-black">#{globalRank}</span>
                <div className="bg-[#FF2A6D]/10 border border-[#FF2A6D]/30 rounded-lg px-2.5 py-1.5 text-center">
                  <div className="font-black text-[18px] leading-none text-[#FF2A6D]" style={{ fontFamily: "var(--font-oswald)" }}>
                    {s.similarity_pct.toFixed(1)}%
                  </div>
                  <div className="text-[8px] text-slate-400 uppercase font-bold mt-0.5">Match</div>
                </div>
              </div>

              <h4 className="font-black text-[18px] uppercase tracking-tight text-white mb-1 leading-none" style={{ fontFamily: "var(--font-oswald)" }}>
                {s.name}
              </h4>
              <p className="text-[10px] text-slate-400 uppercase font-bold mb-4">{s.team} · {s.position}</p>

              {/* Metric bars vs target */}
              <div className="flex-1">
                {[
                  { k: "xg", l: "xG/90", c: "#FF2A6D", max: 0.5 },
                  { k: "xa", l: "xA/90", c: "#007AFF", max: 0.4 },
                  { k: "xgchain", l: "xGChain", c: "#F59E0B", max: 0.8 },
                ].map(({ k, l, c, max }) => {
                  const sv = s.p90[k] ?? 0;
                  return (
                    <div key={k} className="mb-3">
                      <div className="flex justify-between mb-1">
                        <span className="text-[9px] text-slate-400 uppercase font-bold">{l}</span>
                        <span className="text-[10px] font-black" style={{ color: c, fontFamily: "var(--font-oswald)" }}>{sv.toFixed(3)}</span>
                      </div>
                      <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                        <div className="h-full rounded-full transition-all" style={{ width: `${Math.min(100, sv / max * 100)}%`, background: c }} />
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="flex justify-between items-center pt-3 border-t border-white/10 mt-2">
                <span className="text-[9px] text-slate-400 uppercase font-bold">PIR</span>
                <span className="font-black text-[13px]" style={{ color: "#FF2A6D", fontFamily: "var(--font-oswald)" }}>
                  {s.scores.PIR.toFixed(4)}
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Controlli Impaginazione */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center gap-6 mt-10">
          <button
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
            className="px-4 py-2 bg-[#0A192F] border border-white/10 rounded-lg text-[11px] font-bold text-white uppercase tracking-widest disabled:opacity-30 hover:border-[#FF2A6D] transition-colors"
          >
            {t("scout.page_prev")}
          </button>
          <span className="text-[11px] font-mono text-slate-400">
            {t("scout.page_of", { page, total: totalPages })}
          </span>
          <button
            disabled={page === totalPages}
            onClick={() => setPage(p => p + 1)}
            className="px-4 py-2 bg-[#0A192F] border border-white/10 rounded-lg text-[11px] font-bold text-white uppercase tracking-widest disabled:opacity-30 hover:border-[#FF2A6D] transition-colors"
          >
            {t("scout.page_next")}
          </button>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// H2H TAB
// ═══════════════════════════════════════════════════════════════════════════════
function H2HTab({ p1, p2, r1, r2, onClear1, onClear2 }: {
  p1: PlayerDNA | null; p2: PlayerDNA | null;
  r1: RadarData | null; r2: RadarData | null;
  onClear1: () => void; onClear2: () => void;
}) {
  const { t } = useTranslation();
  const h2hOpt = buildH2HRadar(r1, r2, p1?.name, p2?.name);

  return (
    <div className="space-y-6">
      {(!p1 && !p2) && (
        <EmptyState
          Icon={Scale}
          title={t("scout.h2h_title")}
          desc={t("scout.h2h_desc")}
        />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <H2HSlot player={p1} radar={r1} color="#FF2A6D" label="CHALLENGER 1" onClear={onClear1} />
        <H2HSlot player={p2} radar={r2} color="#007AFF" label="CHALLENGER 2" onClear={onClear2} />
      </div>

      {h2hOpt && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-[#0A192F] border border-white/10 rounded-2xl p-6">
          <h3 className="font-black text-[11px] uppercase tracking-[0.2em] text-white mb-1" style={{ fontFamily: "var(--font-oswald)" }}>
            {t("scout.h2h_radar_title")}
          </h3>
          <p className="text-[9px] text-slate-400 uppercase tracking-widest mb-4">
            Confronto su xG · Goals · xA · xGChain · Shots per 90' rispetto al ruolo
          </p>
          <ReactECharts option={h2hOpt} style={{ height: "min(440px, 70vw)" }} />
        </motion.div>
      )}
    </div>
  );
}

function H2HSlot({ player, color, label, onClear }: {
  player: PlayerDNA | null; radar?: RadarData | null;
  color: string; label: string; onClear: () => void;
}) {
  const { t } = useTranslation();
  return (
    <div
      className="bg-[#0A192F] border rounded-2xl overflow-hidden"
      style={{ borderRightColor: player ? color + "50" : "rgba(255,255,255,0.1)", borderBottomColor: player ? color + "50" : "rgba(255,255,255,0.1)", borderLeftColor: player ? color + "50" : "rgba(255,255,255,0.1)", borderTopWidth: 4, borderTopStyle: "solid", borderTopColor: color }}
    >
      <div className="px-6 py-4 flex justify-between items-center border-b border-white/10">
        <span className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400">{label}</span>
        {player && (
          <button onClick={onClear} className="flex items-center gap-1 text-[10px] text-slate-400 hover:text-red-500 transition-colors font-bold uppercase">
            <X size={12} /> {t("scout.remove")}
          </button>
        )}
      </div>

      {player ? (
        <div className="p-6">
          <div className="font-black text-3xl uppercase tracking-tighter mb-1" style={{ color, fontFamily: "var(--font-oswald)" }}>
            {player.name}
          </div>
          <div className="text-[11px] text-slate-400 uppercase font-bold mb-6">{player.team} · {player.position}</div>
          <div className="grid grid-cols-2 gap-3">
            {[
              { l: "PIR",    v: player.scores.PIR.toFixed(4)   },
              { l: "OIS",    v: player.scores.OIS.toFixed(4)   },
              { l: "xG/90", v: player.p90.xg?.toFixed(3)      },
              { l: "xA/90", v: player.p90.xa?.toFixed(3)      },
              { l: "FES",    v: player.scores.FES.toFixed(3)   },
              { l: "CII",    v: player.scores.CII.toFixed(4)   },
            ].map(({ l, v }) => (
              <div key={l} className="bg-white/5 rounded-xl p-3 flex justify-between items-center">
                <span className="text-[9px] text-slate-400 uppercase font-bold">{l}</span>
                <span className="font-black text-[14px]" style={{ color, fontFamily: "var(--font-oswald)" }}>{v}</span>
              </div>
            ))}
          </div>
          <div className="grid grid-cols-3 gap-3 mt-3 border-t border-white/10 pt-3">
            {[
              { l: t("scout.appearances"), v: player.games },
              { l: t("common.minutes"),    v: player.minutes },
              { l: t("common.position"),   v: player.position },
            ].map(({ l, v }) => (
              <div key={l} className="text-center">
                <div className="font-black text-[16px]" style={{ fontFamily: "var(--font-oswald)" }}>{v}</div>
                <div className="text-[9px] text-slate-400 uppercase tracking-wide">{l}</div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="p-10 flex flex-col items-center justify-center text-slate-300 min-h-[280px]">
          <Users size={36} className="mb-3" style={{ color: color + "30" }} />
          <span className="text-[12px] font-black uppercase tracking-widest text-slate-300">{t("scout.waiting")}</span>
          <span className="text-[10px] text-slate-400 mt-1">{t("scout.search_hint")}</span>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// DISCOVER TAB
// ═══════════════════════════════════════════════════════════════════════════════
const POS_BTNS: { id: string; key: string }[] = [
  { id: "ALL", key: "scout.pos_all" },
  { id: "FW",  key: "scout.pos_forward" },
  { id: "AMC", key: "scout.pos_trequarti" },
  { id: "MC",  key: "scout.pos_mid" },
  { id: "DC",  key: "scout.pos_def" },
];

function DiscoverTab({ talents, loading, pos, onPos, onLoad }: {
  talents: PlayerDNA[]; loading: boolean;
  pos: string; onPos: (p: string) => void; onLoad: (n: string) => void;
}) {
  const { t } = useTranslation();
  return (
    <div suppressHydrationWarning>
      <div className="flex flex-wrap items-end justify-between gap-4 mb-8">
        <div>
          <h2 className="text-3xl font-black uppercase tracking-tighter text-[#0A192F]" style={{ fontFamily: "var(--font-oswald)" }}>
            Talent<span className="text-[#FF2A6D]">Radar</span>
          </h2>
          <p className="text-slate-400 text-[10px] uppercase tracking-[0.2em] mt-1">{t("scout.talent_radar_desc")}</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          {POS_BTNS.map(f => (
            <button
              key={f.id}
              onClick={() => onPos(f.id)}
              className="text-[11px] font-black uppercase tracking-wide px-4 py-2 rounded-lg transition-all border"
              style={{
                background: pos === f.id ? "#FF2A6D" : "#fff",
                color: pos === f.id ? "#fff" : "#64748B",
                borderColor: pos === f.id ? "#FF2A6D" : "#E2E8F0",
                fontFamily: "var(--font-oswald)",
              }}
            >
              {t(f.key)}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-5 animate-pulse">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="bg-[#0A192F] border border-white/10 rounded-2xl h-56" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-5">
          {talents.map((t, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              onClick={() => onLoad(t.name)}
              className="sc-talent-card bg-[#0A192F] border border-white/10 rounded-2xl p-5 cursor-pointer transition-all relative overflow-hidden"
            >
              {/* Rank badge */}
              <div className="absolute top-4 right-4 w-7 h-7 rounded-full bg-white/10 flex items-center justify-center">
                <span className="text-[10px] font-black text-slate-400">#{i + 1}</span>
              </div>

              {/* PPI highlight */}
              <div className="mb-4">
                <div className="text-[9px] text-slate-400 uppercase tracking-widest mb-1">PPI Score</div>
                <div className="font-black text-[26px] leading-none text-[#FF2A6D]" style={{ fontFamily: "var(--font-oswald)" }}>
                  {t.scores.PPI.toFixed(3)}
                </div>
              </div>

              <h4 className="font-black text-[17px] uppercase tracking-tight text-white leading-tight mb-1" style={{ fontFamily: "var(--font-oswald)" }}>
                {t.name}
              </h4>
              <p className="text-[9px] text-slate-400 uppercase font-bold mb-4">{t.team} · {t.position}</p>

              {/* Mini stats */}
              <div className="grid grid-cols-3 gap-1.5">
                {[
                  { l: "xG/90", v: t.p90.xg?.toFixed(3), c: "#FF2A6D" },
                  { l: "xA/90", v: t.p90.xa?.toFixed(3), c: "#007AFF" },
                  { l: "OIS",   v: t.scores.OIS.toFixed(3), c: "#10B981" },
                ].map(({ l, v, c }) => (
                  <div key={l} className="bg-white/5 rounded-lg p-2 text-center">
                    <div className="font-black text-[12px] leading-none" style={{ color: c, fontFamily: "var(--font-oswald)" }}>{v}</div>
                    <div className="text-[8px] text-slate-400 uppercase mt-0.5">{l}</div>
                  </div>
                ))}
              </div>

              <div className="mt-3 pt-3 border-t border-white/10 flex justify-between items-center">
                <span className="text-[9px] text-slate-400 uppercase font-bold">{Math.round(t.minutes)} min</span>
                <span className="text-[9px] font-black text-white" style={{ fontFamily: "var(--font-oswald)" }}>
                  {t.games} partite
                </span>
              </div>
            </motion.div>
          ))}

          {talents.length === 0 && !loading && (
            <div className="col-span-4 text-center py-16 text-slate-300 font-black uppercase text-[13px] tracking-widest" style={{ fontFamily: "var(--font-oswald)" }}>
              {t("scout.no_talent")}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// ECHARTS HELPERS
// ═══════════════════════════════════════════════════════════════════════════════
function buildRadarOption(axes: Record<string, AxisData>, color: string) {
  const labels = Object.values(axes).map(a => a.label);
  const vals   = Object.values(axes).map(a => a.percentile);
  return {
    backgroundColor: "transparent",
    radar: {
      indicator: labels.map(l => ({ name: l, max: 100 })),
      shape: "polygon", splitNumber: 4,
      axisName: { color: "#94A3B8", fontSize: 9, fontFamily: "Inter" },
      splitLine: { lineStyle: { color: "rgba(255,255,255,0.08)" } },
      splitArea: { areaStyle: { color: ["rgba(255,255,255,0.03)", "transparent"] } },
      axisLine:  { lineStyle: { color: "rgba(255,255,255,0.08)" } },
    },
    series: [{
      type: "radar",
      data: [{ value: vals, name: "Percentile",
        areaStyle:  { color: color + "22" },
        lineStyle:  { color, width: 2 },
        itemStyle:  { color },
      }],
    }],
  };
}

function buildH2HRadar(r1: RadarData | null, r2: RadarData | null, n1?: string, n2?: string) {
  if (!r1 && !r2) return null;
  const axes   = r1 ? r1.axes : r2!.axes;
  const labels = Object.values(axes).map(a => a.label);
  const v1 = r1 ? Object.values(r1.axes).map(a => a.percentile) : null;
  const v2 = r2 ? Object.values(r2.axes).map(a => a.percentile) : null;

  const datasets: any[] = [];
  if (v1) datasets.push({ value: v1, name: n1 || "P1", areaStyle: { color: "rgba(255,42,109,0.15)" }, lineStyle: { color: "#FF2A6D", width: 2.5 }, itemStyle: { color: "#FF2A6D" } });
  if (v2) datasets.push({ value: v2, name: n2 || "P2", areaStyle: { color: "rgba(0,122,255,0.15)" }, lineStyle: { color: "#007AFF", width: 2.5 }, itemStyle: { color: "#007AFF" } });

  return {
    backgroundColor: "transparent",
    legend: { data: [n1, n2].filter(Boolean), textStyle: { color: "#64748B", fontFamily: "Inter", fontSize: 11 }, bottom: 0 },
    radar: {
      indicator: labels.map(l => ({ name: l, max: 100 })),
      shape: "polygon", splitNumber: 5, radius: "65%",
      axisName: { color: "#94A3B8", fontSize: 11, fontFamily: "Inter" },
      splitLine: { lineStyle: { color: "rgba(255,255,255,0.09)" } },
      splitArea: { areaStyle: { color: ["rgba(255,255,255,0.03)", "transparent", "rgba(255,255,255,0.03)", "transparent", "rgba(255,255,255,0.03)"] } },
      axisLine:  { lineStyle: { color: "rgba(255,255,255,0.08)" } },
    },
    series: [{ type: "radar", data: datasets }],
  };
}

// ═══════════════════════════════════════════════════════════════════════════════
// EMPTY STATE
// ═══════════════════════════════════════════════════════════════════════════════
function EmptyState({ Icon, title, desc }: { Icon: any, title: string, desc: string }) {
  return (
    <div className="flex flex-col items-center justify-center w-full py-32 bg-transparent">
      {/* Icon Container: cerchio elegante scuro, niente bordi aggressivi o tratteggi */}
      <div className="flex items-center justify-center w-24 h-24 mb-6 rounded-full bg-slate-800/50 shadow-inner border border-slate-700/50">
        <Icon className="w-10 h-10 text-pink-500" strokeWidth={1.5} />
      </div>
      
      {/* Title: chiaro, leggibile, autorevole */}
      <h3 className="text-2xl font-extrabold text-slate-100 mb-3 tracking-tight">
        {title}
      </h3>
      
      {/* Description: grigio neutro per non affaticare la vista */}
      <p className="text-slate-400 max-w-lg text-center text-sm leading-relaxed">
        {desc}
      </p>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SEARCH HUB — entry point when no player is selected
// ═══════════════════════════════════════════════════════════════════════════════
function SearchHub({ onLoad, context }: { onLoad: (n: string) => void; context?: string }) {
  const { t } = useTranslation();
  const [q, setQ] = useState("");
  const [sugg, setSugg] = useState<Suggestion[]>([]);
  const [showSugg, setShowSugg] = useState(false);
  const [searching, setSearching] = useState(false);
  const debounce = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (debounce.current) clearTimeout(debounce.current);
    if (q.length < 2) { setSugg([]); setShowSugg(false); return; }
    debounce.current = setTimeout(async () => {
      setSearching(true);
      try {
        const r = await fetch(`${API}/api/scout/search?q=${encodeURIComponent(q)}`);
        const d = await r.json();
        const results: Suggestion[] = (d.results || []).map((x: any) => ({
          name: typeof x === "string" ? x : x.name ?? String(x),
          team: typeof x === "string" ? "" : x.team ?? "",
        }));
        setSugg(results); setShowSugg(results.length > 0);
      } catch { /* silent */ } finally { setSearching(false); }
    }, 300);
  }, [q]);

  const handleSelect = (name: string) => {
    setQ(""); setSugg([]); setShowSugg(false); onLoad(name);
  };

  return (
    <div className="flex flex-col items-center justify-center py-14 px-4">
      {/* Branding */}
      <div className="mb-10 text-center">
        <p className="text-[#FF2A6D] text-[10px] font-black uppercase tracking-[0.4em] mb-3">
          {context || "Intelligence Platform · Season 25/26"}
        </p>
        <h2 className="font-black text-5xl md:text-6xl uppercase tracking-tighter text-[#0A192F] leading-none mb-3"
          style={{ fontFamily: "var(--font-oswald)" }}>
          {t("scout.analyze_player")}
        </h2>
        <p className="text-slate-400 text-[13px]">Top 5 leghe europee · Stagione 25/26 · Min. 500'</p>
      </div>

      {/* Search bar */}
      <div className="relative w-full max-w-2xl">
        <div className="flex items-center bg-white border-2 border-slate-200 rounded-2xl px-5 py-4 gap-3
                        shadow-lg focus-within:border-[#FF2A6D] focus-within:shadow-[0_8px_40px_rgba(255,42,109,0.10)] transition-all duration-200">
          <Search size={20} className="text-slate-400 shrink-0" />
          <input
            ref={inputRef}
            value={q}
            onChange={e => setQ(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && sugg.length) handleSelect(sugg[0].name); }}
            placeholder={t("scout.search_name_placeholder")}
            className="flex-1 bg-transparent outline-none text-[#0A192F] text-[15px] font-bold placeholder:text-slate-400 placeholder:font-normal"
            style={{ fontFamily: "var(--font-oswald)" }}
            autoFocus
          />
          {searching && <Activity size={15} className="text-[#FF2A6D] sc-spin shrink-0" />}
          {q && !searching && (
            <button onClick={() => { setQ(""); setSugg([]); setShowSugg(false); }}
              className="text-slate-400 hover:text-slate-600 transition-colors shrink-0">
              <X size={15} />
            </button>
          )}
        </div>

        <AnimatePresence>
          {showSugg && (
            <motion.div
              initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              className="absolute top-full left-0 right-0 bg-white border border-slate-200 rounded-2xl shadow-2xl overflow-hidden z-50 max-h-72 overflow-y-auto mt-2"
            >
              {sugg.map((s, i) => (
                <div key={i} onClick={() => handleSelect(s.name)}
                  className="sc-sugg flex justify-between items-center px-5 py-3.5 cursor-pointer border-b border-slate-100 last:border-0">
                  <div className="flex items-center gap-3">
                    <div className="w-1.5 h-1.5 rounded-full bg-[#FF2A6D] shrink-0" />
                    <span className="font-black text-[13px] uppercase text-[#0A192F]"
                      style={{ fontFamily: "var(--font-oswald)" }}>{s.name}</span>
                  </div>
                  {s.team && <span className="text-[10px] text-slate-400 font-medium shrink-0 ml-3">{s.team}</span>}
                </div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Serie A suggestion pills */}
      <div className="mt-10 max-w-2xl w-full">
        <p className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-400 mb-4 text-center">
          {t("scout.serie_a_stars")}
        </p>
        <div className="flex flex-wrap gap-2 justify-center">
          {SERIE_A_PILLS.map(s => (
            <button key={s.name} onClick={() => handleSelect(s.name)}
              className="group inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-slate-200 shadow-sm
                          hover:border-[#FF2A6D] hover:shadow-[0_4px_20px_rgba(255,42,109,0.12)] hover:-translate-y-0.5
                          transition-all duration-200 cursor-pointer">
              <span className="text-[#0A192F] text-[12px] font-black uppercase group-hover:text-[#FF2A6D] transition-colors"
                style={{ fontFamily: "var(--font-oswald)" }}>{s.name}</span>
              <span className="text-slate-400 text-[9px] font-medium">{s.team}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function SkeletonTargetTab() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Hero — same dark navy as real player card */}
      <div className="bg-[#0A192F] border border-white/10 rounded-2xl h-32 border-l-[6px] border-l-[#FF2A6D]/30" />
      {/* 8 metric tiles */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="bg-[#0A192F] border border-white/10 rounded-xl h-24" />
        ))}
      </div>
      {/* Shot map + sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 bg-[#0A192F] border border-white/10 rounded-2xl h-[400px]" />
        <div className="lg:col-span-5 flex flex-col gap-5">
          <div className="bg-[#0A192F] border border-white/10 rounded-2xl h-56" />
          <div className="bg-[#0A192F] border border-white/10 rounded-2xl flex-1 min-h-[180px]" />
        </div>
      </div>
    </div>
  );
}