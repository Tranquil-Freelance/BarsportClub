"use client";
import React, { useState } from "react";
import { motion } from "framer-motion";
import { useTalentRadar } from "../hooks/useTalentRadar";
import { TalentCategory, LeagueKey, LEAGUE_LABELS, CATEGORY_META, PlayerDNA } from "../lib/scoutApi";

const CATEGORIES: TalentCategory[] = ["diamonds", "moneyball", "engine", "unlucky", "overperformers"];
const LEAGUES: LeagueKey[] = ["serie_a", "pl", "bundesliga", "liga", "ligue1"];

const POS_OPTS = [
  { id: "ALL", label: "Tutti" },
  { id: "FW",  label: "Attaccanti" },
  { id: "AMC", label: "Trequartisti" },
  { id: "MC",  label: "Centrocampisti" },
  { id: "DC",  label: "Difensori" },
];

function getHeroValue(p: PlayerDNA, category: TalentCategory): string {
  switch (category) {
    case "diamonds":       return p.p90.xgchain?.toFixed(3) ?? "—";
    case "moneyball":      return p.p90.xgbuildup?.toFixed(3) ?? "—";
    case "engine":         return p.p90.xgbuildup?.toFixed(3) ?? "—";
    case "unlucky":        return p.totals.xg?.toFixed(2) ?? "—";
    case "overperformers": return ((p.totals.goals ?? 0) - (p.totals.xg ?? 0)).toFixed(2);
  }
}

function TalentCard({ player, category, rank, onLoad }: {
  player: PlayerDNA; category: TalentCategory; rank: number; onLoad: (n: string) => void;
}) {
  const meta = CATEGORY_META[category];
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: rank * 0.03 }}
      onClick={() => onLoad(player.name)}
      className="bg-white rounded-2xl shadow-sm border border-slate-100 p-5 cursor-pointer transition-all
                 hover:-translate-y-1 hover:shadow-md relative overflow-hidden"
      style={{ borderLeft: `3px solid ${meta.color}` }}
    >
      <div className="absolute top-4 right-4 w-7 h-7 rounded-full bg-slate-50 border border-slate-100 flex items-center justify-center">
        <span className="text-[10px] font-black text-slate-400">#{rank + 1}</span>
      </div>

      <div className="mb-3">
        <div className="text-[9px] text-slate-400 uppercase tracking-widest mb-0.5">{meta.heroMetric}</div>
        <div className="font-black text-[26px] leading-none" style={{ color: meta.color, fontFamily: "var(--font-oswald)" }}>
          {getHeroValue(player, category)}
        </div>
      </div>

      <h4 className="font-black text-[17px] uppercase tracking-tight text-[#334155] leading-tight mb-0.5 pr-8"
        style={{ fontFamily: "var(--font-oswald)" }}>{player.name}</h4>
      <p className="text-[9px] text-slate-400 uppercase font-bold mb-4">{player.team} · {player.position}</p>

      <div className="grid grid-cols-3 gap-1.5">
        {[
          { l: "xG/90",     v: player.p90.xg?.toFixed(3),       c: "#FF2A6D" },
          { l: "xA/90",     v: player.p90.xa?.toFixed(3),       c: "#00D1FF" },
          { l: "OIS",       v: player.scores.OIS.toFixed(3),    c: "#10B981" },
        ].map(({ l, v, c }) => (
          <div key={l} className="bg-slate-50 rounded-lg p-2 text-center border border-slate-100">
            <div className="font-black text-[12px] leading-none" style={{ color: c, fontFamily: "var(--font-oswald)" }}>{v}</div>
            <div className="text-[8px] text-slate-400 uppercase mt-0.5">{l}</div>
          </div>
        ))}
      </div>

      <div className="mt-3 pt-3 border-t border-slate-100 flex justify-between items-center">
        <span className="text-[9px] text-slate-400 uppercase font-bold">{Math.round(player.minutes)} min</span>
        <span className="text-[9px] font-black text-[#334155]" style={{ fontFamily: "var(--font-oswald)" }}>
          {player.games} partite
        </span>
      </div>
    </motion.div>
  );
}

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-5 animate-pulse">
      {Array.from({ length: 12 }).map((_, i) => (
        <div key={i} className="bg-slate-100 rounded-2xl h-56" />
      ))}
    </div>
  );
}

export default function DiscoverTab({ onLoad }: { onLoad: (name: string) => void }) {
  const [category, setCategory] = useState<TalentCategory>("diamonds");
  const [league, setLeague]     = useState<LeagueKey>("serie_a");
  const [pos, setPos]           = useState("ALL");

  const { talents, isLoading } = useTalentRadar(category, league, pos);
  const meta = CATEGORY_META[category];

  return (
    <div className="flex gap-6 min-h-[600px]">
      {/* Sidebar */}
      <div className="w-48 shrink-0 bg-[#0A192F] rounded-2xl overflow-hidden self-start">
        {CATEGORIES.map(cat => {
          const m = CATEGORY_META[cat];
          const active = cat === category;
          return (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className="w-full flex items-center gap-3 px-4 py-4 text-left border-b border-white/5 last:border-0 transition-all"
              style={{ background: active ? m.color + "18" : "transparent" }}
            >
              <span className="text-xl shrink-0">{m.emoji}</span>
              <div>
                <div className="font-black text-[11px] uppercase tracking-wide leading-tight"
                  style={{ color: active ? m.color : "#64748b", fontFamily: "var(--font-oswald)" }}>
                  {m.label}
                </div>
                {active && (
                  <div className="text-[9px] text-slate-500 mt-0.5 leading-tight">{m.desc}</div>
                )}
              </div>
              {active && <div className="ml-auto w-1 h-6 rounded-full" style={{ background: m.color }} />}
            </button>
          );
        })}
      </div>

      {/* Main content */}
      <div className="flex-1 min-w-0">
        {/* Header controls */}
        <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
          <div>
            <h2 className="text-2xl font-black uppercase tracking-tighter text-[#334155] flex items-center gap-2"
              style={{ fontFamily: "var(--font-oswald)" }}>
              <span>{meta.emoji}</span>
              <span>{meta.label}</span>
            </h2>
            <p className="text-slate-400 text-[10px] uppercase tracking-[0.2em] mt-1">{meta.desc}</p>
          </div>

          {/* League + position filters */}
          <div className="flex flex-wrap gap-2">
            <div className="flex gap-1">
              {LEAGUES.map(l => (
                <button key={l} onClick={() => setLeague(l)}
                  className="text-[9px] font-black uppercase tracking-wide px-2.5 py-1.5 rounded-lg transition-all border"
                  style={{
                    background: league === l ? meta.color : "#fff",
                    color:      league === l ? "#fff" : "#64748b",
                    borderColor:league === l ? meta.color : "#e2e8f0",
                    fontFamily: "var(--font-oswald)",
                  }}>
                  {l === "serie_a" ? "ITA" : l === "bundesliga" ? "GER" : l === "liga" ? "ESP" : l === "ligue1" ? "FRA" : "ENG"}
                </button>
              ))}
            </div>
            <div className="flex gap-1">
              {POS_OPTS.map(f => (
                <button key={f.id} onClick={() => setPos(f.id)}
                  className="text-[9px] font-black uppercase tracking-wide px-2.5 py-1.5 rounded-lg transition-all border"
                  style={{
                    background:  pos === f.id ? "#334155" : "#fff",
                    color:       pos === f.id ? "#fff" : "#64748b",
                    borderColor: pos === f.id ? "#334155" : "#e2e8f0",
                    fontFamily:  "var(--font-oswald)",
                  }}>
                  {f.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Player grid */}
        {isLoading ? (
          <SkeletonGrid />
        ) : talents.length === 0 ? (
          <div className="flex items-center justify-center py-24 text-slate-400 font-black uppercase text-[13px] tracking-widest"
            style={{ fontFamily: "var(--font-oswald)" }}>
            Nessun talento trovato
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-5">
            {talents.map((t, i) => (
              <TalentCard key={`${t.name}-${i}`} player={t} category={category} rank={i} onLoad={onLoad} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
