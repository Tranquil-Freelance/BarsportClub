"use client";

import Image from "next/image";
import Link from "next/link";
import React, { useState, useMemo, useCallback, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import "../i18n/config";
import {
  TrendingUp, Percent, Hash, Swords, Target, Users,
  Goal, Crosshair, Plus, Trash2, ChevronDown, ChevronRight,
  BarChart3, SplitSquareVertical, Wallet, ArrowUpRight,
  ExternalLink, Sparkles, Activity, Zap, ShieldAlert,
  Trophy, Gauge, Calculator, PieChart, Dices, Brain,
  Flame, Feather, Star, AlertTriangle, Info, Lightbulb,
  Rocket, Layers, Shuffle, SlidersHorizontal, X, Clock,
} from "lucide-react";
import TeamLogo from "../../components/TeamLogo";
import { generateDeepSeekVerdict, type AiVerdict } from "../services/deepseekService";


// ═══════════════════════════════════════════════════════════════
//  TYPES
// ═══════════════════════════════════════════════════════════════

type LeagueId = "Serie A" | "Premier League" | "La Liga" | "Bundesliga" | "Ligue 1";
type MarketType = "asian-handicap" | "player-shots" | "player-assists" | "btts" | "1x2" | "over-under" | "custom";

interface TeamStats {
  xG: number;
  xGA: number;
  xA: number;
  ppda: number;
  deepPassesConceded: number;
  deepPassesMade: number;
  shotsFaced: number;
  shotsMade: number;
}

interface PlayerProp {
  name: string;
  team: string;
  avgShots: number;
  xA: number;
  keyPasses: number;
}

interface MatchAdvanced {
  id: string;
  home: string;
  away: string;
  league: LeagueId;
  date: string;
  match_datetime: string;
  homeStats: TeamStats;
  awayStats: TeamStats;
  homePlayers: PlayerProp[];
  awayPlayers: PlayerProp[];
}

interface MarketOdds {
  id: string;
  type: MarketType;
  label: string;
  line: string;
  modelProb: number;
  modelOdds: number;
  bestOdds: number;
  agency: string;
  edge: number;
  direction: string;
}


interface SlipSelection {
  match: MatchAdvanced;
  market: MarketOdds;
  pickLabel: string;
}

interface BestPick {
  match: MatchAdvanced;
  market: MarketOdds;
  aiVerdict: AiVerdict;
  combinedEdge: number;
}

interface Bolletta {
  id: string;
  name: string;
  subtitle: string;
  icon: React.ReactNode;
  colorScheme: {
    bg: string;
    border: string;
    accent: string;
    text: string;
    badge: string;
  };
  description: string;
  picks: SlipSelection[];
  totalOdds: number;
  combinedEdge: number;
  riskLabel: string;
  riskColor: string;
}

type SlipMode = "multipla" | "portafoglio";

interface Agency { name: string; link: string; }

// ═══════════════════════════════════════════════════════════════
//  CONSTANTS
// ═══════════════════════════════════════════════════════════════

const ALL_LEAGUES: LeagueId[] = [
  "Serie A", "Premier League", "La Liga", "Bundesliga", "Ligue 1",
];

const LEAGUE_LOGOS: Record<LeagueId, string> = {
  "Serie A":        "/leagues/seriea.png",
  "Premier League": "/leagues/premierleague.png",
  "La Liga":        "/leagues/laliga.png",
  "Bundesliga":     "/leagues/bundesliga.png",
  "Ligue 1":        "/leagues/ligue1.png",
};

const AGENCIES: Agency[] = [
  { name: "Betfair",    link: "https://www.betfair.it" },
  { name: "Snai",       link: "https://www.snai.it" },
  { name: "1xBet",      link: "https://1xbet.com" },
  { name: "Pinnacle",   link: "https://www.pinnacle.com" },
  { name: "Bet365",     link: "https://www.bet365.it" },
  { name: "William Hill", link: "https://www.williamhill.it" },
];

const MARKET_META: Record<MarketType, { icon: React.ReactNode; short: string; color: string }> = {
  "asian-handicap":  { icon: <Swords size={13} />,        short: "AH",      color: "text-indigo-600" },
  "player-shots":    { icon: <Target size={13} />,         short: "TIRI",    color: "text-amber-600" },
  "player-assists":  { icon: <Users size={13} />,          short: "ASSIST",  color: "text-sky-600" },
  "btts":            { icon: <Goal size={13} />,           short: "GOL/GOL", color: "text-rose-600" },
  "1x2":             { icon: <SplitSquareVertical size={13} />, short: "1X2", color: "text-cyan-600" },
  "over-under":      { icon: <Activity size={13} />,       short: "OU",      color: "text-orange-600" },
  "custom":          { icon: <Hash size={13} />,           short: "CUSTOM",  color: "text-slate-500" },
};

// ═══════════════════════════════════════════════════════════════
//  API TYPES + ADAPTERS
// ═══════════════════════════════════════════════════════════════

interface ApiTopPick {
  match_id: number;
  home_team: string;
  away_team: string;
  league_name: string;
  market_label: string;
  odds: number | null;
  ev_base: number | null;
}

const LEAGUE_ID_MAP: Record<string, LeagueId> = {
  "serie a":       "Serie A",
  "premier league":"Premier League",
  "la liga":       "La Liga",
  "bundesliga":    "Bundesliga",
  "ligue 1":       "Ligue 1",
};

function mapLeagueId(name: string): LeagueId {
  return LEAGUE_ID_MAP[name.toLowerCase()] ?? "Serie A";
}

function mapMarketKeyToType(key: string): MarketType {
  const k = key.toLowerCase();
  if (k.includes("1x2")) return "1x2";
  if (k.includes("both_teams") || k.includes("both teams")) return "btts";
  if (k.includes("over") || k.includes("under")) return "over-under";
  if (k.includes("shot")) return "player-shots";
  if (k.includes("assist")) return "player-assists";
  if (k.includes("asian") || k.includes("handicap")) return "asian-handicap";
  return "custom";
}

function emptyStats(): TeamStats {
  return { xG: 0, xGA: 0, xA: 0, ppda: 0, deepPassesConceded: 0, deepPassesMade: 0, shotsFaced: 0, shotsMade: 0 };
}

function mapApiPickToBestPick(p: ApiTopPick): BestPick {
  const odds = p.odds ?? 0;
  const evBase = p.ev_base ?? 0;
  // Derive model probability: EV = odds * model_prob - 1  →  model_prob = (1 + EV) / odds
  const modelProb = odds > 0 ? Math.min((1 + evBase) / odds, 0.99) : 0;
  const edgePct = +(evBase * 100).toFixed(1);
  const confidence: "Alta" | "Media" | "Bassa" = evBase >= 0.07 ? "Alta" : evBase >= 0.045 ? "Media" : "Bassa";
  const marketKey = p.market_label || "1X2";
  return {
    match: {
      id: String(p.match_id),
      home: p.home_team || "—",
      away: p.away_team || "—",
      league: mapLeagueId(p.league_name || "Unknown"),
      date: "",
      match_datetime: "",
      homeStats: emptyStats(),
      awayStats: emptyStats(),
      homePlayers: [],
      awayPlayers: [],
    },
    market: {
      id: `api-${p.match_id}-${marketKey}`,
      type: mapMarketKeyToType(marketKey),
      label: p.market_label || marketKey,
      line: marketKey,
      modelProb,
      modelOdds: modelProb > 0 ? +(1 / modelProb).toFixed(2) : 0,
      bestOdds: odds,
      agency: "",
      edge: edgePct,
      direction: "Over",
    },
    aiVerdict: {
      summary: `Edge ${edgePct}% | Quota ${odds.toFixed(2)}`,
      reasoning: `Modello Poisson: quota ${odds.toFixed(2)}, edge stimato ${edgePct}%.`,
      keyFactor: p.market_label || marketKey,
      confidence,
    },
    combinedEdge: edgePct,
  };
}

function deriveBollettesFromPicks(picks: BestPick[]): Bolletta[] {
  if (picks.length === 0) return [];

  const toSlip = (pick: BestPick): SlipSelection => ({
    match: pick.match,
    market: pick.market,
    pickLabel: `${pick.match.home} vs ${pick.match.away} · ${pick.market.label}`,
  });

  const byProb  = [...picks].sort((a, b) => b.market.modelProb - a.market.modelProb).slice(0, 3);
  const byOdds  = [...picks].sort((a, b) => b.market.bestOdds  - a.market.bestOdds).slice(0, 3);
  const byEdge  = [...picks].sort((a, b) => b.market.edge      - a.market.edge).slice(0, 3);

  function calcGroup(group: BestPick[]): { slips: SlipSelection[]; totalOdds: number; combinedEdge: number } {
    const slips = group.map(toSlip);
    const totalOdds = slips.length > 0 ? +slips.reduce((acc, p) => acc * (p.market.bestOdds || 1), 1).toFixed(2) : 0;
    const combinedEdge = slips.length > 0 ? +(slips.reduce((acc, p) => acc + p.market.edge, 0) / slips.length).toFixed(1) : 0;
    return { slips, totalOdds, combinedEdge };
  }

  const solid = calcGroup(byProb);
  const pazza = calcGroup(byOdds);
  const mix   = calcGroup(byEdge);

  return [
    {
      id: "solida",
      name: "LA SOLIDA",
      subtitle: "Raddoppio Matematico",
      icon: <ShieldAlert size={18} />,
      colorScheme: { bg: "bg-transparent", border: "border-emerald-500/40", accent: "text-emerald-400", text: "text-white", badge: "bg-emerald-900/40 text-emerald-400 border border-emerald-700/50" },
      description: `${solid.slips.length} eventi a basso rischio con la più alta probabilità di successo secondo il modello.`,
      picks: solid.slips,
      totalOdds: solid.totalOdds,
      combinedEdge: solid.combinedEdge,
      riskLabel: "BASSO",
      riskColor: "text-emerald-600",
    },
    {
      id: "pazza",
      name: "LA PAZZA",
      subtitle: "Multipla Europea ad Alta Varianza",
      icon: <Flame size={18} />,
      colorScheme: { bg: "bg-transparent", border: "border-rose-500/40", accent: "text-rose-400", text: "text-white", badge: "bg-rose-900/40 text-rose-400 border border-rose-700/50" },
      description: `${pazza.slips.length} eventi ad alta quota. Rischio elevato, potenziale ritorno esponenziale.`,
      picks: pazza.slips,
      totalOdds: pazza.totalOdds,
      combinedEdge: pazza.combinedEdge,
      riskLabel: "ALTO",
      riskColor: "text-rose-600",
    },
    {
      id: "mixmaster",
      name: "THE MIX MASTER",
      subtitle: "Massimo Valore Atteso (Edge)",
      icon: <Star size={18} />,
      colorScheme: { bg: "bg-transparent", border: "border-indigo-500/40", accent: "text-indigo-400", text: "text-white", badge: "bg-indigo-900/40 text-indigo-400 border border-indigo-700/50" },
      description: `${mix.slips.length} eventi con l'Edge percentuale più alto. Il portafoglio a più alto valore atteso del palinsesto.`,
      picks: mix.slips,
      totalOdds: mix.totalOdds,
      combinedEdge: mix.combinedEdge,
      riskLabel: "MEDIO",
      riskColor: "text-amber-600",
    },
  ];
}

function generateMarkets(_match: MatchAdvanced): MarketOdds[] {
  return [];
}

// ═══════════════════════════════════════════════════════════════
//  COMPONENTS
// ═══════════════════════════════════════════════════════════════

// ── EDGE BADGE ─────────────────────────────────────────────

function EdgeBadge({ edge, size = "sm" }: { edge: number; size?: "sm" | "md" | "lg" }) {
  const isPos = edge > 0;
  const isNeutral = edge >= -0.5 && edge <= 0.5;
  const px = size === "lg" ? "px-3 py-1.5" : size === "md" ? "px-2.5 py-1" : "px-2 py-1";
  const fs = size === "lg" ? "text-sm" : size === "md" ? "text-xs" : "text-xs";

  let bg: string, text: string, border: string;
  if (isPos) {
    bg = "bg-emerald-50";
    text = "text-emerald-600";
    border = "border-emerald-200";
  } else if (isNeutral) {
    bg = "bg-slate-100";
    text = "text-slate-400";
    border = "border-slate-200";
  } else {
    bg = "bg-rose-50";
    text = "text-rose-600";
    border = "border-rose-200";
  }

  return (
    <span className={`inline-flex items-center gap-1 ${px} rounded-md ${border} border ${bg} ${text} ${fs} font-mono font-bold leading-none tabular-nums`}>
      <TrendingUp size={size === "lg" ? 14 : size === "md" ? 12 : 11} />
      {isPos ? "+" : ""}{edge.toFixed(1)}%
    </span>
  );
}

// ── CONFIDENCE BADGE ────────────────────────────────────────

function ConfidenceBadge({ level }: { level: "Alta" | "Media" | "Bassa" }) {
  const colors = {
    Alta: { bg: "bg-emerald-50", text: "text-emerald-600", border: "border-emerald-200", icon: <Sparkles size={12} /> },
    Media: { bg: "bg-amber-50", text: "text-amber-600", border: "border-amber-200", icon: <Activity size={12} /> },
    Bassa: { bg: "bg-rose-50", text: "text-rose-600", border: "border-rose-200", icon: <AlertTriangle size={12} /> },
  };
  const c = colors[level];
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md ${c.bg} ${c.text} ${c.border} border text-xs font-bold font-mono tabular-nums`}>
      {c.icon} {level}
    </span>
  );
}

// ═══════════════════════════════════════════════════════════════
//  BOLLETTE PRONTE (Hero Section)
// ═══════════════════════════════════════════════════════════════

function BollettaCard({
  bolletta,
  onAddToBuilder,
}: {
  bolletta: Bolletta;
  onAddToBuilder: (picks: SlipSelection[]) => void;
}) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(false);
  const cs = bolletta.colorScheme;

  return (
    <div className="flex flex-col h-full px-5 py-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-start gap-2.5">
          <div className={`w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center flex-shrink-0 mt-0.5 ${cs.accent}`}>
            {bolletta.icon}
          </div>
          <div>
            <h3 className="text-sm font-black tracking-tight text-white uppercase">
              {bolletta.name}
            </h3>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-0.5">
              {bolletta.subtitle}
            </p>
          </div>
        </div>
        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${cs.badge}`}>
          {t("betting.risk")} {bolletta.riskLabel}
        </span>
      </div>

      {/* Description */}
      <p className="text-xs text-slate-400 leading-relaxed mb-3">
        {bolletta.description}
      </p>

      {/* Quick Stats */}
      <div className="flex items-center gap-4 mb-3">
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{t("betting.odds")}</span>
          <span className="font-mono font-black text-sm text-white tabular-nums">{bolletta.totalOdds}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{t("betting.avg_edge")}</span>
          <span className={`font-mono font-bold text-sm tabular-nums ${cs.accent}`}>
            +{bolletta.combinedEdge.toFixed(1)}%
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
            {bolletta.picks.length} {t("betting.events")}
          </span>
        </div>
      </div>

      {/* Expanded picks */}
      <div className="flex-1">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-[10px] font-medium text-slate-500 hover:text-slate-300 transition-colors mb-1"
        >
          {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          {expanded ? t("betting.hide_details") : t("betting.show_details")}
        </button>
        {expanded && (
          <div className="pb-2 space-y-1.5">
            {bolletta.picks.map((pick) => {
              const meta = MARKET_META[pick.market.type];
              return (
                <div key={pick.market.id} className="flex items-center justify-between text-xs bg-slate-800/60 rounded-lg px-2.5 py-1.5 border border-slate-700/50">
                  <div className="flex items-center gap-1.5 min-w-0 flex-1">
                    <span className={meta?.color ?? "text-slate-500"}>{meta?.icon}</span>
                    <span className="font-medium text-slate-300 truncate">
                      {pick.match.home} vs {pick.match.away}
                    </span>
                    <span className="text-slate-500 font-mono tabular-nums">{pick.market.line}</span>
                  </div>
                  <span className={`font-mono font-bold flex-shrink-0 ml-2 tabular-nums ${cs.accent}`}>
                    @{pick.market.bestOdds.toFixed(2)}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* CTA */}
      <div className="mt-4">
        <button
          onClick={() => onAddToBuilder(bolletta.picks)}
          className={`w-full py-2.5 rounded-lg font-bold text-xs uppercase tracking-wider transition-all hover:bg-slate-800 flex items-center justify-center gap-1.5 bg-slate-900/80 border ${cs.border} ${cs.accent}`}
        >
          <Plus size={14} />
          {t("betting.add_to_builder")}
        </button>
      </div>
    </div>
  );
}

function BollettePronteSection({
  bollettes,
  onAddToBuilder,
}: {
  bollettes: Bolletta[];
  onAddToBuilder: (picks: SlipSelection[]) => void;
}) {
  const { t } = useTranslation();
  return (
    <div className="mb-6">
      <div className="flex items-center gap-2.5 mb-4">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-sm">
          <Rocket size={16} className="text-white" />
        </div>
        <div>
          <h2 className="text-sm font-black text-slate-800 uppercase tracking-tight">
            {t("betting.bollette_pronte")}
          </h2>
          <p className="text-[10px] text-slate-500 font-medium">
            {t("betting.bollette_desc")}
          </p>
        </div>
      </div>
      <div className="rounded-xl bg-[#1a1b26] border border-slate-700/50 overflow-hidden">
        <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-slate-700/50">
          {bollettes.map((b) => (
            <BollettaCard key={b.id} bolletta={b} onAddToBuilder={onAddToBuilder} />
          ))}
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
//  BEST PICKS & AI VERDICT (DeepSeek-powered)
// ═══════════════════════════════════════════════════════════════

function AiVerdictPanel({ verdict }: { verdict: AiVerdict }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-[10px] font-medium text-slate-400 hover:text-slate-600 transition-colors"
      >
        <Brain size={12} className="text-indigo-400" />
        <span>DeepSeek AI Verdict</span>
        <span className="text-[10px] text-slate-300">— {verdict.summary}</span>
        {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
      </button>
      {open && (
        <div className="mt-1.5 bg-gradient-to-r from-indigo-50/80 to-violet-50/80 border border-indigo-100 rounded-lg p-3 space-y-2">
          <div className="flex items-start gap-2">
            <Lightbulb size={14} className="text-amber-500 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-slate-700 leading-relaxed">
              {verdict.reasoning}
            </p>
          </div>
          <div className="flex items-center justify-between pt-1 border-t border-indigo-100/50">
            <div className="flex items-center gap-1.5">
              <Info size={11} className="text-slate-400" />
              <span className="text-[10px] font-medium text-slate-500">
                Fattore chiave: <strong className="text-slate-700">{verdict.keyFactor}</strong>
              </span>
            </div>
            <ConfidenceBadge level={verdict.confidence} />
          </div>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
//  TOP 3 BEST PICKS — HERO SECTION
// ═══════════════════════════════════════════════════════════════


function BestPickHeroCard({
  pick,
  rank,
  onAddToSlip,
}: {
  pick: BestPick;
  rank: 1 | 2 | 3;
  onAddToSlip: (match: MatchAdvanced, market: MarketOdds) => void;
}) {
  const { t } = useTranslation();
  const meta = MARKET_META[pick.market.type];
  const isTop = rank === 1;
  const gradientBorder = isTop
    ? "linear-gradient(135deg, #ccff00, #00f0ff)"
    : "linear-gradient(135deg, rgba(204,255,0,0.3), rgba(0,240,255,0.3))";
  const glowShadow = isTop
    ? "0 0 30px rgba(204,255,0,0.15), 0 0 60px rgba(0,240,255,0.08)"
    : "0 0 15px rgba(204,255,0,0.06)";

  return (
    <div
      className="relative flex-shrink-0 w-[280px] sm:w-72 rounded-2xl overflow-hidden"
      style={{
        background: "rgba(10,16,30,0.95)",
        border: "1px solid transparent",
        boxShadow: glowShadow,
      }}
    >
      {/* Gradient border overlay */}
      <div
        className="absolute inset-0 rounded-2xl pointer-events-none"
        style={{
          border: "1.5px solid transparent",
          borderRadius: "inherit",
          backgroundImage: gradientBorder,
          WebkitMask: "linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0)",
          WebkitMaskComposite: "xor",
          maskComposite: "exclude",
        }}
      />

      {/* Rank badge */}
      <div className="absolute top-3 left-3 z-10">
        <div
          className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] font-black font-mono uppercase tracking-wider ${
            isTop ? "bg-[#ccff00]/20 text-[#ccff00]" : "bg-white/5 text-white/40"
          }`}
          style={{ border: `1px solid ${isTop ? "rgba(204,255,0,0.3)" : "rgba(255,255,255,0.08)"}` }}
        >
          <Star size={10} className={isTop ? "text-[#ccff00]" : "text-white/30"} />
          #{rank} BEST PICK
        </div>
      </div>

      {/* Content */}
      <div className="px-4 pt-12 pb-4 flex flex-col gap-3">
        {/* League + Match */}
        <div className="flex items-center gap-2">
          <img src={LEAGUE_LOGOS[pick.match.league]} alt="" className="w-5 h-5 object-contain flex-shrink-0" />
          <span className="text-[10px] font-mono font-bold uppercase tracking-widest text-white/40">
            {pick.match.league}
          </span>
        </div>
        <div className="font-black text-white leading-tight text-sm" style={{ fontFamily: "'Oswald', var(--font-oswald, sans-serif)" }}>
          {pick.match.home}
          <span className="text-white/20 text-[11px] font-normal mx-1">vs</span>
          {pick.match.away}
        </div>

        {/* Market icon + label */}
        <div className="flex items-center gap-2">
          <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${isTop ? "bg-[#ccff00]/15" : "bg-white/5"}`}
            style={{ border: `1px solid ${isTop ? "rgba(204,255,0,0.2)" : "rgba(255,255,255,0.06)"}` }}>
            <span style={{ color: isTop ? "#ccff00" : "rgba(255,255,255,0.5)" }}>
              {pick.market.type === "player-shots" ? <Target size={14} /> :
               pick.market.type === "player-assists" ? <Users size={14} /> :
               pick.market.type === "btts" ? <Goal size={14} /> :
               <Swords size={14} />}
            </span>
          </div>
          <div>
            <span className="text-[11px] font-bold text-white/80 uppercase tracking-wider">{meta?.short}</span>
            <span className="text-[11px] font-mono font-bold text-white/50 ml-2">{pick.market.line}</span>
          </div>
        </div>

        {/* Odds + Edge row */}
        <div className="grid grid-cols-2 gap-2">
          <div className="flex flex-col items-center rounded-xl py-2.5"
            style={{ background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.05)" }}>
            <span className="font-mono font-black text-lg leading-none tabular-nums" style={{ color: "#00f0ff" }}>
              @{pick.market.bestOdds.toFixed(2)}
            </span>
            <span className="text-[9px] font-mono font-bold uppercase tracking-widest mt-1 text-white/30">
              {t("betting.odds")}
            </span>
          </div>
          <div className="flex flex-col items-center rounded-xl py-2.5"
            style={{ background: "rgba(204,255,0,0.06)", border: "1px solid rgba(204,255,0,0.15)" }}>
            <span className="font-mono font-black text-lg leading-none tabular-nums" style={{ color: "#ccff00", textShadow: "0 0 20px rgba(204,255,0,0.3)" }}>
              +{pick.market.edge.toFixed(1)}%
            </span>
            <span className="text-[9px] font-mono font-bold uppercase tracking-widest mt-1 text-[#ccff00]/50">
              EDGE
            </span>
          </div>
        </div>

        {/* PUNTA ORA button */}
        <button
          onClick={() => onAddToSlip(pick.match, pick.market)}
          className="w-full py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all duration-200 active:scale-[0.97]"
          style={{
            background: isTop
              ? "linear-gradient(135deg, #ccff00, #00f0ff)"
              : "linear-gradient(135deg, rgba(204,255,0,0.15), rgba(0,240,255,0.15))",
            color: isTop ? "#0a101e" : "#ccff00",
            border: `1px solid ${isTop ? "transparent" : "rgba(204,255,0,0.2)"}`,
          }}
        >
          <Zap size={12} className="inline mr-1.5" />
          {t("betting.bet_now")}
        </button>
      </div>
    </div>
  );
}

function BestPicksHeroSection({
  picks,
  onAddToSlip,
}: {
  picks: BestPick[];
  onAddToSlip: (match: MatchAdvanced, market: MarketOdds) => void;
}) {
  const { t } = useTranslation();
  if (picks.length === 0) return null;

  return (
    <div className="mb-6">
      <div className="flex items-center gap-2.5 mb-4">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#ccff00] to-[#00f0ff] flex items-center justify-center shadow-sm">
          <Star size={15} className="text-[#0a101e]" />
        </div>
        <div>
          <h2 className="text-sm font-black text-slate-800 uppercase tracking-tight">
            {t("betting.top_3_best_picks")}
          </h2>
          <p className="text-[10px] text-slate-500 font-medium">
            {t("betting.top_3_desc")}
          </p>
        </div>
      </div>

      {/* Horizontal scrollable container */}
      <div className="flex gap-4 overflow-x-auto pb-2 -mx-4 px-4 snap-x snap-mandatory scrollbar-hide md:mx-0 md:px-0 md:grid md:grid-cols-3">
        {picks.map((pick, i) => (
          <div key={pick.market.id} className="snap-start">
            <BestPickHeroCard
              pick={pick}
              rank={(i + 1) as 1 | 2 | 3}
              onAddToSlip={onAddToSlip}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

function BestPickRow({
  pick,
  isSelected,
  onToggle,
}: {
  pick: BestPick;
  isSelected: boolean;
  onToggle: () => void;
}) {
  const meta = MARKET_META[pick.market.type];

  return (
    <div
      className={`group px-4 py-3 border-b border-slate-100 transition-all cursor-pointer ${
        isSelected
          ? "bg-emerald-50/70 border-l-2 border-l-emerald-400"
          : "hover:bg-slate-50 border-l-2 border-l-transparent"
      }`}
      onClick={onToggle}
    >
      <div className="flex items-center justify-between gap-4">
        {/* Left: Match info + Market */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <img src={LEAGUE_LOGOS[pick.match.league]} alt="" className="w-5 h-5 object-contain flex-shrink-0" />
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800 whitespace-nowrap">
                <span>{pick.match.home}</span>
                <span className="text-slate-400 text-xs font-normal">vs</span>
                <span>{pick.match.away}</span>
              </div>
              <p className="text-[10px] text-slate-500 font-mono tabular-nums">{pick.match.date}</p>
            </div>
          </div>
        </div>

        {/* Center: Market + Edge */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <div className="flex items-center gap-1.5">
            <span className={meta?.color ?? "text-slate-500"}>{meta?.icon}</span>
            <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">{meta?.short}</span>
            <span className="text-xs font-bold text-slate-800 tabular-nums">{pick.market.line}</span>
          </div>
          <EdgeBadge edge={pick.market.edge} size="md" />
        </div>

        {/* Right: Odds + CTA */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <div className="text-right">
            <span className="font-mono text-xs font-bold text-indigo-600 tabular-nums">@{pick.market.bestOdds.toFixed(2)}</span>
            <p className="text-[10px] text-slate-400 font-medium">{pick.market.agency}</p>
          </div>
          <div className={`p-1.5 rounded-lg border transition-all ${
            isSelected
              ? "bg-emerald-500 border-emerald-500 text-white"
              : "bg-white border-slate-200 text-slate-400 group-hover:border-emerald-300 group-hover:text-emerald-500 group-hover:bg-emerald-50"
          }`}>
            {isSelected ? <Trash2 size={12} /> : <Plus size={12} />}
          </div>
        </div>
      </div>

      {/* AI Verdict */}
      <AiVerdictPanel verdict={pick.aiVerdict} />
    </div>
  );
}

function BestPicksSection({
  picks,
  selections,
  onToggle,
}: {
  picks: BestPick[];
  selections: SlipSelection[];
  onToggle: (match: MatchAdvanced, market: MarketOdds) => void;
}) {
  const { t } = useTranslation();
  const [expandedPicks, setExpandedPicks] = useState(5);

  const selectedKeys = useMemo(() => new Set(selections.map(s => s.market.id)), [selections]);

  const visiblePicks = picks.slice(0, expandedPicks);

  // ── Async DeepSeek enhancement ─────────────────────────
  // On mount, try to upgrade verdicts via real DeepSeek/Ollama
  const [enhancedVerdicts, setEnhancedVerdicts] = useState<Record<string, AiVerdict>>({});

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();

    async function upgradeVerdicts() {
      for (const pick of picks) {
        if (cancelled) break;
        const id = pick.market.id;
        try {
          const deepSeekResult = await generateDeepSeekVerdict(
            pick.match,
            pick.market,
            controller.signal,
          );
          if (!cancelled) {
            setEnhancedVerdicts(prev => ({ ...prev, [id]: deepSeekResult }));
          }
        } catch {
          // Silently keep local verdict
        }
      }
    }

    upgradeVerdicts();
    return () => { cancelled = true; controller.abort(); };
  }, [picks]);

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Star size={14} className="text-amber-500" />
          <h2 className="text-sm font-bold text-slate-800 uppercase tracking-tight">
            {t("betting.top_european_singles")}
          </h2>
          <span className="text-xs font-mono text-slate-400 bg-slate-100 px-2 py-0.5 rounded-md tabular-nums">
            Edge {(picks[0]?.combinedEdge ?? 0).toFixed(1)}% – {(picks[picks.length - 1]?.combinedEdge ?? 0).toFixed(1)}%
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Brain size={12} className="text-indigo-400" />
          <span className="text-[10px] font-medium text-slate-500">{t("betting.deepseek_ai_per_pick")}</span>
        </div>
      </div>

      {/* Picks List */}
      <div className="divide-y divide-slate-100">
        {visiblePicks.map((pick) => {
          const id = pick.market.id;
          const enhancedVerdict = enhancedVerdicts[id];
          const displayPick = enhancedVerdict
            ? { ...pick, aiVerdict: enhancedVerdict }
            : pick;
          return (
            <BestPickRow
              key={id}
              pick={displayPick}
              isSelected={selectedKeys.has(id)}
              onToggle={() => onToggle(pick.match, pick.market)}
            />
          );
        })}

        {picks.length === 0 && (
          <div className="px-6 py-12 text-center">
            <div className="flex flex-col items-center gap-2">
              <BarChart3 size={24} className="text-slate-300" />
              <p className="text-xs text-slate-400 font-medium">{t("betting.no_positive_edge")}</p>
            </div>
          </div>
        )}

        {/* Show more / less */}
        {picks.length > 5 && (
          <button
            onClick={() => setExpandedPicks(expandedPicks >= picks.length ? 5 : picks.length)}
            className="w-full py-2.5 text-xs font-bold text-slate-400 hover:text-slate-600 hover:bg-slate-50 transition-all uppercase tracking-wider flex items-center justify-center gap-1"
          >
            {expandedPicks >= picks.length ? (
              <>{t("betting.hide_details")} <ChevronDown size={12} /></>
            ) : (
              <>{t("betting.show_all_count", { count: picks.length })} <ChevronRight size={12} /></>
            )}
          </button>
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
//  SLIP BUILDER (Enhanced)
// ═══════════════════════════════════════════════════════════════

function SlipBuilder({
  selections,
  onRemove,
  onClear,
}: {
  selections: SlipSelection[];
  onRemove: (idx: number) => void;
  onClear: () => void;
}) {
  const { t } = useTranslation();
  const [mode, setMode] = useState<SlipMode>("multipla");
  const [stake, setStake] = useState(50);

  // ── MULTIPLA ──
  const multiplaData = useMemo(() => {
    if (selections.length === 0) return null;
    const combinedOdds = selections.reduce((acc, s) => acc * s.market.bestOdds, 1);
    const impliedProb = (1 / combinedOdds) * 100;
    const payout = stake * combinedOdds;
    const profit = payout - stake;
    const agencyCounts: Record<string, number> = {};
    selections.forEach(s => { agencyCounts[s.market.agency] = (agencyCounts[s.market.agency] || 0) + 1; });
    const bestAgency = Object.entries(agencyCounts).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "N/D";
    return { combinedOdds: +combinedOdds.toFixed(2), impliedProb: +impliedProb.toFixed(1), payout: +payout.toFixed(2), profit: +profit.toFixed(2), bestAgency };
  }, [selections, stake]);

  // ── PORTAFOGLIO ──
  const portfolioData = useMemo(() => {
    if (selections.length === 0) return null;
    const totalAbsEdge = selections.reduce((acc, s) => acc + Math.abs(s.market.edge), 0) || 1;
    const allocations = selections.map((s) => {
      const weight = Math.max(0, s.market.edge) / totalAbsEdge;
      const allocatedStake = stake * weight;
      const potentialReturn = allocatedStake * s.market.bestOdds;
      const profit = potentialReturn - allocatedStake;
      return { pick: s.pickLabel, odds: s.market.bestOdds, edge: s.market.edge, weight: +(weight * 100).toFixed(1), allocatedStake: +allocatedStake.toFixed(2), potentialReturn: +potentialReturn.toFixed(2), profit: +profit.toFixed(2) };
    }).filter(a => a.allocatedStake > 0);
    const totalStake = allocations.reduce((a, b) => a + b.allocatedStake, 0);
    const totalReturn = allocations.reduce((a, b) => a + b.potentialReturn, 0);
    const totalProfit = allocations.reduce((a, b) => a + b.profit, 0);
    return { allocations, totalStake: +totalStake.toFixed(2), totalReturn: +totalReturn.toFixed(2), totalProfit: +totalProfit.toFixed(2) };
  }, [selections, stake]);

  // Combined Edge for the slip
  const avgEdge = useMemo(() => {
    if (selections.length === 0) return 0;
    return selections.reduce((acc, s) => acc + s.market.edge, 0) / selections.length;
  }, [selections]);

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden sticky top-4">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Wallet size={14} className="text-slate-600" />
          <h2 className="text-sm font-bold text-slate-800 uppercase tracking-tight">{t("betting.slip_builder")}</h2>
        </div>
        {selections.length > 0 && (
          <button onClick={onClear} className="text-[10px] font-medium text-rose-500 hover:text-rose-600 transition-colors flex items-center gap-1">
            <Trash2 size={12} /> {t("betting.clear_slip")}
          </button>
        )}
      </div>

      {/* Combined Edge Ribbon */}
      {selections.length > 0 && (
        <div className="px-4 py-2 bg-gradient-to-r from-indigo-50 to-violet-50 border-b border-indigo-100 flex items-center justify-between">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{t("betting.avg_edge")}</span>
          <EdgeBadge edge={avgEdge} size="md" />
        </div>
      )}

      {/* Mode Toggle */}
      <div className="px-4 py-2.5 border-b border-slate-100">
        <div className="flex rounded-lg overflow-hidden border border-slate-200 bg-slate-50 p-0.5">
          <button onClick={() => setMode("multipla")} className={`flex-1 py-1.5 text-xs font-bold uppercase tracking-wider rounded-md transition-all ${mode === "multipla" ? "bg-white text-slate-800 shadow-sm border border-slate-200" : "text-slate-500 hover:text-slate-700"}`}>
            <Calculator size={12} className="inline mr-1" /> {t("betting.multipla")}
          </button>
          <button onClick={() => setMode("portafoglio")} className={`flex-1 py-1.5 text-xs font-bold uppercase tracking-wider rounded-md transition-all ${mode === "portafoglio" ? "bg-white text-slate-800 shadow-sm border border-slate-200" : "text-slate-500 hover:text-slate-700"}`}>
            <PieChart size={12} className="inline mr-1" /> {t("betting.portfolio")}
          </button>
        </div>
      </div>

      {/* Empty State */}
      {selections.length === 0 && (
        <div className="px-4 py-10 text-center">
          <div className="w-12 h-12 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-center mx-auto mb-3">
            <Dices size={20} className="text-slate-400" />
          </div>
          <p className="text-xs font-medium text-slate-400">
            {t("betting.empty_slip_hint")}
          </p>
        </div>
      )}

      {/* Selections List */}
      {selections.length > 0 && (
        <div className="divide-y divide-slate-100 max-h-64 overflow-y-auto">
          {selections.map((sel, i) => {
            const meta = MARKET_META[sel.market.type];
            return (
              <div key={`${sel.match.id}-${sel.market.type}-${i}`} className="px-4 py-2.5 flex items-center justify-between gap-3 hover:bg-slate-50 transition-colors">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className={meta?.color ?? "text-slate-500"}>{meta?.icon}</span>
                    <span className="text-xs font-bold text-slate-700">{meta?.short}</span>
                    <span className="text-[10px] text-slate-400 font-mono tabular-nums">{sel.market.line}</span>
                  </div>
                  <p className="text-xs text-slate-600 font-medium truncate">
                    {sel.match.home} vs {sel.match.away}
                  </p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="font-mono text-xs font-bold text-indigo-600 tabular-nums">@{sel.market.bestOdds.toFixed(2)}</span>
                    <EdgeBadge edge={sel.market.edge} />
                  </div>
                </div>
                <button onClick={() => onRemove(i)} className="p-1.5 rounded-lg hover:bg-rose-50 hover:text-rose-500 text-slate-300 transition-all flex-shrink-0">
                  <Trash2 size={12} />
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Stake Input */}
      {selections.length > 0 && (
        <div className="px-4 py-3 border-t border-slate-100">
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{t("betting.stake")}</label>
            <span className="font-mono text-xs font-bold text-slate-800 tabular-nums">€{(stake ?? 50).toFixed(2)}</span>
          </div>
          <input type="range" min={5} max={500} step={5} value={stake} onChange={e => setStake(Number(e.target.value))} className="w-full accent-emerald-500 h-1.5 cursor-pointer" />
          <div className="flex justify-between text-[10px] text-slate-400 font-mono mt-0.5">
            <span className="tabular-nums">€5</span><span className="tabular-nums">€500</span>
          </div>
        </div>
      )}

      {/* MULTIPLA OUTPUT */}
      {selections.length > 0 && mode === "multipla" && multiplaData && (
        <div className="px-4 py-3 border-t border-slate-100 space-y-2">
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{t("betting.combined_odds")}</span>
              <span className="font-mono text-base font-black text-emerald-600 tabular-nums">{(multiplaData?.combinedOdds ?? 1).toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{t("betting.implied_probability")}</span>
              <span className="font-mono text-xs font-bold text-slate-700 tabular-nums">{(multiplaData?.impliedProb ?? 0).toFixed(1)}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{t("betting.potential_win")}</span>
              <span className="font-mono text-sm font-black text-slate-800 tabular-nums">€{(multiplaData?.payout ?? 0).toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{t("betting.net_profit")}</span>
              <span className={`font-mono text-sm font-black tabular-nums ${(multiplaData?.profit ?? 0) > 0 ? "text-emerald-600" : "text-rose-600"}`}>
                {(multiplaData?.profit ?? 0) > 0 ? "+" : ""}€{(multiplaData?.profit ?? 0).toFixed(2)}
              </span>
            </div>
          </div>

          <div className="bg-indigo-50 border border-indigo-200 rounded-lg px-3 py-2.5">
            <div className="flex items-start gap-2">
              <Sparkles size={12} className="text-indigo-500 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-[10px] font-bold text-indigo-700 uppercase tracking-wider">{t("betting.agency_recommendation")}</p>
                <p className="text-xs text-indigo-600 font-medium">
                  {t("betting.play_at_agency", { agency: multiplaData?.bestAgency ?? "N/D" })}
                </p>
              </div>
            </div>
          </div>

          <a
            href={(AGENCIES.find(a => a.name === multiplaData?.bestAgency)?.link) ?? AGENCIES[0]?.link ?? "#"}
            target="_blank"
            className="flex items-center justify-center gap-2 w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-bold uppercase tracking-wider transition-all"
          >
            <ExternalLink size={13} /> {t("betting.play_at")} {multiplaData?.bestAgency ?? "bookmaker"}
          </a>
        </div>
      )}

      {/* PORTAFOGLIO OUTPUT */}
      {selections.length > 0 && mode === "portafoglio" && portfolioData && (
        <div className="px-4 py-3 border-t border-slate-100 space-y-2">
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 space-y-2">
            <p className="text-[10px] font-bold uppercase tracking-wider text-amber-700 flex items-center gap-1.5">
              <PieChart size={12} /> {t("betting.optimal_allocation")} ({selections.length} {t("betting.singles")})
            </p>
            <div className="space-y-1.5">
              {portfolioData.allocations.map((a, i) => (
                <div key={i} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5 min-w-0 flex-1">
                    <span className="font-medium text-slate-700 truncate">{a.pick.split("·")[0]?.trim() ?? a.pick}</span>
                    <span className="font-mono text-slate-400 tabular-nums">@{a.odds.toFixed(2)}</span>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className="font-mono font-bold text-slate-800 tabular-nums">€{(a.allocatedStake ?? 0).toFixed(2)}</span>
                    <span className={`font-mono text-[10px] tabular-nums ${(a.edge ?? 0) > 0 ? "text-emerald-600" : "text-rose-600"}`}>
                      {(a.edge ?? 0) > 0 ? "+" : ""}{(a.edge ?? 0).toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <div className="border-t border-amber-200/60 pt-2 space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-500 font-medium">{t("betting.total_stake")}</span>
                <span className="font-mono font-bold text-slate-800 tabular-nums">€{(portfolioData.totalStake ?? 0).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-500 font-medium">{t("betting.total_return")}</span>
                <span className="font-mono font-bold text-emerald-600 tabular-nums">€{(portfolioData.totalReturn ?? 0).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-500 font-medium">{t("betting.total_profit")}</span>
                <span className={`font-mono font-bold tabular-nums ${(portfolioData.totalProfit ?? 0) > 0 ? "text-emerald-600" : "text-rose-600"}`}>
                  {(portfolioData.totalProfit ?? 0) > 0 ? "+" : ""}€{(portfolioData.totalProfit ?? 0).toFixed(2)}
                </span>
              </div>
            </div>
          </div>
          <p className="text-[10px] text-slate-400 leading-relaxed px-1">
            {t("betting.kelly_criterion")}
          </p>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
//  MARKET TABLE + MOBILE CARDS + BOTTOM SHEET FILTERS
// ═══════════════════════════════════════════════════════════════

// ── Bottom Sheet (mobile filter menu) ──────────────────────
function FilterBottomSheet({
  open,
  onClose,
  leagueFilter,
  marketFilter,
  bestPicksOnly,
  edgeFilter,
  probFilter,
  onLeagueChange,
  onMarketChange,
  onBestPicksChange,
  onEdgeFilterChange,
  onProbFilterChange,
}: {
  open: boolean;
  onClose: () => void;
  leagueFilter: LeagueId | "all";
  marketFilter: MarketType | "all";
  bestPicksOnly: boolean;
  edgeFilter: number | null;
  probFilter: number | null;
  onLeagueChange: (v: LeagueId | "all") => void;
  onMarketChange: (v: MarketType | "all") => void;
  onBestPicksChange: (v: boolean) => void;
  onEdgeFilterChange: (v: number | null) => void;
  onProbFilterChange: (v: number | null) => void;
}) {
  const { t } = useTranslation();
  const edgeOptions = [null, 2, 5, 7, 10, 15];
  const probOptions = [null, 40, 50, 60, 70, 80];

  return (
    <>
      {/* Overlay */}
      <div
        className={`fixed inset-0 z-50 bg-black/50 transition-opacity duration-300 md:hidden ${
          open ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
        onClick={onClose}
      />
      {/* Sheet */}
      <div
        className={`fixed bottom-0 left-0 right-0 z-50 bg-white rounded-t-2xl shadow-2xl transition-transform duration-300 md:hidden ${
          open ? "translate-y-0" : "translate-y-full"
        }`}
        style={{ maxHeight: "85vh" }}
      >
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white z-10">
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-tight">
            <SlidersHorizontal size={14} className="inline mr-2 text-slate-500" />
            {t("betting.filters")}
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 p-1">
            <X size={16} />
          </button>
        </div>
        <div className="p-5 space-y-5 overflow-y-auto" style={{ maxHeight: "calc(85vh - 56px)" }}>
          {/* ⭐ SOLO BEST PICKS Toggle */}
          <div>
            <label className="flex items-center justify-between cursor-pointer">
              <div className="flex items-center gap-2">
                <Star size={14} className="text-amber-500" />
                <span className="text-sm font-bold text-slate-800">{t("betting.only_best_picks")}</span>
              </div>
              <button
                onClick={() => onBestPicksChange(!bestPicksOnly)}
                className={`relative w-11 h-6 rounded-full transition-colors ${
                  bestPicksOnly ? "bg-emerald-500" : "bg-slate-200"
                }`}
              >
                <span
                  className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform ${
                    bestPicksOnly ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </label>
            <p className="text-xs text-slate-500 mt-1 ml-7">
              Solo scommesse con EDGE{'>'}7% e Probabilit&agrave;{'>'}60%
            </p>
          </div>

          <div className="h-px bg-slate-100" />

          {/* Edge Filter */}
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1.5">
              <TrendingUp size={12} /> EDGE Minimo
            </label>
            <div className="flex gap-2 flex-wrap">
              {edgeOptions.map(v => (
                <button
                  key={v ?? "all"}
                  onClick={() => onEdgeFilterChange(v)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold font-mono transition-all ${
                    edgeFilter === v
                      ? "bg-emerald-100 text-emerald-700 border border-emerald-300"
                      : "bg-slate-50 text-slate-500 border border-slate-200 hover:border-slate-300"
                  }`}
                >
                  {v === null ? "Tutti" : `≥${v}%`}
                </button>
              ))}
            </div>
          </div>

          {/* Probabilità Filter */}
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1.5">
              <Percent size={12} /> Probabilità Minima
            </label>
            <div className="flex gap-2 flex-wrap">
              {probOptions.map(v => (
                <button
                  key={v ?? "all"}
                  onClick={() => onProbFilterChange(v)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold font-mono transition-all ${
                    probFilter === v
                      ? "bg-indigo-100 text-indigo-700 border border-indigo-300"
                      : "bg-slate-50 text-slate-500 border border-slate-200 hover:border-slate-300"
                  }`}
                >
                  {v === null ? "Tutti" : `≥${v}%`}
                </button>
              ))}
            </div>
          </div>

          <div className="h-px bg-slate-100" />

          {/* League Filter */}
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1.5">
              <Trophy size={12} /> Campionato
            </label>
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={() => onLeagueChange("all")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  leagueFilter === "all"
                    ? "bg-slate-800 text-white"
                    : "bg-slate-50 text-slate-500 border border-slate-200 hover:border-slate-300"
                }`}
              >
                Tutti
              </button>
              {ALL_LEAGUES.map(l => (
                <button
                  key={l}
                  onClick={() => onLeagueChange(l)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    leagueFilter === l
                      ? "bg-slate-800 text-white"
                      : "bg-slate-50 text-slate-500 border border-slate-200 hover:border-slate-300"
                  }`}
                >
                  {l}
                </button>
              ))}
            </div>
          </div>

          {/* Market Filter */}
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1.5">
              <Target size={12} /> Mercato
            </label>
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={() => onMarketChange("all")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  marketFilter === "all"
                    ? "bg-slate-800 text-white"
                    : "bg-slate-50 text-slate-500 border border-slate-200 hover:border-slate-300"
                }`}
              >
                Tutti
              </button>
              <button onClick={() => onMarketChange("asian-handicap")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${marketFilter === "asian-handicap" ? "bg-slate-800 text-white" : "bg-slate-50 text-slate-500 border border-slate-200 hover:border-slate-300"}`}>AH</button>
              <button onClick={() => onMarketChange("player-shots")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${marketFilter === "player-shots" ? "bg-slate-800 text-white" : "bg-slate-50 text-slate-500 border border-slate-200 hover:border-slate-300"}`}>TIRI</button>
              <button onClick={() => onMarketChange("player-assists")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${marketFilter === "player-assists" ? "bg-slate-800 text-white" : "bg-slate-50 text-slate-500 border border-slate-200 hover:border-slate-300"}`}>ASSIST</button>
              <button onClick={() => onMarketChange("btts")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${marketFilter === "btts" ? "bg-slate-800 text-white" : "bg-slate-50 text-slate-500 border border-slate-200 hover:border-slate-300"}`}>GOL/GOL</button>
            </div>
          </div>

          {/* Bookie Filter (information) */}
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1.5">
              <ExternalLink size={12} /> Bookie Consigliati
            </label>
            <div className="flex gap-2 flex-wrap">
              {AGENCIES.slice(0, 4).map(a => (
                <span key={a.name} className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-50 text-slate-600 border border-slate-200">
                  {a.name}
                </span>
              ))}
            </div>
          </div>

          {/* Timing */}
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1.5">
              <Clock size={12} /> Timing Eventi
            </label>
            <p className="text-xs text-slate-500">Solo eventi futuri (filtro zombie attivo)</p>
          </div>

          <div className="h-8" />
        </div>
      </div>
    </>
  );
}

// ── Desktop Table Row ──────────────────────────────────────
function MarketRow({
  match, market, onAdd, isSelected, selectedInMatch,
}: {
  match: MatchAdvanced;
  market: MarketOdds;
  onAdd: () => void;
  isSelected: boolean;
  selectedInMatch: boolean;
}) {
  const meta = MARKET_META[market.type];

  return (
    <tr className={`border-b border-slate-100 transition-colors ${isSelected ? "bg-emerald-50/70" : "hover:bg-slate-50"}`}>
      <td className="px-3 py-3">
        <div className="flex items-center gap-2 min-w-0">
          <img src={LEAGUE_LOGOS[match.league]} alt="" className="w-5 h-5 object-contain flex-shrink-0" />
          <div className="min-w-0">
            <div className="flex items-center gap-1.5 text-sm font-semibold text-slate-800 whitespace-nowrap">
              <span className="tabular-nums">{match.home}</span>
              <span className="text-slate-400 text-xs font-normal">vs</span>
              <span className="tabular-nums">{match.away}</span>
            </div>
            <p className="text-xs text-slate-500 font-mono tabular-nums">{match.date}</p>
          </div>
        </div>
      </td>
      <td className="px-2 py-3">
        <div className="flex items-center gap-1.5">
          <span className={meta?.color ?? ""}>{meta?.icon}</span>
          <span className="text-sm font-bold text-slate-700 uppercase tracking-wider">{meta?.short}</span>
        </div>
      </td>
      <td className="px-2 py-3">
        <span className="text-sm font-bold text-slate-800 tabular-nums">{market.line}</span>
      </td>
      <td className="px-2 py-3 text-right">
        <span className="font-mono text-sm font-bold text-slate-800 tabular-nums">{((market.modelProb ?? 0) * 100).toFixed(1)}%</span>
      </td>
      <td className="px-2 py-3 text-right">
        <span className="font-mono text-sm font-bold text-indigo-600 tabular-nums">{(market.modelOdds ?? 1).toFixed(2)}</span>
      </td>
      <td className="px-2 py-3 text-right">
        <span className="font-mono text-sm font-bold text-slate-800 tabular-nums">{(market.bestOdds ?? 1).toFixed(2)}</span>
      </td>
      <td className="px-2 py-3">
        <span className="text-sm font-medium text-slate-500">{market.agency}</span>
      </td>
      <td className="px-2 py-3 text-right">
        <EdgeBadge edge={market.edge} />
      </td>
      <td className="px-2 py-3 text-center">
        <button
          onClick={onAdd}
          disabled={selectedInMatch && !isSelected}
          className={`p-1.5 rounded-lg border transition-all ${
            isSelected
              ? "bg-emerald-500 border-emerald-500 text-white shadow-sm"
              : selectedInMatch
                ? "bg-slate-100 border-slate-200 text-slate-300 cursor-not-allowed"
                : "bg-white border-slate-200 text-slate-400 hover:border-emerald-300 hover:text-emerald-500 hover:bg-emerald-50"
          }`}
          title={isSelected ? "Rimuovi" : "Aggiungi allo slip"}
        >
          {isSelected ? <Trash2 size={14} /> : <Plus size={14} />}
        </button>
      </td>
    </tr>
  );
}

// ── Mobile Card ────────────────────────────────────────────
function MarketCard({
  match, market, onAdd, isSelected, selectedInMatch, isBestPick,
}: {
  match: MatchAdvanced;
  market: MarketOdds;
  onAdd: () => void;
  isSelected: boolean;
  selectedInMatch: boolean;
  isBestPick: boolean;
}) {
  const meta = MARKET_META[market.type];
  const isTopValue = market.edge > 7 && (market.modelProb * 100) > 60;

  return (
    <div
      className={`relative rounded-xl p-4 transition-all ${
        isSelected
          ? "bg-emerald-50/80 border-2 border-emerald-400"
          : "bg-white border border-slate-200 hover:border-slate-300"
      } ${isTopValue ? "animate-pulse-border" : ""}`}
    >
      {/* TOP VALUE badge */}
      {isTopValue && (
        <div className="absolute -top-2 -right-2 z-10">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-gradient-to-r from-amber-400 to-orange-500 text-[10px] font-black text-white uppercase tracking-wider shadow-lg">
            <Star size={10} /> TOP VALUE
          </span>
        </div>
      )}

      {/* Match + Market row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <img src={LEAGUE_LOGOS[match.league]} alt="" className="w-6 h-6 object-contain flex-shrink-0" />
          <div className="min-w-0">
            <div className="text-sm font-bold text-slate-800 truncate tabular-nums">
              {match.home}
              <span className="text-slate-400 text-xs font-normal mx-1">vs</span>
              {match.away}
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-xs font-mono tabular-nums text-slate-400">{match.date}</span>
              <span className="text-[10px] text-slate-300">•</span>
              <span className="text-xs font-medium text-slate-500">{match.league}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Market details */}
      <div className="mt-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={meta?.color ?? "text-slate-500"}>{meta?.icon}</span>
          <span className="text-sm font-bold text-slate-700 uppercase tracking-wider">{meta?.short}</span>
          <span className="text-sm font-bold text-slate-800 tabular-nums">{market.line}</span>
        </div>
        <span className="text-xs font-medium text-slate-500">{market.agency}</span>
      </div>

      {/* Stats row */}
      <div className="mt-3 grid grid-cols-4 gap-2">
        <div className="flex flex-col items-center rounded-lg py-2 bg-slate-50 border border-slate-100">
          <span className="font-mono font-bold text-sm text-indigo-600 tabular-nums">{(market.bestOdds ?? 1).toFixed(2)}</span>
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Quota</span>
        </div>
        <div className="flex flex-col items-center rounded-lg py-2 bg-slate-50 border border-slate-100">
          <span className="font-mono font-bold text-sm text-slate-800 tabular-nums">{((market.modelProb ?? 0) * 100).toFixed(1)}%</span>
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Prob.</span>
        </div>
        <div className="flex flex-col items-center rounded-lg py-2 bg-slate-50 border border-slate-100">
          <span className="font-mono font-bold text-sm text-indigo-600 tabular-nums">{(market.modelOdds ?? 1).toFixed(2)}</span>
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Nostra</span>
        </div>
        <div className={`flex flex-col items-center rounded-lg py-2 border ${
          market.edge > 0 ? "bg-emerald-50 border-emerald-200" : "bg-slate-50 border-slate-100"
        }`}>
          <span className={`font-mono font-bold text-sm tabular-nums ${market.edge > 0 ? "text-emerald-600" : "text-slate-500"}`}>
            {market.edge > 0 ? "+" : ""}{market.edge.toFixed(1)}%
          </span>
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">EDGE</span>
        </div>
      </div>

      {/* CTA */}
      <button
        onClick={onAdd}
        disabled={selectedInMatch && !isSelected}
        className={`mt-3 w-full py-2.5 rounded-xl text-xs font-black uppercase tracking-wider transition-all flex items-center justify-center gap-1.5 ${
          isSelected
            ? "bg-emerald-500 text-white shadow-sm"
            : selectedInMatch
              ? "bg-slate-100 text-slate-300 cursor-not-allowed"
              : "bg-slate-800 text-white hover:bg-slate-700 active:scale-[0.98]"
        }`}
      >
        {isSelected ? (
          <><Trash2 size={13} /> RIMUOVI DALLO SLIP</>
        ) : (
          <><Plus size={13} /> PUNTA ORA</>
        )}
      </button>
    </div>
  );
}

// ── Market Table (Desktop) + Mobile Cards ─────────────────
function MarketTable({
  matches, selections, onToggle,
}: {
  matches: MatchAdvanced[];
  selections: SlipSelection[];
  onToggle: (match: MatchAdvanced, market: MarketOdds) => void;
}) {
  const { t } = useTranslation();
  const [leagueFilter, setLeagueFilter] = useState<LeagueId | "all">("all");
  const [marketFilter, setMarketFilter] = useState<MarketType | "all">("all");
  const [bestPicksOnly, setBestPicksOnly] = useState(false);
  const [edgeFilter, setEdgeFilter] = useState<number | null>(null);
  const [probFilter, setProbFilter] = useState<number | null>(null);
  const [filterSheetOpen, setFilterSheetOpen] = useState(false);

  const filtered = useMemo(() => {
    const allMarkets: { match: MatchAdvanced; market: MarketOdds }[] = [];
    for (const match of matches) {
      const markets = generateMarkets(match);
      for (const market of markets) {
        allMarkets.push({ match, market });
      }
    }

    return allMarkets.filter(({ match, market }) => {
      // League filter
      if (leagueFilter !== "all" && match.league !== leagueFilter) return false;
      // Market filter
      if (marketFilter !== "all" && market.type !== marketFilter) return false;
      // Best picks toggle
      if (bestPicksOnly && !(market.edge > 7 && (market.modelProb * 100) > 60)) return false;
      // Edge filter
      if (edgeFilter !== null && market.edge < edgeFilter) return false;
      // Probability filter
      if (probFilter !== null && (market.modelProb * 100) < probFilter) return false;
      return true;
    });
  }, [matches, leagueFilter, marketFilter, bestPicksOnly, edgeFilter, probFilter]);

  const selectedKeys = useMemo(() => new Set(selections.map(s => s.market.id)), [selections]);

  // Group by match for mobile view
  const groupedByMatch = useMemo(() => {
    const groups: { match: MatchAdvanced; markets: MarketOdds[] }[] = [];
    const matchMap = new Map<string, { match: MatchAdvanced; markets: MarketOdds[] }>();
    for (const { match, market } of filtered) {
      const key = match.id;
      if (!matchMap.has(key)) matchMap.set(key, { match, markets: [] });
      matchMap.get(key)!.markets.push(market);
    }
    return Array.from(matchMap.values());
  }, [filtered]);

  const totalBets = useMemo(() => {
    let count = 0;
    for (const match of matches) {
      count += generateMarkets(match).length;
    }
    return count;
  }, [matches]);

  const activeFilterCount = [leagueFilter !== "all", marketFilter !== "all", bestPicksOnly, edgeFilter !== null, probFilter !== null].filter(Boolean).length;

  return (
    <>
      {/* Bottom Sheet (mobile filters) */}
      <FilterBottomSheet
        open={filterSheetOpen}
        onClose={() => setFilterSheetOpen(false)}
        leagueFilter={leagueFilter}
        marketFilter={marketFilter}
        bestPicksOnly={bestPicksOnly}
        edgeFilter={edgeFilter}
        probFilter={probFilter}
        onLeagueChange={setLeagueFilter}
        onMarketChange={setMarketFilter}
        onBestPicksChange={setBestPicksOnly}
        onEdgeFilterChange={setEdgeFilter}
        onProbFilterChange={setProbFilter}
      />

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Header + Filters */}
        <div className="px-4 py-3 border-b border-slate-200">
          {/* Top row: title + mobile filter button */}
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Layers size={14} className="text-slate-600" />
              <h2 className="text-sm font-bold text-slate-800 uppercase tracking-tight">Tutti i Mercati</h2>
              <span className="text-xs font-mono text-slate-400 bg-slate-100 px-2 py-0.5 rounded-md tabular-nums">{filtered.length} risultati</span>
            </div>
            {/* Mobile filter trigger */}
            <button
              onClick={() => setFilterSheetOpen(true)}
              className="md:hidden flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 text-slate-600 text-xs font-bold"
            >
              <SlidersHorizontal size={13} />
              Filtri{activeFilterCount > 0 ? ` (${activeFilterCount})` : ""}
            </button>
          </div>

          {/* Desktop filters + ⭐ BEST PICKS toggle */}
          <div className="hidden md:flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-3">
              {/* ⭐ SOLO BEST PICKS Toggle */}
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <button
                  onClick={() => setBestPicksOnly(!bestPicksOnly)}
                  className={`relative w-9 h-5 rounded-full transition-colors ${
                    bestPicksOnly ? "bg-emerald-500" : "bg-slate-200"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow-sm transition-transform ${
                      bestPicksOnly ? "translate-x-4" : "translate-x-0"
                    }`}
                  />
                </button>
                <span className={`text-xs font-bold tracking-tight ${bestPicksOnly ? "text-amber-600" : "text-slate-500"}`}>
                  <Star size={11} className="inline mr-0.5" />
                  SOLO BEST PICKS
                </span>
              </label>

              {/* Edge quick filter chips */}
              <div className="flex items-center gap-1">
                {[null, 5, 10].map(v => (
                  <button
                    key={v ?? "all"}
                    onClick={() => setEdgeFilter(v)}
                    className={`px-2 py-1 rounded-md text-[10px] font-bold font-mono transition-all ${
                      edgeFilter === v
                        ? "bg-emerald-100 text-emerald-700 border border-emerald-300"
                        : "bg-slate-50 text-slate-400 border border-slate-200 hover:border-slate-300"
                    }`}
                  >
                    {v === null ? "Edge" : `≥${v}%`}
                  </button>
                ))}
              </div>

              {/* Prob quick filter chips */}
              <div className="flex items-center gap-1">
                {[null, 50, 70].map(v => (
                  <button
                    key={v ?? "all"}
                    onClick={() => setProbFilter(v)}
                    className={`px-2 py-1 rounded-md text-[10px] font-bold font-mono transition-all ${
                      probFilter === v
                        ? "bg-indigo-100 text-indigo-700 border border-indigo-300"
                        : "bg-slate-50 text-slate-400 border border-slate-200 hover:border-slate-300"
                    }`}
                  >
                    {v === null ? "Prob" : `≥${v}%`}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <select value={leagueFilter} onChange={e => setLeagueFilter(e.target.value as LeagueId | "all")}
                className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2 py-1.5 text-slate-700 font-medium focus:outline-none focus:ring-1 focus:ring-slate-300">
                <option value="all">Alle Ligen</option>
                {ALL_LEAGUES.map(l => <option key={l} value={l}>{l}</option>)}
              </select>
              <select value={marketFilter} onChange={e => setMarketFilter(e.target.value as MarketType | "all")}
                className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2 py-1.5 text-slate-700 font-medium focus:outline-none focus:ring-1 focus:ring-slate-300">
                <option value="all">Alle Märkte</option>
                <option value="asian-handicap">Asian Handicap (AH)</option>
                <option value="player-shots">Over Tiri Giocatore (TIRI)</option>
                <option value="player-assists">Over Assist (ASSIST)</option>
                <option value="btts">Entrambe Segnano (GOL/GOL)</option>
              </select>
            </div>
          </div>
        </div>

        {/* MOBILE: Card List */}
        <div className="md:hidden divide-y divide-slate-100">
          {groupedByMatch.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <div className="flex flex-col items-center gap-2">
                <BarChart3 size={24} className="text-slate-300" />
                <p className="text-sm text-slate-400 font-medium">{t("betting.no_market_filters")}</p>
              </div>
            </div>
          ) : (
            <div className="p-3 space-y-3">
              {groupedByMatch.map(({ match, markets }) =>
                markets.map((market) => {
                  const isSel = selectedKeys.has(market.id);
                  const hasOtherSelected = selections.some(s => s.match.id === match.id);
                  const isBestPick = market.edge > 7 && (market.modelProb * 100) > 60;
                  return (
                    <MarketCard
                      key={market.id}
                      match={match}
                      market={market}
                      onAdd={() => onToggle(match, market)}
                      isSelected={isSel}
                      selectedInMatch={hasOtherSelected && !isSel}
                      isBestPick={isBestPick}
                    />
                  );
                })
              )}
            </div>
          )}
        </div>

        {/* DESKTOP: Table */}
        <div className="hidden md:block overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="px-3 py-2.5 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">Match / Evento</th>
                <th className="px-2 py-2.5 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">Mercato</th>
                <th className="px-2 py-2.5 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">Linea</th>
                <th className="px-2 py-2.5 text-right text-[10px] font-bold uppercase tracking-wider text-slate-500">Prob.</th>
                <th className="px-2 py-2.5 text-right text-[10px] font-bold uppercase tracking-wider text-indigo-500">Nostra Quota</th>
                <th className="px-2 py-2.5 text-right text-[10px] font-bold uppercase tracking-wider text-slate-500">Quota Book</th>
                <th className="px-2 py-2.5 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">Agenzia</th>
                <th className="px-2 py-2.5 text-right text-[10px] font-bold uppercase tracking-wider text-emerald-600">EDGE</th>
                <th className="px-2 py-2.5 text-center text-[10px] font-bold uppercase tracking-wider text-slate-500 w-10"></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(({ match, market }) => {
                const isSel = selectedKeys.has(market.id);
                const hasOtherSelected = selections.some(s => s.match.id === match.id);
                return (
                  <MarketRow key={market.id} match={match} market={market}
                    onAdd={() => onToggle(match, market)}
                    isSelected={isSel} selectedInMatch={hasOtherSelected && !isSel}
                  />
                );
              })}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={9} className="px-6 py-16 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <BarChart3 size={24} className="text-slate-300" />
                      <p className="text-sm text-slate-400 font-medium">Nessun filtro di mercato</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

// ═══════════════════════════════════════════════════════════════
//  STATS RIBBON
// ═══════════════════════════════════════════════════════════════

function StatsRibbon({ selections }: { selections: SlipSelection[] }) {
  const stats = useMemo(() => {
    if (selections.length === 0) return null;
    const avgEdge = selections.reduce((acc, s) => acc + s.market.edge, 0) / selections.length;
    const posEdges = selections.filter(s => s.market.edge > 0).length;
    const marketsCount: Record<string, number> = {};
    selections.forEach(s => { marketsCount[s.market.type] = (marketsCount[s.market.type] || 0) + 1; });
    return { avgEdge: +avgEdge.toFixed(1), posEdges, total: selections.length, marketsCount };
  }, [selections]);

  if (!stats) return null;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm px-4 py-2.5 flex items-center gap-4 flex-wrap">
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Edge Medio</span>
        <EdgeBadge edge={stats.avgEdge} size="md" />
      </div>
      <div className="w-px h-5 bg-slate-200" />
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">+EV</span>
        <span className="text-xs font-mono font-bold text-emerald-600 tabular-nums">{stats.posEdges}/{stats.total}</span>
      </div>
      <div className="w-px h-5 bg-slate-200" />
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Mercati</span>
        {Object.entries(stats.marketsCount).map(([type, count]) => {
          const meta = MARKET_META[type as MarketType];
          return (
            <span key={type} className={`inline-flex items-center gap-1 text-[10px] font-mono font-bold tabular-nums ${meta?.color ?? "text-slate-600"}`}>
              {meta?.icon}{count}
            </span>
          );
        })}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
//  MAIN PAGE — VALUE BROKER
// ═══════════════════════════════════════════════════════════════

export default function ValueBrokerPage() {
  const { t } = useTranslation();
  const [selections, setSelections] = useState<SlipSelection[]>([]);
  const [topBestPicks, setTopBestPicks] = useState<BestPick[]>([]);
  const [bestPicks, setBestPicks]       = useState<BestPick[]>([]);
  const [bollettes, setBollettes]       = useState<Bolletta[]>([]);

  useEffect(() => {
    const apiBase = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000") + "/api/v1";
    async function loadTopPicks() {
      try {
        const res = await fetch(`${apiBase}/betting/top-picks`);
        if (!res.ok) return;
        const data: { top_picks: ApiTopPick[] } = await res.json();
        const picks = (data.top_picks ?? []).map(mapApiPickToBestPick);
        setTopBestPicks(picks.slice(0, 3));
        setBestPicks(picks);
        setBollettes(deriveBollettesFromPicks(picks));
      } catch {
        // leave state empty — hero sections render nothing gracefully
      }
    }
    loadTopPicks();
  }, []);

  const handleToggle = useCallback((match: MatchAdvanced, market: MarketOdds) => {
    const id = market.id;
    setSelections(prev => {
      const idx = prev.findIndex(s => s.market.id === id);
      if (idx >= 0) return prev.filter((_, i) => i !== idx);
      const hasMatch = prev.some(s => s.match.id === match.id);
      if (hasMatch) return prev;
      const pickLabel = `${match.home} vs ${match.away} · ${market.label}`;
      return [...prev, { match, market, pickLabel }];
    });
  }, []);

  /** Add entire bolletta to builder */
  const handleAddBolletta = useCallback((picks: SlipSelection[]) => {
    setSelections(prev => {
      const existing = new Set(prev.map(s => s.market.id));
      const newPicks = picks.filter(p => !existing.has(p.market.id));
      if (newPicks.length === 0) return prev;
      return [...prev, ...newPicks];
    });
  }, []);

  const handleRemove = useCallback((idx: number) => {
    setSelections(prev => prev.filter((_, i) => i !== idx));
  }, []);

  const handleClear = useCallback(() => {
    setSelections([]);
  }, []);

  // Zombie filter: on mount, drop selections whose match is in the past
  useEffect(() => {
    const now = new Date();
    setSelections(prev => prev.filter(s => !s.match.match_datetime || new Date(s.match.match_datetime) > now));
  }, []);

  return (
    <div className="relative min-h-screen text-slate-800 font-sans pb-16">
      {/* Full-page background */}
      <div className="fixed inset-0 z-0">
        <Image src="/betting/hero.png" alt="" fill priority className="object-cover" />
        <div className="absolute inset-0 bg-black/50" />
      </div>

      {/* Disclaimer Banner */}
      <div className="w-full bg-rose-500 py-2.5 px-4 shadow-sm sticky top-0 z-[60]">
        <p className="text-center text-[10px] font-bold uppercase tracking-[0.25em] text-white italic">
          {t("betting.warning")}
        </p>
      </div>

      {/* PAGE HEADER */}
      <div className="relative z-10 border-b border-slate-200 bg-white shadow-sm">
        <div className="max-w-[1750px] mx-auto px-4 md:px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center shadow-sm">
              <Crosshair size={16} className="text-white" />
            </div>
            <div>
              <h1 className="font-black text-xl tracking-tight text-slate-800 uppercase">{t("betting.title")}</h1>
              <p className="text-[10px] text-slate-500 tracking-[0.15em] uppercase font-medium">
                {t("betting.model_subtitle")}
              </p>
            </div>
            <div className="ml-auto flex items-center gap-3 text-xs">
              <div className="flex items-center gap-1.5 text-slate-500">
                <Zap size={13} className="text-amber-500" />
                <span className="text-[10px] font-medium">{bestPicks.length} {t("betting.future_events")}</span>
              </div>
              <div className="flex items-center gap-1.5 text-slate-500">
                <Activity size={13} className="text-emerald-500" />
                <span className="text-[10px] font-medium">{selections.length} {t("betting.selections")}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* LAB SUB-NAVIGATION — Analytics Tools */}
      <div className="relative z-10 border-b border-slate-700/50 bg-[#0d1b2a]">
        <div className="max-w-[1750px] mx-auto px-4 md:px-6 py-2 flex items-center gap-3">
          <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500 mr-1 hidden sm:inline">
            Labs
          </span>
          <Link
            href="/betting/lab1"
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold tracking-wider uppercase rounded-md border border-slate-700 text-slate-300 hover:text-white hover:border-cyan-500 hover:bg-cyan-500/10 transition-all duration-200"
          >
            <Brain size={13} className="text-cyan-400" />
            Lab 1: Market Analytics
          </Link>
          <Link
            href="/betting/lab2"
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold tracking-wider uppercase rounded-md border border-slate-700 text-slate-300 hover:text-white hover:border-violet-500 hover:bg-violet-500/10 transition-all duration-200"
          >
            <Layers size={13} className="text-violet-400" />
            Lab 2: The Matrix
          </Link>
        </div>
      </div>

      <div className="relative z-10 max-w-[1750px] mx-auto px-4 md:px-6 mt-6">
        {/* TOP 3 BEST PICKS + BOLLETTE PRONTE — elevated over background */}
        <div className="relative z-10 w-full max-w-7xl mx-auto px-4 py-8">
          {/* TOP 3 BEST PICKS — Hero Section (Edge × Probabilità) */}
          <BestPicksHeroSection picks={topBestPicks} onAddToSlip={handleToggle} />

          {/* Bollette Pronte (Hero) */}
          <BollettePronteSection bollettes={bollettes} onAddToBuilder={handleAddBolletta} />
        </div>

        {/* MAIN LAYOUT: 8 cols left | 4 cols right */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* LEFT — Best Picks + Market Table */}
          <main className="lg:col-span-8 space-y-4">
            {/* Best PICKS & AI VERDICT */}
            <BestPicksSection
              picks={bestPicks}
              selections={selections}
              onToggle={handleToggle}
            />

            {/* Stats Ribbon */}
            <StatsRibbon selections={selections} />

            {/* Detailed Market Table (collapsible) */}
            <details className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden" open>
              <summary className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-slate-600 cursor-pointer hover:text-slate-800 transition-colors flex items-center gap-2">
                <Layers size={14} /> Tabella Mercati Completa
                <ChevronRight size={12} className="ml-auto" />
              </summary>
              <div className="border-t border-slate-100">
                <MarketTable matches={[]} selections={selections} onToggle={handleToggle} />
              </div>
            </details>

            {/* Strategy Legend */}
            <details className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <summary className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-slate-600 cursor-pointer hover:text-slate-800 transition-colors flex items-center gap-2">
                <Gauge size={14} /> Metodologia di Calcolo
                <ChevronRight size={12} className="ml-auto" />
              </summary>
              <div className="px-4 pb-4 border-t border-slate-100 pt-3 space-y-3 text-xs text-slate-600 leading-relaxed">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="bg-indigo-50/50 border border-indigo-100 rounded-lg p-3">
                    <p className="font-bold text-indigo-700 uppercase tracking-wider text-[10px] mb-1">Asian Handicap (AH)</p>
                    <p>Calcolato sul delta xG tra le due squadre. Maggiore è il divario di xG, più alta è la linea di handicap.</p>
                  </div>
                  <div className="bg-amber-50/50 border border-amber-100 rounded-lg p-3">
                    <p className="font-bold text-amber-700 uppercase tracking-wider text-[10px] mb-1">Over Tiri Giocatore (TIRI)</p>
                    <p>Basato sulla media tiri/90 del giocatore corretta per il PPDA avversario. PPDA alto = pressing basso.</p>
                  </div>
                  <div className="bg-sky-50/50 border border-sky-100 rounded-lg p-3">
                    <p className="font-bold text-sky-700 uppercase tracking-wider text-[10px] mb-1">Over Assist (ASSIST)</p>
                    <p>Combina xA e Key Passes in un indice di creatività composito.</p>
                  </div>
                  <div className="bg-rose-50/50 border border-rose-100 rounded-lg p-3">
                    <p className="font-bold text-rose-700 uppercase tracking-wider text-[10px] mb-1">Entrambe Segnano (GOL/GOL)</p>
                    <p>Stimato su Deep Passes concessi da entrambe le squadre: più passaggi nella propria trequarti = più gol.</p>
                  </div>
                </div>
                <p className="text-[10px] text-slate-400 italic">
                  * Tutte le quote modello sono calcolate su metriche avanzate. I dati reali verranno integrati con endpoint dedicati.
                </p>
              </div>
            </details>
          </main>

          {/* RIGHT — Slip Builder (sticky) */}
          <aside className="lg:col-span-4 space-y-4">
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm px-4 py-2.5 flex items-center gap-3">
              <Hash size={14} className="text-slate-400" />
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{t("betting.slots", { used: selections.length, total: 12 })}</span>
              <div className="flex-1 h-1.5 rounded-full overflow-hidden bg-slate-100">
                <div className="h-full rounded-full transition-all duration-500 bg-gradient-to-r from-slate-600 to-slate-800" style={{ width: `${(selections.length / 12) * 100}%` }} />
              </div>
            </div>

            {/* Slip Builder */}
            <SlipBuilder selections={selections} onRemove={handleRemove} onClear={handleClear} />

            <div className="bg-white rounded-xl border border-slate-200 shadow-sm px-4 py-3">
              <div className="flex items-start gap-2">
                <ShieldAlert size={14} className="text-slate-400 mt-0.5 flex-shrink-0" />
                <div className="text-[10px] text-slate-500 leading-relaxed">
                  {t("betting.value_broker_intro")}
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
