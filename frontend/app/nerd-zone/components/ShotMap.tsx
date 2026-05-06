"use client";

import { useState } from "react";

interface Shot {
  x: number;
  y: number;
  xg: number;
  result: string;
  situation: string;
  minute: number;
}

interface Props {
  shots: Shot[];
}

const RESULT_COLOR: Record<string, string> = {
  Goal:    "#10B981",
  Saved:   "#EF4444",
  Missed:  "#6B7280",
  Blocked: "#F59E0B",
};

// Understat coords: X=0(own goal)→1(opp goal), Y=0(left)→1(right)
// We render the attacking half only (X ≥ 0.5), rotated vertically.
// SVG viewport: width=300, height=420. Penalty area drawn schematically.
const W = 300;
const H = 420;
// Understat: X=0(own goal)→1(opp goal), Y=0(left)→1(right)
// SVG: goal at BOTTOM (svgY=H), halfway line at TOP (svgY=0)
// We show the attacking half only: X 0.5→1.0 maps to svgY 0→H
function toSvg(ux: number, uy: number): [number, number] {
  const svgX = uy * W;
  const svgY = (ux - 0.5) * 2 * H;
  return [svgX, svgY];
}

function shotRadius(xg: number): number {
  return Math.max(4, Math.min(18, 4 + xg * 40));
}

export default function ShotMap({ shots }: Props) {
  const [hovered, setHovered] = useState<Shot | null>(null);

  const goals  = shots.filter(s => s.result === "Goal");
  const others = shots.filter(s => s.result !== "Goal");

  return (
    <div className="relative flex flex-col items-center gap-3">
      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-[11px]">
        {Object.entries(RESULT_COLOR).map(([label, color]) => (
          <div key={label} className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-full border border-white/20" style={{ background: color }} />
            <span className="text-slate-400">{label}</span>
          </div>
        ))}
        <div className="flex items-center gap-1.5 ml-2">
          <div className="flex items-center gap-0.5">
            <div className="w-2.5 h-2.5 rounded-full bg-slate-600 border border-white/10" />
            <div className="w-4 h-4 rounded-full bg-slate-600 border border-white/10" />
          </div>
          <span className="text-slate-500">size = xG</span>
        </div>
      </div>

      {/* Pitch */}
      <div className="relative" style={{ width: W, height: H }}>
        <svg
          width={W}
          height={H}
          viewBox={`0 0 ${W} ${H}`}
          className="bg-[#0d1a0f] rounded-xl border border-slate-800/60"
        >
          {/* Grass stripes */}
          {Array.from({ length: 8 }).map((_, i) => (
            <rect
              key={i}
              x={0} y={i * (H / 8)}
              width={W} height={H / 8}
              fill={i % 2 === 0 ? "#0d1a0f" : "#0f1e11"}
            />
          ))}

          {/* Halfway line (top of half-pitch) */}
          <line x1={0} y1={0} x2={W} y2={0} stroke="#1e3a22" strokeWidth={1.5} />

          {/* Touchlines */}
          <rect x={2} y={2} width={W - 4} height={H - 4}
                fill="none" stroke="#2d5235" strokeWidth={1.5} />

          {/* Penalty area (83% line, Y 21%–79%) */}
          {(() => {
            const [x1] = toSvg(0.83, 0.21);
            const [x2] = toSvg(0.83, 0.79);
            const [, y1] = toSvg(0.83, 0.5);
            return (
              <rect
                x={x1} y={y1}
                width={x2 - x1} height={H - y1 - 2}
                fill="none" stroke="#2d5235" strokeWidth={1.5}
              />
            );
          })()}

          {/* 6-yard box (94% line, Y 30%–70%) */}
          {(() => {
            const [x1] = toSvg(0.94, 0.3);
            const [x2] = toSvg(0.94, 0.7);
            const [, y1] = toSvg(0.94, 0.5);
            return (
              <rect
                x={x1} y={y1}
                width={x2 - x1} height={H - y1 - 2}
                fill="none" stroke="#2d5235" strokeWidth={1.2}
              />
            );
          })()}

          {/* Goal (Y 45%–55%, at bottom) */}
          <rect
            x={W * 0.42} y={H - 8}
            width={W * 0.16} height={10}
            fill="none" stroke="#4ade80" strokeWidth={2}
            rx={1}
          />

          {/* Penalty spot */}
          {(() => {
            const [sx, sy] = toSvg(0.88, 0.5);
            return <circle cx={sx} cy={sy} r={2.5} fill="#2d5235" />;
          })()}

          {/* Centre circle arc */}
          {(() => {
            const [cx, cy] = toSvg(0.5, 0.5);
            return (
              <ellipse cx={cx} cy={cy}
                rx={W * 0.14} ry={H * 0.07}
                fill="none" stroke="#1e3a22" strokeWidth={1.2} />
            );
          })()}

          {/* Non-goal shots (render under goals) */}
          {others.map((s, i) => {
            const [sx, sy] = toSvg(s.x, s.y);
            const r = shotRadius(s.xg);
            const color = RESULT_COLOR[s.result] ?? "#6B7280";
            return (
              <circle
                key={`o-${i}`}
                cx={sx} cy={sy} r={r}
                fill={color} fillOpacity={0.55}
                stroke={color} strokeWidth={1}
                style={{ cursor: "pointer", filter: `drop-shadow(0 0 3px ${color}60)` }}
                onMouseEnter={() => setHovered(s)}
                onMouseLeave={() => setHovered(null)}
              />
            );
          })}

          {/* Goals on top */}
          {goals.map((s, i) => {
            const [sx, sy] = toSvg(s.x, s.y);
            const r = shotRadius(s.xg);
            return (
              <circle
                key={`g-${i}`}
                cx={sx} cy={sy} r={r}
                fill="#10B981" fillOpacity={0.85}
                stroke="#34D399" strokeWidth={1.5}
                style={{ cursor: "pointer", filter: "drop-shadow(0 0 6px #10B98180)" }}
                onMouseEnter={() => setHovered(s)}
                onMouseLeave={() => setHovered(null)}
              />
            );
          })}
        </svg>

        {/* Tooltip */}
        {hovered && (
          <div className="absolute top-3 left-3 bg-[#0a0e17]/95 border border-slate-700/60 rounded-xl p-3 text-xs shadow-2xl backdrop-blur-sm z-10 min-w-[160px]">
            <div className="flex items-center gap-2 mb-1.5">
              <div className="w-2.5 h-2.5 rounded-full" style={{ background: RESULT_COLOR[hovered.result] ?? "#6B7280" }} />
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

      {/* Stats summary */}
      <div className="flex gap-4 text-xs font-mono">
        {[
          { label: "Shots",  val: shots.length,                        color: "text-slate-400" },
          { label: "Goals",  val: goals.length,                        color: "text-[#10B981]" },
          { label: "xG",     val: shots.reduce((s,v)=>s+v.xg,0).toFixed(2), color: "text-[#60a5fa]" },
          { label: "Δ",      val: (goals.length - shots.reduce((s,v)=>s+v.xg,0)).toFixed(2),
            color: goals.length - shots.reduce((s,v)=>s+v.xg,0) >= 0 ? "text-[#10B981]" : "text-[#EF4444]" },
        ].map(item => (
          <div key={item.label} className="bg-[#0d1220] border border-slate-800 rounded-lg px-3 py-1.5 flex gap-2">
            <span className="text-slate-600 uppercase tracking-widest">{item.label}</span>
            <span className={`font-bold ${item.color}`}>{item.val}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

