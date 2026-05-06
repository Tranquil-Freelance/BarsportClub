"use client";
import React from "react";
import { motion } from "framer-motion";
import { Target } from "lucide-react";
import { usePlayerDNA } from "../hooks/usePlayerDNA";
import SearchHub from "./SearchHub";
import PitchSVG from "./PitchSVG";
import LaserRadar, { RadarPlayer } from "./LaserRadar";

const SERIE_A_PILLS = [
  { name: "Rafael Leão",      team: "Milan"      },
  { name: "Lautaro Martínez", team: "Inter"      },
  { name: "Kenan Yıldız",     team: "Juventus"   },
  { name: "Paulo Dybala",     team: "Roma"       },
  { name: "Ademola Lookman",  team: "Atalanta"   },
  { name: "Mateo Retegui",    team: "Atalanta"   },
  { name: "Marcus Thuram",    team: "Inter"      },
  { name: "Romelu Lukaku",    team: "Napoli"     },
  { name: "Moise Kean",       team: "Fiorentina" },
  { name: "Nicolò Barella",   team: "Inter"      },
];

const SCORE_CFG = [
  { key: "PIR",  label: "Player Impact Rating",    max: 0.5,  accent: "#FF2A6D" },
  { key: "OIS",  label: "Offensive Impact Score",  max: 0.6,  accent: "#FF2A6D" },
  { key: "CII",  label: "Creative Influence Index",max: 0.4,  accent: "#00D1FF" },
  { key: "FES",  label: "Finishing Efficiency",    max: 2.0,  accent: "#10B981" },
  { key: "AIR",  label: "Attacking Involvement",   max: 0.02, accent: "#00D1FF" },
  { key: "BCS",  label: "Buildup Contribution",    max: 0.015,accent: "#F59E0B" },
  { key: "PPI",  label: "Player Potential Index",  max: 0.5,  accent: "#F59E0B" },
  { key: "MVGI", label: "Market Value Gap",        max: 1.0,  accent: "#94A3B8" },
];

function scoreColor(pct: number, accent: string) {
  if (pct > 0.7) return accent;
  if (pct > 0.4) return accent + "BB";
  return "#94A3B8";
}

function Skeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="bg-slate-100 rounded-2xl h-32 border-l-[6px] border-l-slate-200" />
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        {Array.from({ length: 8 }).map((_, i) => <div key={i} className="bg-slate-100 rounded-xl h-24" />)}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 bg-slate-100 rounded-2xl h-[400px]" />
        <div className="lg:col-span-5 flex flex-col gap-5">
          <div className="bg-slate-100 rounded-2xl h-56" />
          <div className="bg-slate-100 rounded-2xl flex-1 min-h-[180px]" />
        </div>
      </div>
    </div>
  );
}

export default function TargetTab({
  playerName,
  onLoad,
}: {
  playerName: string | null;
  onLoad: (n: string) => void;
}) {
  const { dna, radar, shots, isLoading } = usePlayerDNA(playerName);

  if (!playerName) {
    return (
      <SearchHub
        onSelect={onLoad}
        context="DNA Target · Profilo Offensivo Completo"
        pills={SERIE_A_PILLS}
      />
    );
  }

  if (isLoading) return <Skeleton />;

  if (!dna) {
    return (
      <div className="flex flex-col items-center justify-center py-24">
        <p className="text-slate-400 text-[13px] font-bold uppercase tracking-wide">
          Nessun dato trovato per &ldquo;{playerName}&rdquo;
        </p>
        <button onClick={() => onLoad("")} className="mt-4 text-[11px] text-[#FF2A6D] font-black uppercase hover:underline">
          ← Nuova ricerca
        </button>
      </div>
    );
  }

  const radarPlayer: RadarPlayer | null = radar
    ? { name: dna.name, color: "#FF2A6D", axes: radar.axes }
    : null;

  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="bg-white shadow-sm border border-slate-100 rounded-2xl px-8 py-6 flex flex-wrap items-center gap-8 border-l-[6px] border-l-[#FF2A6D]">
        <div className="flex-1 min-w-0">
          <p className="text-[#FF2A6D] text-[10px] font-black uppercase tracking-[0.3em] mb-1">{dna.position}</p>
          <h2 className="text-[#334155] font-black text-5xl uppercase tracking-tighter leading-none truncate"
            style={{ fontFamily: "var(--font-oswald)" }}>{dna.name}</h2>
          <p className="text-slate-400 text-[12px] uppercase tracking-widest mt-1 font-bold">{dna.team}</p>
        </div>
        <div className="flex gap-8 shrink-0">
          {[
            { l: "Presenze", v: dna.games },
            { l: "Minuti",   v: `${dna.minutes}'` },
            { l: "Gol",      v: Math.round(dna.totals.goals ?? 0) },
            { l: "Assist",   v: Math.round(dna.totals.assists ?? 0) },
          ].map(({ l, v }) => (
            <div key={l} className="text-center">
              <div className="text-[#334155] font-black text-2xl leading-none" style={{ fontFamily: "var(--font-oswald)" }}>{v}</div>
              <div className="text-slate-400 text-[9px] uppercase tracking-widest mt-1">{l}</div>
            </div>
          ))}
        </div>
        <div className="text-center border-l border-slate-100 pl-8 shrink-0">
          <p className="text-[#FF2A6D] text-[10px] font-black uppercase tracking-[0.3em] mb-1">PIR</p>
          <div className="text-[#FF2A6D] font-black text-4xl leading-none" style={{ fontFamily: "var(--font-oswald)" }}>
            {dna.scores.PIR.toFixed(3)}
          </div>
          <p className="text-slate-400 text-[9px] uppercase tracking-widest mt-1">Impact Rating</p>
        </div>
      </div>

      {/* Score tiles */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        {SCORE_CFG.map(({ key, label, max, accent }, idx) => {
          const val = (dna.scores as any)[key] ?? 0;
          const pct = Math.min(1, Math.max(0, val / max));
          const col = scoreColor(pct, accent);
          return (
            <motion.div key={key}
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              className="bg-white border border-slate-100 rounded-xl p-4 text-center shadow-sm"
            >
              <div className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-2">{key}</div>
              <div className="font-black text-xl leading-none mb-2" style={{ color: col, fontFamily: "var(--font-oswald)" }}>
                {val.toFixed(key === "AIR" || key === "BCS" ? 5 : key === "FES" ? 2 : 3)}
              </div>
              <div className="h-1 bg-slate-100 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }} animate={{ width: `${pct * 100}%` }}
                  transition={{ duration: 0.8, delay: 0.3 }}
                  className="h-full rounded-full" style={{ background: col }}
                />
              </div>
              <div className="text-[8px] text-slate-400 mt-2 leading-tight">{label}</div>
            </motion.div>
          );
        })}
      </div>

      {/* Shot map + radar + p90 */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 bg-white border border-slate-100 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <Target size={15} className="text-[#FF2A6D]" />
            <h3 className="font-black text-[11px] uppercase tracking-[0.2em] text-[#334155]"
              style={{ fontFamily: "var(--font-oswald)" }}>Shot Map Intelligence</h3>
          </div>
          <PitchSVG shots={shots} />
        </div>

        <div className="lg:col-span-5 flex flex-col gap-5">
          {/* Radar */}
          <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm">
            <h3 className="font-black text-[11px] uppercase tracking-[0.2em] text-[#334155] mb-1"
              style={{ fontFamily: "var(--font-oswald)" }}>Scouting Radar Model</h3>
            {radarPlayer ? (
              <>
                <p className="text-slate-400 text-[9px] uppercase tracking-widest mb-3">
                  Percentili · {radar!.pool_size} giocatori · stesso ruolo
                </p>
                <LaserRadar players={[radarPlayer]} height={220} />
                <div className="mt-3 space-y-1.5">
                  {Object.entries(radar!.axes).map(([k, ax]) => (
                    <div key={k} className="flex justify-between items-center">
                      <span className="text-[10px] text-slate-400 font-medium">{ax.label}</span>
                      <div className="flex items-center gap-3">
                        <span className="text-[10px] text-slate-400">{ax.value.toFixed(3)}</span>
                        <span className="text-[11px] font-black w-9 text-right"
                          style={{ color: ax.percentile > 70 ? "#FF2A6D" : ax.percentile > 40 ? "#00D1FF" : "#94A3B8" }}>
                          {ax.percentile}°
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="py-8 text-center text-slate-400 text-[11px] uppercase">Dati radar non disponibili</div>
            )}
          </div>

          {/* P90 table */}
          <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm">
            <h3 className="font-black text-[11px] uppercase tracking-[0.2em] text-[#334155] mb-4"
              style={{ fontFamily: "var(--font-oswald)" }}>Metriche Per 90'</h3>
            <div className="space-y-2">
              {[
                { l: "xG / 90",       v: dna.p90.xg?.toFixed(3),        c: "#FF2A6D" },
                { l: "xA / 90",       v: dna.p90.xa?.toFixed(3),        c: "#00D1FF" },
                { l: "Goals / 90",    v: dna.p90.goals?.toFixed(2),     c: "#10B981" },
                { l: "Shots / 90",    v: dna.p90.shots?.toFixed(2),     c: "#94A3B8" },
                { l: "Key Passes/90", v: dna.p90.key_passes?.toFixed(2),c: "#94A3B8" },
                { l: "xGChain / 90",  v: dna.p90.xgchain?.toFixed(3),   c: "#F59E0B" },
                { l: "xGBuildup/90",  v: dna.p90.xgbuildup?.toFixed(3), c: "#F59E0B" },
              ].map(({ l, v, c }) => (
                <div key={l} className="flex justify-between items-center py-1.5 border-b border-slate-50 last:border-0">
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
