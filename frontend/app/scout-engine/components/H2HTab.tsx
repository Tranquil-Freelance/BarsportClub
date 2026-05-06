"use client";
import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Users } from "lucide-react";
import { usePlayerDNA } from "../hooks/usePlayerDNA";
import { PlayerDNA, RadarData } from "../lib/scoutApi";
import SearchHub from "./SearchHub";
import LaserRadar, { RadarPlayer } from "./LaserRadar";

const SCORE_ROWS = [
  { key: "PIR",  label: "Player Impact Rating" },
  { key: "OIS",  label: "Offensive Impact Score" },
  { key: "CII",  label: "Creative Influence" },
  { key: "FES",  label: "Finishing Efficiency" },
] as const;

const P90_ROWS = [
  { key: "xg",  label: "xG / 90" },
  { key: "xa",  label: "xA / 90" },
] as const;

function toRadarPlayer(dna: PlayerDNA, radar: RadarData, color: string): RadarPlayer {
  return {
    name: dna.name,
    color,
    axes: radar.axes,
  };
}

function SlotCard({
  name, color, label, onClear,
}: { name: string | null; color: string; label: string; onClear: () => void }) {
  const { dna, isLoading } = usePlayerDNA(name);

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden"
      style={{ borderTop: `4px solid ${color}` }}>
      <div className="px-6 py-4 flex justify-between items-center border-b border-slate-100">
        <span className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400">{label}</span>
        {name && (
          <button onClick={onClear} className="flex items-center gap-1 text-[10px] text-slate-400 hover:text-red-500 transition-colors font-bold uppercase">
            <X size={12} /> Rimuovi
          </button>
        )}
      </div>

      {isLoading && (
        <div className="p-6 animate-pulse space-y-3">
          <div className="h-8 bg-slate-100 rounded w-3/4" />
          <div className="h-4 bg-slate-100 rounded w-1/2" />
          <div className="grid grid-cols-2 gap-3 mt-4">
            {Array.from({ length: 6 }).map((_, i) => <div key={i} className="h-14 bg-slate-100 rounded-xl" />)}
          </div>
        </div>
      )}

      {!isLoading && dna && (
        <div className="p-6">
          <div className="font-black text-3xl uppercase tracking-tighter mb-1"
            style={{ color, fontFamily: "var(--font-oswald)" }}>{dna.name}</div>
          <div className="text-[11px] text-slate-400 uppercase font-bold mb-6">{dna.team} · {dna.position}</div>
          <div className="grid grid-cols-2 gap-3">
            {[
              { l: "PIR",   v: dna.scores.PIR.toFixed(4) },
              { l: "OIS",   v: dna.scores.OIS.toFixed(4) },
              { l: "xG/90", v: dna.p90.xg?.toFixed(3) },
              { l: "xA/90", v: dna.p90.xa?.toFixed(3) },
              { l: "FES",   v: dna.scores.FES.toFixed(3) },
              { l: "CII",   v: dna.scores.CII.toFixed(4) },
            ].map(({ l, v }) => (
              <div key={l} className="bg-slate-50 rounded-xl p-3 flex justify-between items-center border border-slate-100">
                <span className="text-[9px] text-slate-400 uppercase font-bold">{l}</span>
                <span className="font-black text-[14px]" style={{ color, fontFamily: "var(--font-oswald)" }}>{v}</span>
              </div>
            ))}
          </div>
          <div className="grid grid-cols-3 gap-3 mt-3 border-t border-slate-100 pt-3">
            {[
              { l: "Presenze", v: dna.games },
              { l: "Minuti",   v: dna.minutes },
              { l: "Pos",      v: dna.position },
            ].map(({ l, v }) => (
              <div key={l} className="text-center">
                <div className="font-black text-[16px] text-[#334155]" style={{ fontFamily: "var(--font-oswald)" }}>{v}</div>
                <div className="text-[9px] text-slate-400 uppercase tracking-wide">{l}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!isLoading && !dna && !name && (
        <div className="p-10 flex flex-col items-center justify-center min-h-[280px]">
          <Users size={36} className="mb-3" style={{ color: color + "30" }} />
          <span className="text-[12px] font-black uppercase tracking-widest text-slate-400">In attesa</span>
          <span className="text-[10px] text-slate-400 mt-1">Cerca il giocatore qui sopra</span>
        </div>
      )}
    </div>
  );
}

function ComparisonTable({ dna1, dna2, color1, color2 }: {
  dna1: PlayerDNA; dna2: PlayerDNA; color1: string; color2: string;
}) {
  const rows: { label: string; v1: number; v2: number }[] = [
    { label: "PIR",    v1: dna1.scores.PIR, v2: dna2.scores.PIR },
    { label: "OIS",    v1: dna1.scores.OIS, v2: dna2.scores.OIS },
    { label: "CII",    v1: dna1.scores.CII, v2: dna2.scores.CII },
    { label: "FES",    v1: dna1.scores.FES, v2: dna2.scores.FES },
    { label: "xG/90",  v1: dna1.p90.xg,    v2: dna2.p90.xg },
    { label: "xA/90",  v1: dna1.p90.xa,    v2: dna2.p90.xa },
  ];

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-100">
        <h3 className="font-black text-[11px] uppercase tracking-[0.2em] text-[#334155]"
          style={{ fontFamily: "var(--font-oswald)" }}>Confronto Metriche</h3>
      </div>
      <div className="divide-y divide-slate-50">
        {rows.map(({ label, v1, v2 }, i) => {
          const w1 = v1 >= v2;
          const w2 = v2 > v1;
          return (
            <div key={label} className={`flex items-center px-6 py-3 ${i % 2 === 0 ? "bg-slate-50/50" : ""}`}>
              <div className="w-24 shrink-0">
                <span className={`inline-block px-2 py-0.5 rounded-md text-[11px] font-black`}
                  style={{ background: w1 ? color1 + "20" : "transparent", color: w1 ? color1 : "#94a3b8" }}>
                  {v1.toFixed(4)}
                </span>
              </div>
              <div className="flex-1 text-center">
                <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wide">{label}</span>
              </div>
              <div className="w-24 shrink-0 text-right">
                <span className={`inline-block px-2 py-0.5 rounded-md text-[11px] font-black`}
                  style={{ background: w2 ? color2 + "20" : "transparent", color: w2 ? color2 : "#94a3b8" }}>
                  {v2.toFixed(4)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function H2HTab() {
  const [name1, setName1] = useState<string | null>(null);
  const [name2, setName2] = useState<string | null>(null);
  const { dna: dna1, radar: radar1 } = usePlayerDNA(name1);
  const { dna: dna2, radar: radar2 } = usePlayerDNA(name2);

  const color1 = "#00D1FF";
  const color2 = "#FF5C00";

  const radarPlayers: RadarPlayer[] = [
    ...(dna1 && radar1 ? [toRadarPlayer(dna1, radar1, color1)] : []),
    ...(dna2 && radar2 ? [toRadarPlayer(dna2, radar2, color2)] : []),
  ];

  return (
    <div className="space-y-6">
      {/* Dual search bars */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.3em] mb-2"
            style={{ color: color1 }}>Challenger 1</p>
          <SearchHub onSelect={setName1} placeholder="Cerca primo giocatore…" size="sm" />
        </div>
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.3em] mb-2"
            style={{ color: color2 }}>Challenger 2</p>
          <SearchHub onSelect={setName2} placeholder="Cerca secondo giocatore…" size="sm" />
        </div>
      </div>

      {/* Slot cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SlotCard name={name1} color={color1} label="CHALLENGER 1" onClear={() => setName1(null)} />
        <SlotCard name={name2} color={color2} label="CHALLENGER 2" onClear={() => setName2(null)} />
      </div>

      {/* Laser radar */}
      <AnimatePresence>
        {radarPlayers.length > 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <h3 className="font-black text-[11px] uppercase tracking-[0.2em] text-[#334155] mb-1"
              style={{ fontFamily: "var(--font-oswald)" }}>
              Radar Comparativo — Percentili Posizione
            </h3>
            <p className="text-[9px] text-slate-400 uppercase tracking-widest mb-4">
              xG · Goals · xA · xGChain · Shots per 90' rispetto al ruolo
            </p>
            <LaserRadar players={radarPlayers} height={380} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Comparison table */}
      <AnimatePresence>
        {dna1 && dna2 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <ComparisonTable dna1={dna1} dna2={dna2} color1={color1} color2={color2} />
          </motion.div>
        )}
      </AnimatePresence>

      {!name1 && !name2 && (
        <div className="flex flex-col items-center justify-center py-24 text-slate-300">
          <div className="w-20 h-20 rounded-full bg-slate-100 flex items-center justify-center mb-6">
            <Users size={32} className="text-slate-300" />
          </div>
          <h3 className="text-xl font-black text-slate-300 mb-2 tracking-tight">H2H Duel Engine</h3>
          <p className="text-slate-400 text-sm text-center max-w-sm">
            Cerca due giocatori con le barre qui sopra — i radar percentili saranno sovrapposti con effetto laser.
          </p>
        </div>
      )}
    </div>
  );
}
