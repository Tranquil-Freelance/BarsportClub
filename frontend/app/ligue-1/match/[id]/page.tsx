"use client";

import React, { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Target, Activity, BarChart3, Crosshair } from "lucide-react";
import { useTranslation } from "react-i18next";
import "../../../i18n/config";

// Percorso corretto: esce da [id], esce da match, esce da serie-a, entra in components
import MatchLineups from "../../../components/MatchLineups";
import { API_BASE } from "@/app/lib/apiClient";

// ─── INTERFACCE TYPESCRIPT RIGOROSE ─────────────────────────────────

interface MatchStats {
  home_shots: number;
  away_shots: number;
  home_sot: number;
  away_sot: number;
  home_deep: number;
  away_deep: number;
  home_ppda: number;
  away_ppda: number;
  home_xpts: number;
  away_xpts: number;
}

interface MatchData {
  id: number;
  home_team: string;
  away_team: string;
  home_xG: number;
  away_xG: number;
  home_score: number;
  away_score: number;
  stats?: MatchStats;
}

interface ShotData {
  minute: number;
  player: string;
  result: string;
  team: string;
  xG: number;
  X: number;
  Y: number;
  situation?: string;
  shotType?: string;
  lastAction?: string;
}

interface ApiResponse {
  match: MatchData;
  shots: ShotData[];
}

interface StepData {
  min: number;
  xg: number;
}

interface ChartHoverState {
  min: number;
  xgH: number;
  xgA: number;
}

interface StatBarProps {
  label: string;
  home?: number;
  away?: number;
  isFloat?: boolean;
  index?: number;
}

// ─── COMPONENTE PRINCIPALE ──────────────────────────────────────────

export default function MatchDetailsPage() {
  const { t } = useTranslation();
  const params = useParams();
  const router = useRouter();
  const matchId = params.id as string;
  
  const [data, setData] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [hoveredShot, setHoveredShot] = useState<ShotData | null>(null);
  const [chartHover, setChartHover] = useState<ChartHoverState | null>(null);
  const chartRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!matchId) return;
    
    fetch(`${API_BASE}/api/matches/${matchId}/details`)
      .then(res => res.json())
      .then((json: ApiResponse) => { 
        setData(json); 
        setLoading(false); 
      })
      .catch((err) => {
        console.error("Errore nel fetch dei dettagli partita:", err);
        setLoading(false);
      });
  }, [matchId]);

  if (loading) return (
    <div suppressHydrationWarning className="min-h-screen bg-[#0A192F] flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-8 h-8 border-2 border-[#FF2A6D] border-t-transparent rounded-full animate-spin" />
        <span className="text-[10px] font-black uppercase tracking-[0.5em] text-slate-500">{t("match.analyzing")}</span>
      </div>
    </div>
  );

  if (!data || !data.match) return (
    <div suppressHydrationWarning className="min-h-screen bg-[#0A192F] flex items-center justify-center font-black text-slate-600 tracking-widest text-sm">
      {t("match.not_found")}
    </div>
  );

  const { match, shots } = data;

  const uniqueShots = shots.filter((s: ShotData, index: number, self: ShotData[]) =>
    index === self.findIndex((t: ShotData) => (
      t.minute === s.minute && t.player === s.player && t.result === s.result && t.team === s.team
    ))
  );

  const homeShots = uniqueShots.filter((s: ShotData) => s.team === 'h' || s.team === 'home').sort((a: ShotData, b: ShotData) => a.minute - b.minute);
  const awayShots = uniqueShots.filter((s: ShotData) => s.team === 'a' || s.team === 'away').sort((a: ShotData, b: ShotData) => a.minute - b.minute);

  const maxRawXG = Math.max(match.home_xG, match.away_xG, 1.0);
  const maxVisualXG = Math.ceil(maxRawXG * 2) / 2;

  const getCumulativeData = (teamShots: ShotData[]): StepData[] => {
    let current = 0;
    const points: StepData[] = [{ min: 0, xg: 0 }];
    teamShots.forEach(s => { 
      current += s.xG; 
      points.push({ min: s.minute, xg: current }); 
    });
    return points;
  };

  const homeSteps = getCumulativeData(homeShots);
  const awaySteps = getCumulativeData(awayShots);

  const CHART_W = 1000;
  const CHART_H = 300;

  const generateStepPath = (steps: StepData[]): string => {
    if (steps.length === 0) return `M 0 ${CHART_H} L ${CHART_W} ${CHART_H}`;
    let d = `M 0 ${CHART_H}`;
    let lastY = CHART_H;
    for (let i = 0; i < steps.length; i++) {
      const s = steps[i];
      const x = (s.min / 95) * CHART_W;
      const newY = CHART_H - (s.xg / maxVisualXG) * CHART_H;
      d += ` L ${x} ${lastY} L ${x} ${newY}`;
      lastY = newY;
    }
    d += ` L ${CHART_W} ${lastY}`;
    return d;
  };

  const handleChartMouseMove = (e: React.MouseEvent<SVGSVGElement, MouseEvent>) => {
    if (!chartRef.current) return;
    const rect = chartRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const minute = Math.max(0, Math.min(95, Math.round((x / rect.width) * 95)));
    
    const findXG = (steps: StepData[]) => {
      const step = [...steps].reverse().find(s => s.min <= minute);
      return step ? step.xg : 0;
    };
    
    setChartHover({ min: minute, xgH: findXG(homeSteps), xgA: findXG(awaySteps) });
  };

  const yAxisTicks: number[] = [];
  for (let i = 0; i <= maxVisualXG; i += 0.5) yAxisTicks.push(i);

  const shotToSvg = (s: ShotData) => {
    const isHome = s.team === 'h' || s.team === 'home';
    const cx = isHome ? (1 - s.X) * 100 : s.X * 100;
    const cy = s.Y * 68;
    return { cx, cy, isHome };
  };

  const homeGoals = uniqueShots.filter((s: ShotData) => (s.team === 'h' || s.team === 'home') && s.result === 'Goal').length;
  const awayGoals = uniqueShots.filter((s: ShotData) => (s.team === 'a' || s.team === 'away') && s.result === 'Goal').length;
  const homeXG = homeShots.reduce((a: number, s: ShotData) => a + s.xG, 0);
  const awayXG = awayShots.reduce((a: number, s: ShotData) => a + s.xG, 0);

  const StatBar: React.FC<StatBarProps> = ({ label, home = 0, away = 0, isFloat = false, index = 0 }) => {
    const total = home + away || 1;
    const homePct = (home / total) * 100;
    const homeWins = home > away;
    const awayWins = away > home;
    
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, delay: index * 0.06 }}
        className="group"
      >
        <div className="flex items-baseline justify-between mb-2.5">
          <span
            className="font-black tabular-nums leading-none transition-all duration-200"
            style={{
              fontSize: "clamp(1.6rem, 3vw, 2.4rem)",
              color: homeWins ? "#007AFF" : "#4a7ab5",
              textShadow: homeWins ? "0 0 20px rgba(0,122,255,0.35)" : "none",
              fontFamily: "var(--font-oswald, var(--font-inter, sans-serif))",
            }}
          >
            {isFloat ? home.toFixed(2) : home}
          </span>

          <span
            className="text-[9px] font-black uppercase tracking-[0.3em] px-3 py-1 rounded-full"
            style={{
              color: "#94a3b8",
              background: "rgba(148,163,184,0.07)",
              letterSpacing: "0.22em",
            }}
          >
            {label}
          </span>

          <span
            className="font-black tabular-nums leading-none transition-all duration-200"
            style={{
              fontSize: "clamp(1.6rem, 3vw, 2.4rem)",
              color: awayWins ? "#FF2A6D" : "#b54a69",
              textShadow: awayWins ? "0 0 20px rgba(255,42,109,0.35)" : "none",
              fontFamily: "var(--font-oswald, var(--font-inter, sans-serif))",
            }}
          >
            {isFloat ? away.toFixed(2) : away}
          </span>
        </div>

        <div className="relative h-[14px] w-full rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.04)" }}>
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${homePct}%` }}
            transition={{ duration: 0.7, delay: index * 0.06 + 0.1, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="absolute left-0 top-0 h-full rounded-full"
            style={{
              background: homeWins
                ? "linear-gradient(90deg, #0051d4 0%, #007AFF 100%)"
                : "linear-gradient(90deg, #003b99 0%, #005fd4 100%)",
              boxShadow: homeWins ? "0 0 12px rgba(0,122,255,0.4)" : "none",
            }}
          />
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${100 - homePct}%` }}
            transition={{ duration: 0.7, delay: index * 0.06 + 0.15, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="absolute right-0 top-0 h-full rounded-full"
            style={{
              background: awayWins
                ? "linear-gradient(90deg, #FF2A6D 0%, #c41f54 100%)"
                : "linear-gradient(90deg, #c41f54 0%, #8a1438 100%)",
              boxShadow: awayWins ? "0 0 12px rgba(255,42,109,0.4)" : "none",
            }}
          />
        </div>
      </motion.div>
    );
  };

  return (
    <div suppressHydrationWarning className="min-h-screen bg-[#0A192F] text-white font-sans pb-20" style={{ fontFamily: "var(--font-inter, sans-serif)" }}>

      {/* TOP BAR */}
      <div className="bg-[#060F1E] border-b border-slate-800 h-14 flex items-center px-6 sticky top-0 z-50 justify-between">
        <button onClick={() => router.back()} className="flex items-center gap-3 group hover:opacity-60 transition-opacity cursor-pointer">
          <ArrowLeft size={16} className="text-slate-500" />
          <span className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-500">{t("match.back")}</span>
        </button>
        <span className="text-[9px] font-black text-[#FF2A6D] uppercase tracking-[0.4em]">{t("match.report_title")}</span>
      </div>

      <main className="max-w-[1000px] mx-auto py-10 px-6 space-y-6">

        {/* HERO RESULT BANNER */}
        <section className="bg-[#060F1E] rounded-2xl border border-slate-800 border-b-4 border-b-[#FF2A6D] overflow-hidden">
          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-0">
            {/* Home */}
            <div className="p-8 flex flex-col items-center text-center border-r border-slate-800">
              <h1 className="text-2xl md:text-3xl font-black uppercase tracking-tighter leading-none mb-3 text-white"
                style={{ fontFamily: "var(--font-oswald, var(--font-inter, sans-serif))" }}>
                {match.home_team}
              </h1>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">xG</span>
                <span className="text-xl font-black text-[#007AFF]">{match.home_xG.toFixed(2)}</span>
              </div>
            </div>

            {/* Score */}
            <div className="px-8 flex flex-col items-center gap-1">
              <div className="flex items-center gap-4">
                <span className="text-6xl md:text-7xl font-black tracking-tighter text-white"
                  style={{ fontFamily: "var(--font-oswald, var(--font-inter, sans-serif))" }}>
                  {match.home_score}
                </span>
                <span className="text-3xl text-[#FF2A6D] font-black">—</span>
                <span className="text-6xl md:text-7xl font-black tracking-tighter text-white"
                  style={{ fontFamily: "var(--font-oswald, var(--font-inter, sans-serif))" }}>
                  {match.away_score}
                </span>
              </div>
              <span className="text-[9px] font-black uppercase tracking-[0.3em] text-slate-600 mt-1">{t("match.final_result")}</span>
            </div>

            {/* Away */}
            <div className="p-8 flex flex-col items-center text-center border-l border-slate-800">
              <h1 className="text-2xl md:text-3xl font-black uppercase tracking-tighter leading-none mb-3 text-white"
                style={{ fontFamily: "var(--font-oswald, var(--font-inter, sans-serif))" }}>
                {match.away_team}
              </h1>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xl font-black text-[#FF2A6D]">{match.away_xG.toFixed(2)}</span>
                <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">xG</span>
              </div>
            </div>
          </div>
        </section>

        {/* xG TIMING CHART */}
        <section className="bg-[#060F1E] rounded-2xl border border-slate-800 p-6">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <Activity size={16} className="text-slate-600" />
              <h2 className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">{t("match.xg_momentum")}</h2>
            </div>
            <div className="flex gap-5 text-[9px] font-black uppercase tracking-widest">
              <span className="text-[#007AFF] flex items-center gap-1.5">
                <div className="w-4 h-0.5 bg-[#007AFF]" /> {match.home_team}
              </span>
              <span className="text-[#FF2A6D] flex items-center gap-1.5">
                <div className="w-4 h-0.5 bg-[#FF2A6D]" /> {match.away_team}
              </span>
            </div>
          </div>

          <div className="relative flex">
            {/* Y axis */}
            <div className="flex flex-col justify-between pr-3 text-[9px] font-black text-slate-600 h-[260px] shrink-0">
              {[...yAxisTicks].reverse().map((tick, i) => (
                <span key={i} className="-translate-y-1/2">{tick.toFixed(1)}</span>
              ))}
            </div>

            <div className="relative flex-1 h-[260px]">
              {/* X axis minutes */}
              <div className="absolute -top-5 w-full flex">
                {[0, 15, 30, 45, 60, 75, 90].map(min => (
                  <span key={min} className="absolute text-[9px] font-black text-slate-600 -translate-x-1/2"
                    style={{ left: `${(min / 95) * 100}%` }}>
                    {min}&apos;
                  </span>
                ))}
              </div>

              <svg ref={chartRef} viewBox={`0 0 ${CHART_W} ${CHART_H}`} preserveAspectRatio="none"
                className="w-full h-full cursor-crosshair overflow-visible"
                onMouseMove={handleChartMouseMove} onMouseLeave={() => setChartHover(null)}>

                <defs>
                  <linearGradient id="homeGrad" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#007AFF" stopOpacity="0.15" />
                    <stop offset="100%" stopColor="#007AFF" stopOpacity="0" />
                  </linearGradient>
                  <linearGradient id="awayGrad" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#FF2A6D" stopOpacity="0.15" />
                    <stop offset="100%" stopColor="#FF2A6D" stopOpacity="0" />
                  </linearGradient>
                </defs>

                {/* Grid lines */}
                {yAxisTicks.map(tick => {
                  const y = CHART_H - (tick / maxVisualXG) * CHART_H;
                  return <line key={tick} x1="0" y1={y} x2={CHART_W} y2={y} stroke="#1e3a5f" strokeWidth="0.5" strokeDasharray="6,6" vectorEffect="non-scaling-stroke" />;
                })}

                {/* Area fills */}
                <path d={`${generateStepPath(homeSteps)} L ${CHART_W} ${CHART_H} L 0 ${CHART_H} Z`} fill="url(#homeGrad)" />
                <path d={`${generateStepPath(awaySteps)} L ${CHART_W} ${CHART_H} L 0 ${CHART_H} Z`} fill="url(#awayGrad)" />

                {/* Lines */}
                <path d={generateStepPath(homeSteps)} fill="none" stroke="#007AFF" strokeWidth="2" strokeLinejoin="miter" strokeMiterlimit="10" vectorEffect="non-scaling-stroke" />
                <path d={generateStepPath(awaySteps)} fill="none" stroke="#FF2A6D" strokeWidth="2" strokeLinejoin="miter" strokeMiterlimit="10" vectorEffect="non-scaling-stroke" />

                {/* Goal markers */}
                {uniqueShots.filter((s: ShotData) => s.result === 'Goal').map((goal: ShotData, idx: number) => {
                  const isHome = goal.team === 'h' || goal.team === 'home';
                  const steps = isHome ? homeSteps : awaySteps;
                  const pt = steps.find(s => s.min === goal.minute);
                  if (!pt) return null;
                  const cx = (pt.min / 95) * CHART_W;
                  const cy = CHART_H - (pt.xg / maxVisualXG) * CHART_H;
                  return <text key={idx} x={cx} y={cy} fontSize="20" textAnchor="middle" dominantBaseline="central">⚽</text>;
                })}

                {/* Hover line */}
                {chartHover && (
                  <line x1={(chartHover.min / 95) * CHART_W} y1="0" x2={(chartHover.min / 95) * CHART_W} y2={CHART_H}
                    stroke="#FF2A6D" strokeWidth="0.8" strokeDasharray="4,4" vectorEffect="non-scaling-stroke" />
                )}
              </svg>

              {/* Hover tooltip */}
              {chartHover && (
                <div className="absolute top-2 left-1/2 -translate-x-1/2 pointer-events-none bg-[#0A192F] border border-slate-700 text-white px-4 py-2 rounded-lg shadow-xl z-50 text-[9px] font-black flex gap-4 whitespace-nowrap">
                  <span className="text-slate-500">{chartHover.min}&apos; MIN</span>
                  <span className="text-[#007AFF]">{match.home_team}: {chartHover.xgH.toFixed(2)}</span>
                  <span className="text-[#FF2A6D]">{match.away_team}: {chartHover.xgA.toFixed(2)}</span>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* SHOT MAP — full pitch SVG */}
        <section className="bg-[#060F1E] rounded-2xl border border-slate-800 p-6">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <Crosshair size={16} className="text-slate-600" />
              <h2 className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">{t("match.shot_map")}</h2>
            </div>
            {/* Shot summary */}
            <div className="flex items-center gap-6 text-[9px] font-black uppercase tracking-widest">
              <div className="flex items-center gap-2">
                <span className="text-[#007AFF]">{match.home_team}</span>
                <span className="text-slate-600">•</span>
                <span className="text-slate-400">{homeShots.length} tiri</span>
                <span className="text-slate-600">•</span>
                <span className="text-white">{homeGoals} gol</span>
                <span className="text-slate-600">•</span>
                <span className="text-[#007AFF]">xG {homeXG.toFixed(2)}</span>
              </div>
              <span className="text-slate-700">|</span>
              <div className="flex items-center gap-2">
                <span className="text-[#FF2A6D]">{match.away_team}</span>
                <span className="text-slate-600">•</span>
                <span className="text-slate-400">{awayShots.length} tiri</span>
                <span className="text-slate-600">•</span>
                <span className="text-white">{awayGoals} gol</span>
                <span className="text-slate-600">•</span>
                <span className="text-[#FF2A6D]">xG {awayXG.toFixed(2)}</span>
              </div>
            </div>
          </div>

          <div className="relative w-full" style={{ aspectRatio: "100/68" }}>
            <svg viewBox="0 0 100 68" preserveAspectRatio="xMidYMid meet" className="w-full h-full rounded-xl overflow-hidden">
              <defs>
                <filter id="goal-glow-full" x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur in="SourceAlpha" stdDeviation="1.5" result="blur" />
                  <feFlood floodColor="#FFD700" floodOpacity="0.8" result="color" />
                  <feComposite in="color" in2="blur" operator="in" result="shadow" />
                  <feMerge><feMergeNode in="shadow" /><feMergeNode in="SourceGraphic" /></feMerge>
                </filter>
              </defs>

              {/* Pitch background */}
              <rect x="0" y="0" width="100" height="68" fill="#1a5c2a" />
              {/* Pitch stripes */}
              {[0,1,2,3,4,5,6,7,8,9].map(i => (
                <rect key={i} x={i*10} y="0" width="10" height="68" fill={i%2===0 ? "#1a5c2a" : "#1d6430"} />
              ))}

              {/* Lines */}
              <g stroke="#FFFFFF" strokeOpacity="0.5" strokeWidth="0.3" fill="none" vectorEffect="non-scaling-stroke">
                <rect x="0.5" y="0.5" width="99" height="67" />
                <line x1="50" y1="0.5" x2="50" y2="67.5" />
                <circle cx="50" cy="34" r="9.15" />
                <circle cx="50" cy="34" r="0.5" fill="white" fillOpacity="0.5" />
                <rect x="0.5" y="13.9" width="16.5" height="40.2" />
                <rect x="0.5" y="24.8" width="5.5" height="18.4" />
                <rect x="83" y="13.9" width="16.5" height="40.2" />
                <rect x="94" y="24.8" width="5.5" height="18.4" />
                <circle cx="11" cy="34" r="0.5" fill="white" fillOpacity="0.5" />
                <circle cx="89" cy="34" r="0.5" fill="white" fillOpacity="0.5" />
              </g>

              <rect x="0" y="29.5" width="0.5" height="9" fill="#FFFFFF" fillOpacity="0.8" />
              <rect x="99.5" y="29.5" width="0.5" height="9" fill="#FFFFFF" fillOpacity="0.8" />

              <text x="8" y="65" fontSize="2.5" fontWeight="900" fill="#007AFF" fillOpacity="0.6" textAnchor="middle"
                style={{ fontFamily: "var(--font-oswald, sans-serif)" }}>
                {match.home_team.substring(0, 12).toUpperCase()}
              </text>
              <text x="92" y="65" fontSize="2.5" fontWeight="900" fill="#FF2A6D" fillOpacity="0.6" textAnchor="middle"
                style={{ fontFamily: "var(--font-oswald, sans-serif)" }}>
                {match.away_team.substring(0, 12).toUpperCase()}
              </text>

              {uniqueShots.map((s: ShotData, i: number) => {
                const { cx, cy, isHome } = shotToSvg(s);
                const isGoal = s.result === 'Goal';
                const color = isHome ? "#007AFF" : "#FF2A6D";
                const r = 0.8 + s.xG * 1.8;

                if (isGoal) {
                  return (
                    <text key={i} x={cx} y={cy} textAnchor="middle" dominantBaseline="central"
                      fontSize="4.5" filter="url(#goal-glow-full)"
                      onMouseEnter={() => setHoveredShot(s)} onMouseLeave={() => setHoveredShot(null)}
                      style={{ cursor: "crosshair" }}>
                      ⚽
                    </text>
                  );
                }
                return (
                  <circle key={i} cx={cx} cy={cy} r={r}
                    fill={color} fillOpacity={0.55}
                    stroke={color} strokeWidth={0.35} strokeOpacity={0.9}
                    onMouseEnter={() => setHoveredShot(s)} onMouseLeave={() => setHoveredShot(null)}
                    style={{ cursor: "crosshair" }}
                  />
                );
              })}
            </svg>

            <AnimatePresence>
              {hoveredShot && (
                <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
                  className="absolute top-4 right-4 bg-[#060F1E]/95 backdrop-blur-xl text-white p-5 rounded-2xl shadow-2xl z-50 border border-slate-800 min-w-[240px] pointer-events-none">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <div className="text-[9px] font-black text-[#FF2A6D] uppercase tracking-widest mb-1">{hoveredShot.minute}&apos; MIN</div>
                      <div className="text-base font-black uppercase leading-tight">{hoveredShot.player}</div>
                    </div>
                    <div className={`px-2.5 py-1 rounded-lg text-[9px] font-black uppercase border ${hoveredShot.result === 'Goal' ? 'bg-green-500/20 text-green-400 border-green-500/30' : 'bg-white/5 border-white/10 text-slate-400'}`}>
                      {hoveredShot.result}
                    </div>
                  </div>
                  <div className="space-y-2 border-t border-slate-800 pt-3">
                    <div className="flex justify-between text-[10px] font-bold">
                      <span className="text-slate-500 uppercase">{t("match.shot_action")}</span>
                      <span className="text-white">{hoveredShot.situation || 'Open Play'}</span>
                    </div>
                    <div className="flex justify-between text-[10px] font-bold">
                      <span className="text-slate-500 uppercase">{t("match.shot_type")}</span>
                      <span className="text-yellow-400">{hoveredShot.shotType || 'N/D'}</span>
                    </div>
                    <div className="flex justify-between text-[10px] font-bold">
                      <span className="text-slate-500 uppercase">{t("match.previous")}</span>
                      <span className="text-slate-300">{hoveredShot.lastAction || '-'}</span>
                    </div>
                    <div className="flex justify-between items-center pt-2 border-t border-slate-800">
                      <span className="text-[9px] font-black text-slate-500 uppercase">xG</span>
                      <span className="text-2xl font-black text-white">{hoveredShot.xG.toFixed(3)}</span>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="flex items-center justify-center gap-8 mt-4 text-[9px] font-black uppercase tracking-widest text-slate-500">
            <span className="flex items-center gap-2"><svg width="10" height="10"><circle cx="5" cy="5" r="4" fill="#007AFF" fillOpacity="0.55" stroke="#007AFF" strokeWidth="1" /></svg>{t("match.shot_home")}</span>
            <span className="flex items-center gap-2"><svg width="10" height="10"><circle cx="5" cy="5" r="4" fill="#FF2A6D" fillOpacity="0.55" stroke="#FF2A6D" strokeWidth="1" /></svg>{t("match.shot_away")}</span>
            <span className="flex items-center gap-1">⚽ {t("match.goal_label")}</span>
            <span className="flex items-center gap-1">{t("match.circle_xg")}</span>
          </div>
        </section>

        {/* MATCH STATS */}
        <section
          className="rounded-2xl overflow-hidden"
          style={{
            background: "linear-gradient(135deg, #060F1E 0%, #081424 100%)",
            border: "1px solid rgba(255,255,255,0.06)",
            boxShadow: "0 4px 40px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04)",
          }}
        >
          <div
            className="flex justify-between items-center px-8 py-5"
            style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
          >
            <h3
              className="font-black uppercase tracking-tight text-[#007AFF]"
              style={{
                fontSize: "clamp(0.85rem, 2vw, 1.1rem)",
                fontFamily: "var(--font-oswald, var(--font-inter, sans-serif))",
                textShadow: "0 0 16px rgba(0,122,255,0.3)",
              }}
            >
              {match.home_team}
            </h3>

            <div className="flex flex-col items-center gap-1.5">
              <BarChart3 size={14} className="text-slate-600" />
              <span className="text-[8px] font-black uppercase tracking-[0.4em] text-slate-600">{t("match.stats_title")}</span>
            </div>

            <h3
              className="font-black uppercase tracking-tight text-right text-[#FF2A6D]"
              style={{
                fontSize: "clamp(0.85rem, 2vw, 1.1rem)",
                fontFamily: "var(--font-oswald, var(--font-inter, sans-serif))",
                textShadow: "0 0 16px rgba(255,42,109,0.3)",
              }}
            >
              {match.away_team}
            </h3>
          </div>

          <div className="px-8 py-6 space-y-6">
            <StatBar index={0} label="GOALS"          home={match.home_score}          away={match.away_score} />
            <StatBar index={1} label="xG"             home={match.home_xG}             away={match.away_xG}              isFloat />
            <StatBar index={2} label="SHOTS"          home={match.stats?.home_shots}    away={match.stats?.away_shots} />
            <StatBar index={3} label="SHOTS ON TARGET" home={match.stats?.home_sot}      away={match.stats?.away_sot} />
            <StatBar index={4} label="DEEP"           home={match.stats?.home_deep}     away={match.stats?.away_deep} />
            <StatBar index={5} label="PPDA"           home={match.stats?.home_ppda}     away={match.stats?.away_ppda}     isFloat />
            <StatBar index={6} label="xPTS"           home={match.stats?.home_xpts}     away={match.stats?.away_xpts}     isFloat />
          </div>
        </section>

        {/* NUOVO COMPONENTE FORMAZIONI */}
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
           <MatchLineups 
              matchId={matchId} 
              homeTeam={match.home_team} 
              awayTeam={match.away_team} 
           />
        </motion.section>

      </main>
    </div>
  );
}