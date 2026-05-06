"use client";

import { useState, useMemo } from "react";

export interface ShotData {
  x: number;
  y: number;
  xg: number;
  result: string;
  situation: string;
  minute: number;
}

// Color by situation (matches Understat palette)
const SIT_COLOR: Record<string, string> = {
  OpenPlay:       "#60a5fa",
  FromCorner:     "#f59e0b",
  SetPiece:       "#ec4899",
  DirectFreekick: "#22c55e",
  Penalty:        "#a78bfa",
  Unknown:        "#6b7280",
};

const W = 620;
const H = 380;

// Understat: X=0(own goal)→1(opp goal), Y=0(left)→1(right)
// We show attacking half horizontally: goal on LEFT
// X=1(goal) → svgX=0, X=0.5(halfway) → svgX=W
// Y=0(left) → svgY=0, Y=1(right) → svgY=H
function toSvg(ux: number, uy: number): [number, number] {
  const svgX = Math.max(0, (1 - ux) * 2 * W);
  const svgY = uy * H;
  return [svgX, svgY];
}

function shotR(xg: number) {
  return Math.max(3, Math.min(20, 3 + xg * 36));
}

// Convert Understat Y-range to SVG Y coordinates
function yRange(y0: number, y1: number): [number, number] {
  return [y0 * H, y1 * H];
}

// Convert Understat X to SVG X
function xCoord(ux: number): number {
  return (1 - ux) * 2 * W;
}

interface Props {
  shots: ShotData[];
  colorBy?: "situation" | "result";
}

const RESULT_COLOR: Record<string, string> = {
  Goal:    "#10B981",
  Saved:   "#EF4444",
  Missed:  "#6b7280",
  Blocked: "#f59e0b",
};

export default function ShotMapHorizontal({ shots, colorBy = "situation" }: Props) {
  const [hovered, setHovered] = useState<ShotData | null>(null);
  const [mode, setMode]       = useState<"situation" | "result">(colorBy);

  const goals  = useMemo(() => shots.filter(s => s.result === "Goal"), [shots]);
  const others = useMemo(() => shots.filter(s => s.result !== "Goal"), [shots]);

  function getColor(s: ShotData) {
    if (mode === "result") return RESULT_COLOR[s.result] ?? "#6b7280";
    return SIT_COLOR[s.situation] ?? SIT_COLOR.Unknown;
  }

  // Pitch markings (all Understat coord-based)
  const penaltyAreaY   = yRange(0.21, 0.79);
  const penaltyAreaX   = xCoord(0.83);        // left edge of penalty area in SVG
  const sixYardY       = yRange(0.365, 0.635);
  const sixYardX       = xCoord(0.942);
  const goalY          = yRange(0.446, 0.554);
  const [penSpotX, penSpotY] = toSvg(0.88, 0.5);
  const [centreX, centreY]   = toSvg(0.5, 0.5);

  const legendEntries = mode === "situation"
    ? Object.entries(SIT_COLOR).filter(([k]) => k !== "Unknown")
    : Object.entries(RESULT_COLOR);

  return (
    <div className="space-y-3">
      {/* Controls */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          {(["situation", "result"] as const).map(m => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all border ${
                mode === m
                  ? "bg-[#10B981]/15 border-[#10B981]/40 text-[#10B981]"
                  : "bg-[#0d1220] border-slate-800 text-slate-600 hover:text-slate-400"
              }`}
            >
              By {m}
            </button>
          ))}
        </div>
        {/* Stats pills */}
        <div className="flex gap-3 text-xs font-mono">
          {[
            { label: "Sh",  val: shots.length,                                  color: "text-slate-400" },
            { label: "G",   val: goals.length,                                  color: "text-[#10B981]" },
            { label: "xG",  val: shots.reduce((s,v)=>s+v.xg,0).toFixed(2),     color: "text-[#60a5fa]" },
          ].map(p => (
            <span key={p.label} className="bg-[#0d1220] border border-slate-800 rounded px-2 py-0.5 flex gap-1.5">
              <span className="text-slate-600 uppercase">{p.label}</span>
              <span className={`font-bold ${p.color}`}>{p.val}</span>
            </span>
          ))}
        </div>
      </div>

      {/* SVG Pitch */}
      <div className="relative overflow-hidden rounded-2xl border border-slate-800/60">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          width="100%"
          style={{ maxWidth: W, display: "block", margin: "0 auto" }}
          className="bg-[#0d1a0f]"
        >
          {/* Grass stripes */}
          {Array.from({ length: 10 }).map((_, i) => (
            <rect key={i} x={i * (W / 10)} y={0} width={W / 10} height={H}
              fill={i % 2 === 0 ? "#0d1a0f" : "#0f1e11"} />
          ))}

          {/* Pitch boundary */}
          <rect x={2} y={2} width={W - 4} height={H - 4}
            fill="none" stroke="#2d5235" strokeWidth={1.5} />

          {/* Halfway line (right edge = halfway) */}
          <line x1={W} y1={2} x2={W} y2={H - 2} stroke="#1e3a22" strokeWidth={1.5} />

          {/* Centre circle arc (right side, partial half-circle) */}
          <ellipse cx={W} cy={centreY} rx={W * 0.18} ry={H * 0.3}
            fill="none" stroke="#1e3a22" strokeWidth={1.2}
            strokeDasharray="4 3" />

          {/* Penalty area */}
          <rect
            x={0} y={penaltyAreaY[0]}
            width={penaltyAreaX} height={penaltyAreaY[1] - penaltyAreaY[0]}
            fill="none" stroke="#2d5235" strokeWidth={1.5}
          />

          {/* 6-yard box */}
          <rect
            x={0} y={sixYardY[0]}
            width={sixYardX} height={sixYardY[1] - sixYardY[0]}
            fill="none" stroke="#2d5235" strokeWidth={1.2}
          />

          {/* Goal */}
          <rect
            x={-6} y={goalY[0]}
            width={8} height={goalY[1] - goalY[0]}
            fill="none" stroke="#4ade80" strokeWidth={2}
          />

          {/* Penalty spot */}
          <circle cx={penSpotX} cy={penSpotY} r={3} fill="#2d5235" />

          {/* Penalty arc */}
          <path
            d={`M ${penaltyAreaX} ${penaltyAreaY[0] + (penaltyAreaY[1]-penaltyAreaY[0])*0.3}
                A ${H * 0.2} ${H * 0.2} 0 0 0
                ${penaltyAreaX} ${penaltyAreaY[0] + (penaltyAreaY[1]-penaltyAreaY[0])*0.7}`}
            fill="none" stroke="#2d5235" strokeWidth={1.2}
          />

          {/* Non-goal shots (rendered under goals) */}
          {others.map((s, i) => {
            const [sx, sy] = toSvg(s.x, s.y);
            const r = shotR(s.xg);
            const color = getColor(s);
            return (
              <circle key={`o${i}`}
                cx={sx} cy={sy} r={r}
                fill={color} fillOpacity={0.6}
                stroke={color} strokeWidth={0.8}
                style={{ cursor: "pointer", filter: `drop-shadow(0 0 2px ${color}50)` }}
                onMouseEnter={() => setHovered(s)}
                onMouseLeave={() => setHovered(null)}
              />
            );
          })}

          {/* Goals on top with stronger glow */}
          {goals.map((s, i) => {
            const [sx, sy] = toSvg(s.x, s.y);
            const r = shotR(s.xg);
            const color = mode === "result" ? "#10B981" : getColor(s);
            return (
              <circle key={`g${i}`}
                cx={sx} cy={sy} r={r}
                fill={color} fillOpacity={0.9}
                stroke="#fff" strokeWidth={1.2}
                style={{ cursor: "pointer", filter: `drop-shadow(0 0 5px ${color}90)` }}
                onMouseEnter={() => setHovered(s)}
                onMouseLeave={() => setHovered(null)}
              />
            );
          })}
        </svg>

        {/* Tooltip */}
        {hovered && (
          <div className="absolute top-3 right-3 bg-[#0a0e17]/95 border border-slate-700/60 rounded-xl p-3 text-xs shadow-2xl backdrop-blur-sm z-10 min-w-[160px]">
            <div className="flex items-center gap-2 mb-1.5">
              <div className="w-2 h-2 rounded-full"
                style={{ background: mode === "result" ? (RESULT_COLOR[hovered.result]??"#6b7280") : (SIT_COLOR[hovered.situation]??SIT_COLOR.Unknown) }} />
              <span className="font-bold text-white">{hovered.result}</span>
            </div>
            <div className="space-y-0.5 font-mono text-slate-400">
              <div>xG: <span className="text-white">{hovered.xg.toFixed(3)}</span></div>
              <div>Sit: <span className="text-slate-300">{hovered.situation}</span></div>
              <div>Min: <span className="text-slate-300">{hovered.minute}&apos;</span></div>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3">
        {legendEntries.map(([label, color]) => (
          <div key={label} className="flex items-center gap-1.5 text-[11px]">
            <div className="w-2.5 h-2.5 rounded-full border border-white/10" style={{ background: color }} />
            <span className="text-slate-500">{label}</span>
          </div>
        ))}
        <div className="flex items-center gap-1.5 text-[11px] ml-2">
          <div className="w-5 h-5 rounded-full border-2 border-white/40 bg-transparent flex-shrink-0" />
          <span className="text-slate-600">goal (white border)</span>
        </div>
      </div>
    </div>
  );
}
