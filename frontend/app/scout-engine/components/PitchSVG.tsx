"use client";
import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Shot } from "../lib/scoutApi";

const toSvgCoords = (X: number, Y: number) => ({
  cx: Math.round(Y * 1000) / 10,
  cy: Math.max(-2, Math.min(74, Math.round((1 - X) / 0.6 * 70 * 10) / 10)),
});

const resultStyle = (result: string): { fill: string; stroke: string; opacity: number } => {
  switch (result) {
    case "Goal":        return { fill: "#FFD700", stroke: "#FFD700", opacity: 1 };
    case "SavedShot":   return { fill: "#3B82F6", stroke: "#60A5FA", opacity: 0.75 };
    case "BlockedShot": return { fill: "#6366F1", stroke: "#818CF8", opacity: 0.70 };
    case "ShotOnPost":  return { fill: "#F59E0B", stroke: "#FCD34D", opacity: 0.85 };
    default:            return { fill: "#EF4444", stroke: "#F87171", opacity: 0.60 };
  }
};

export default function PitchSVG({ shots }: { shots: Shot[] }) {
  const [hovered, setHovered] = useState<(Shot & { cx: number; cy: number }) | null>(null);

  const goals    = shots.filter(s => s.result === "Goal");
  const nonGoals = shots.filter(s => s.result !== "Goal");
  const totalXG  = shots.reduce((acc, s) => acc + (s.xG || 0), 0);
  const avgXG    = shots.length ? totalXG / shots.length : 0;

  return (
    <div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
        {[
          { l: "Gol",       v: goals.length,       c: "#FFD700" },
          { l: "xG Totale", v: totalXG.toFixed(2), c: "#FF2A6D" },
          { l: "Tiri Tot.", v: shots.length,        c: "#334155" },
          { l: "xG/Tiro",  v: avgXG.toFixed(3),    c: "#94A3B8" },
        ].map(({ l, v, c }) => (
          <div key={l} className="bg-white rounded-lg px-3 py-2 text-center shadow-sm border border-slate-100">
            <div className="font-black text-[18px] leading-none" style={{ color: c, fontFamily: "var(--font-oswald)" }}>{v}</div>
            <div className="text-[9px] text-slate-400 uppercase tracking-widest mt-1">{l}</div>
          </div>
        ))}
      </div>

      <div className="relative rounded-xl overflow-hidden" style={{ background: "#163D25" }}>
        <svg viewBox="0 0 100 70" style={{ width: "100%", display: "block" }} preserveAspectRatio="xMidYMid meet">
          <defs>
            <pattern id="pitch-stripes" width="100" height="10" patternUnits="userSpaceOnUse">
              <rect width="100" height="5" fill="rgba(255,255,255,0.018)" />
            </pattern>
            <filter id="goal-glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="1.8" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
            <radialGradient id="danger-zone" cx="50%" cy="5%" r="45%">
              <stop offset="0%"   stopColor="#FF2A6D" stopOpacity="0.18" />
              <stop offset="100%" stopColor="#FF2A6D" stopOpacity="0" />
            </radialGradient>
          </defs>

          <rect x="0" y="0" width="100" height="70" fill="#163D25" />
          <rect x="0" y="0" width="100" height="70" fill="url(#pitch-stripes)" />

          <g stroke="rgba(255,255,255,0.45)" strokeWidth="0.45" fill="none">
            <rect x="2" y="0" width="96" height="70" />
            <line x1="2" y1="70" x2="98" y2="70" strokeWidth="0.6" stroke="rgba(255,255,255,0.5)" />
            <rect x="20.4" y="0" width="59.2" height="19.2" />
            <rect x="36.5" y="0" width="27" height="6.4" />
            <rect x="44.6" y="0" width="10.8" height="2.8" stroke="rgba(255,255,255,0.8)" strokeWidth="0.7" />
            <circle cx="50" cy="12.8" r="0.7" fill="rgba(255,255,255,0.6)" stroke="none" />
            <path d="M 33 19.2 A 11 10.5 0 0 1 67 19.2" />
          </g>

          <rect x="20.4" y="0" width="59.2" height="19.2" fill="url(#danger-zone)" />

          {nonGoals.map((s, i) => {
            const { cx, cy } = toSvgCoords(s.X, s.Y);
            const { fill, stroke, opacity } = resultStyle(s.result);
            const r = 1.0 + s.xG * 1.5;
            return (
              <circle key={`ng-${i}`} cx={cx} cy={cy} r={r}
                fill={fill} fillOpacity={opacity} stroke={stroke} strokeWidth={0.4} strokeOpacity={0.9}
                style={{ cursor: "pointer" }}
                onMouseEnter={() => setHovered({ ...s, cx, cy })}
                onMouseLeave={() => setHovered(null)}
              />
            );
          })}

          {goals.map((s, i) => {
            const { cx, cy } = toSvgCoords(s.X, s.Y);
            return (
              <text key={`g-${i}`} x={cx} y={cy} textAnchor="middle" dominantBaseline="central"
                fontSize="5" style={{ cursor: "pointer", userSelect: "none" }}
                filter="url(#goal-glow)"
                onMouseEnter={() => setHovered({ ...s, cx, cy })}
                onMouseLeave={() => setHovered(null)}>
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

        <AnimatePresence>
          {hovered && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}
              className="absolute top-3 right-3 rounded-xl p-4 min-w-[210px] pointer-events-none z-20"
              style={{
                background: "rgba(7,13,26,0.97)",
                border: "1px solid rgba(255,255,255,0.1)",
                borderLeft: `3px solid ${hovered.result === "Goal" ? "#FFD700" : "#FF2A6D"}`,
                backdropFilter: "blur(8px)",
              }}
            >
              <div className="flex items-center gap-2 mb-3 pb-2 border-b border-white/10">
                <div className="w-3 h-3 rounded-full" style={{ background: resultStyle(hovered.result).fill }} />
                <span className="font-black text-[15px] uppercase"
                  style={{ color: hovered.result === "Goal" ? "#FFD700" : "#E2E8F0", fontFamily: "var(--font-oswald)" }}>
                  {hovered.result === "Goal" ? "⚽ GOAL!" : hovered.result}
                </span>
              </div>
              {[
                { l: "xG",     v: hovered.xG?.toFixed(3) },
                { l: "Minuto", v: `${hovered.minute}'` },
                { l: "Azione", v: hovered.situation },
                { l: "Tipo",   v: hovered.shotType || "—" },
              ].map(({ l, v }) => (
                <div key={l} className="flex justify-between items-center mb-1.5">
                  <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wide">{l}</span>
                  <span className="text-[11px] font-black"
                    style={{ color: l === "xG" ? "#FF2A6D" : "#E2E8F0", fontFamily: "var(--font-oswald)", fontSize: l === "xG" ? 15 : 11 }}>
                    {v}
                  </span>
                </div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="flex items-center gap-5 mt-3 flex-wrap">
        {[
          { color: "#FFD700", label: `Gol (${goals.length})` },
          { color: "#3B82F6", label: "Parato" },
          { color: "#6366F1", label: "Bloccato" },
          { color: "#F59E0B", label: "Palo" },
          { color: "#EF4444", label: "Fuori" },
        ].map(({ color, label }) => (
          <div key={label} className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
            <span className="text-[10px] text-slate-400 font-bold uppercase">{label}</span>
          </div>
        ))}
        <span className="text-[10px] text-slate-500 ml-auto">● dimensione = xG</span>
      </div>
    </div>
  );
}
