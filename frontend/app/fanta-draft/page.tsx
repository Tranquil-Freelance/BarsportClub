"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Activity, Crosshair, TrendingUp,
  ChevronLeft, ChevronRight, ChevronDown,
} from "lucide-react";
import { clsx } from "clsx";
import { useTranslation } from "react-i18next";
import "../i18n/config";

import StartSitView from "@/app/components/fanta/StartSitView";
import MatchupView  from "@/app/components/fanta/MatchupView";
import AuctionView  from "@/app/components/fanta/AuctionView";

// ─── Types ────────────────────────────────────────────────────────────────────

export type TabId       = "start-sit" | "matchup" | "auction";
export type LeagueId    = "Serie A" | "Premier League" | "La Liga" | "Bundesliga" | "Ligue 1";
export type AuctionMode = "iniziale" | "riparazione";

// ─── All 5 leagues now ───────────────────────────────────────────────────────

const TABS: { id: TabId; label: string; icon: React.ReactNode; color: string }[] = [
  { id: "start-sit", label: "Start / Sit",  icon: <Activity    size={18} />, color: "#00f0ff" },
  { id: "matchup",   label: "Matchup",       icon: <Crosshair   size={18} />, color: "#ccff00" },
  { id: "auction",   label: "Auction Brain", icon: <TrendingUp  size={18} />, color: "#ff2a4b" },
];

/** All 5 European top leagues */
export const LEAGUES: LeagueId[] = [
  "Serie A",
  "Premier League",
  "La Liga",
  "Bundesliga",
  "Ligue 1",
];

// ─── League logo map ──────────────────────────────────────────────────────────

export const LEAGUE_LOGOS: Record<LeagueId, string> = {
  "Serie A":        "/leagues/seriea.png",
  "Premier League": "/leagues/premierleague.png",
  "La Liga":        "/leagues/laliga.png",
  "Bundesliga":     "/leagues/bundesliga.png",
  "Ligue 1":        "/leagues/ligue1.png",
};

// Render per-tab — now passes league + year down so every view is silo-aware
function renderView(tab: TabId, auctionMode: AuctionMode, league: LeagueId, year: number | null): React.ReactNode {
  const season = auctionMode === "iniziale" ? "2025" : "2025";
  switch (tab) {
    case "start-sit": return <StartSitView league={league} />;
    case "matchup":   return <MatchupView   league={league} year={year ?? undefined} />;
    case "auction":   return <AuctionView   season={season} mode={auctionMode} league={league} year={year ?? undefined} />;
  }
}

// ─── League Selector ──────────────────────────────────────────────────────────

function LeagueSelector({ value, onChange }: { value: LeagueId; onChange: (l: LeagueId) => void }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative z-[100]">
      <button
        onClick={() => setOpen(v => !v)}
        className="flex items-center gap-2 px-3.5 py-1.5 rounded-full text-[9px] font-black uppercase tracking-widest transition-all"
        style={{ background: "rgba(0,0,0,0.04)", border: "1px solid #e2e8f0", color: "#1E293B" }}
      >
        <img src={LEAGUE_LOGOS[value]} alt="" className="w-4 h-4 object-contain rounded-full" />
        <span>{value}</span>
        <ChevronDown
          size={10}
          style={{
            transform: open ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 200ms",
            color: "#64748b",
          }}
        />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.97 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 top-full mt-2 rounded-xl overflow-hidden z-50 border shadow-2xl"
            style={{ minWidth: 200, background: "#ffffff", borderColor: "#e2e8f0" }}
          >
            {LEAGUES.map(l => (
              <button
                key={l}
                onClick={() => { onChange(l); setOpen(false); }}
                className="w-full text-left px-4 py-3 text-[9px] font-black uppercase tracking-widest transition-colors flex items-center gap-3"
                style={{ color: l === value ? "#FF2A6D" : "#64748b", background: l === value ? "rgba(255,42,109,0.06)" : "transparent" }}
                onMouseEnter={e => { if (l !== value) (e.currentTarget as HTMLElement).style.background = "rgba(0,0,0,0.03)"; }}
                onMouseLeave={e => { if (l !== value) (e.currentTarget as HTMLElement).style.background = "transparent"; }}
              >
                <img src={LEAGUE_LOGOS[l]} alt="" className="w-5 h-5 object-contain rounded-full" />
                {l}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── Year Dropdown ────────────────────────────────────────────────────────────

function YearDropdown({ value, years, onChange }: {
  value: number | null;
  years: number[];
  onChange: (y: number) => void;
}) {
  const [open, setOpen] = useState(false);
  if (!years.length) return null;
  return (
    <div className="relative">
      <button
        onClick={() => setOpen(v => !v)}
        className="flex items-center gap-2 px-3.5 py-1.5 rounded-full text-[9px] font-black uppercase tracking-widest transition-all"
        style={{ background: "rgba(0,0,0,0.04)", border: "1px solid #e2e8f0", color: "#1E293B" }}
      >
        <span>{value ?? "—"}</span>
        <ChevronDown size={10} style={{ transform: open ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 200ms", color: "#64748b" }} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.97 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 top-full mt-2 rounded-xl overflow-hidden z-50 border shadow-2xl"
            style={{ minWidth: 90, background: "#ffffff", borderColor: "#e2e8f0" }}
          >
            {years.map(y => (
              <button
                key={y}
                onClick={() => { onChange(y); setOpen(false); }}
                className="w-full text-left px-4 py-3 text-[9px] font-black uppercase tracking-widest transition-colors"
                style={{ color: y === value ? "#FF2A6D" : "#64748b", background: y === value ? "rgba(255,42,109,0.06)" : "transparent" }}
                onMouseEnter={e => { if (y !== value) (e.currentTarget as HTMLElement).style.background = "rgba(0,0,0,0.03)"; }}
                onMouseLeave={e => { if (y !== value) (e.currentTarget as HTMLElement).style.background = "transparent"; }}
              >
                {y}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── Auction Mode Toggle ──────────────────────────────────────────────────────

function AuctionModeToggle({
  value, onChange,
}: {
  value: AuctionMode;
  onChange: (m: AuctionMode) => void;
}) {
  const { t } = useTranslation();
  const auctionModeLabels: Record<AuctionMode, string> = {
    iniziale: t("fanta.auction_initial"),
    riparazione: t("fanta.auction_repair"),
  };
  return (
    <div
      className="flex items-center overflow-hidden rounded-full flex-shrink-0"
      style={{ background: "rgba(0,0,0,0.04)", border: "1px solid #e2e8f0" }}
    >
      <span
        className="pl-3 pr-2 text-[8px] font-mono font-black uppercase tracking-[0.2em] flex-shrink-0"
        style={{ color: "#f87171" }}
      >
        {t("fanta.auction")}
      </span>
      {(["iniziale", "riparazione"] as AuctionMode[]).map((m, i) => (
        <button
          key={m}
          onClick={() => onChange(m)}
          className="px-3 py-1.5 text-[9px] font-mono font-black uppercase tracking-widest transition-all"
          style={{
            background: value === m ? "#FF2A6D" : "transparent",
            color: value === m ? "#fff" : "#64748b",
            borderRadius: i === 0 ? "0" : "0 9999px 9999px 0",
          }}
        >
          {auctionModeLabels[m]}
        </button>
      ))}
    </div>
  );
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────

const TAB_LABEL_KEYS: Record<TabId, string> = {
  "start-sit": "fanta.tab_start_sit",
  "matchup":   "fanta.tab_matchup",
  "auction":   "fanta.tab_auction_brain",
};

function Sidebar({
  active, onChange, expanded, onToggle,
}: {
  active: TabId;
  onChange: (t: TabId) => void;
  expanded: boolean;
  onToggle: () => void;
}) {
  const { t } = useTranslation();
  return (
    <aside
      className="flex flex-col h-full flex-shrink-0 overflow-y-auto transition-all duration-300"
      style={{
        width: expanded ? 224 : 72,
        background: "#ffffff",
        borderRight: "1px solid #e2e8f0",
      }}
    >
      {/* Logo */}
      <div
        className="flex items-center justify-center h-14 px-4 flex-shrink-0"
        style={{ borderBottom: "1px solid #e2e8f0" }}
      >
        {expanded ? (
          <span
            className="font-black uppercase tracking-tighter leading-none"
            style={{ fontFamily: "'Oswald', var(--font-oswald, sans-serif)", fontSize: "1.05rem", color: "#1E293B" }}
          >
            FANTA<span style={{ color: "#FF2A6D" }}>IQ</span>
          </span>
        ) : (
          <span
            className="font-black uppercase"
            style={{ fontFamily: "'Oswald', var(--font-oswald, sans-serif)", fontSize: "0.9rem", color: "#FF2A6D" }}
          >
            FQ
          </span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex flex-col gap-1 p-2 flex-1">
        {TABS.map(tab => {
          const isActive = active === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onChange(tab.id)}
              title={!expanded ? t(TAB_LABEL_KEYS[tab.id]) : undefined}
              className={clsx(
                "relative flex items-center gap-3 rounded-xl transition-all duration-150 select-none",
                expanded ? "px-4 py-3" : "px-0 py-3 justify-center",
              )}
              style={{
                background: isActive ? `${tab.color}18` : "transparent",
                color: isActive ? tab.color : "#64748b",
              }}
            >
              {isActive && (
                <motion.div
                  layoutId="sidebar-indicator"
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-6 rounded-full"
                  style={{ background: tab.color, boxShadow: `0 0 8px ${tab.color}, 0 0 16px ${tab.color}60` }}
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                />
              )}
              <span style={{ color: isActive ? tab.color : "#94a3b8" }}>
                {tab.icon}
              </span>
              {expanded && (
                <span className="text-[10px] font-black uppercase tracking-[0.15em] leading-none whitespace-nowrap">
                  {t(TAB_LABEL_KEYS[tab.id])}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={onToggle}
        className="flex items-center justify-center h-12 flex-shrink-0 transition-colors"
        style={{ borderTop: "1px solid #e2e8f0", color: "#94a3b8" }}
        onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "rgba(0,0,0,0.03)"}
        onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "transparent"}
        title={expanded ? t("fanta.compress") : t("fanta.expand")}
      >
        {expanded ? <ChevronLeft size={14} /> : <ChevronRight size={14} />}
      </button>
    </aside>
  );
}

// ─── Topbar ───────────────────────────────────────────────────────────────────

function Topbar({
  activeTab, league, onLeagueChange, auctionMode, onAuctionModeChange,
  year, years, onYearChange,
}: {
  activeTab: TabId;
  league: LeagueId;
  onLeagueChange: (l: LeagueId) => void;
  auctionMode: AuctionMode;
  onAuctionModeChange: (m: AuctionMode) => void;
  year: number | null;
  years: number[];
  onYearChange: (y: number) => void;
}) {
  const { t } = useTranslation();
  const tab = TABS.find(tab => tab.id === activeTab)!;

  return (
    <header
      className="h-14 flex items-center px-6 gap-4 flex-shrink-0 relative z-[100]"
      style={{
        background: "rgba(255,255,255,0.92)",
        borderBottom: "1px solid #e2e8f0",
        backdropFilter: "blur(12px)",
      }}
    >
      {/* View label */}
      <div className="flex items-center gap-2.5 flex-1 min-w-0">
        <span style={{ color: tab.color }}>{tab.icon}</span>
        <span
          className="font-black uppercase tracking-tighter leading-none"
          style={{ fontFamily: "'Oswald', var(--font-oswald, sans-serif)", fontSize: "1rem", color: "#1E293B" }}
        >
          {t(TAB_LABEL_KEYS[tab.id])}
        </span>
        <div
          className="h-px flex-1 min-w-4 max-w-24"
          style={{ background: `linear-gradient(90deg, ${tab.color}30, transparent)` }}
        />
      </div>

      {/* Auction mode toggle — only when auction tab is active */}
      <AnimatePresence>
        {activeTab === "auction" && (
          <motion.div
            initial={{ opacity: 0, scale: 0.92, x: 8 }}
            animate={{ opacity: 1, scale: 1, x: 0 }}
            exit={{ opacity: 0, scale: 0.92, x: 8 }}
            transition={{ duration: 0.15 }}
          >
            <AuctionModeToggle value={auctionMode} onChange={onAuctionModeChange} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Year + League selectors */}
      <YearDropdown value={year} years={years} onChange={onYearChange} />
      <LeagueSelector value={league} onChange={onLeagueChange} />
    </header>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function FantaDraftPage() {
  const [activeTab,        setActiveTab]        = useState<TabId>("start-sit");
  const [sidebarExpanded,  setSidebarExpanded]  = useState(false);
  const [league,           setLeague]           = useState<LeagueId>("Serie A");
  const [auctionMode,      setAuctionMode]      = useState<AuctionMode>("iniziale");
  const [year,             setYear]             = useState<number | null>(null);
  const [seasons,          setSeasons]          = useState<number[]>([]);

  useEffect(() => {
    fetch(`http://localhost:8000/api/fanta/seasons?league=${encodeURIComponent(league)}`)
      .then(r => r.ok ? r.json() : [])
      .then((data: number[]) => {
        setSeasons(data);
        if (data.length > 0) setYear(data[0]);
      })
      .catch(() => {});
  }, [league]);

  return (
    <div suppressHydrationWarning className="h-[calc(100vh-80px)] overflow-hidden flex" style={{ background: "#F1F5F9", color: "#1E293B" }}>

      <Sidebar
        active={activeTab}
        onChange={setActiveTab}
        expanded={sidebarExpanded}
        onToggle={() => setSidebarExpanded(v => !v)}
      />

      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">

        <Topbar
          activeTab={activeTab}
          league={league}
          onLeagueChange={setLeague}
          auctionMode={auctionMode}
          onAuctionModeChange={setAuctionMode}
          year={year}
          years={seasons}
          onYearChange={setYear}
        />

        <main className="flex-1 overflow-y-auto p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={`${activeTab}-${league}-${year}`}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.18, ease: "easeOut" }}
            >
              {renderView(activeTab, auctionMode, league, year)}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
