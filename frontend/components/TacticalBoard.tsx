"use client";

import React, { useState } from "react";

export interface Shot {
  minute: number;
  player: string;
  xG: number;
  result: string;
  X: number;
  Y: number;
  team_type?: "h" | "a";
}

export interface TacticalBoardProps {
  shots: Shot[];
  matchInfo?: {
    home_team: string;
    away_team: string;
  };
  width?: number;
  height?: number;
}

const TacticalBoard: React.FC<TacticalBoardProps> = ({
  shots,
  matchInfo,
  width = 800,
  height = 600,
}) => {
  // SVG viewBox matches the 0‑100 coordinate system used by Understat
  const viewBox = "0 0 100 100";
  // Invert Y coordinate because SVG's y=0 is top, while Understat's Y=0 is bottom
  const mapY = (y: number) => 100 - y;

  const [hoveredShot, setHoveredShot] = useState<Shot | null>(null);

  // Determine color based on shot result
  const getColor = (result: string) => {
    switch (result.toLowerCase()) {
      case "goal":
        return "#db2777"; // pink
      case "saved":
        return "#3b82f6"; // blue
      case "blocked":
        return "#f59e0b"; // amber
      case "off target":
      case "missed":
        return "#9ca3af"; // gray
      default:
        return "#6b7280"; // default gray
    }
  };

  // Determine radius based on xG (bigger xG = bigger circle)
  const getRadius = (xG: number) => {
    const base = 0.5;
    return base + xG * 2; // scale factor
  };

  // Pitch outline and markings
  const pitchLines = (
    <>
      {/* Outer rectangle */}
      <rect
        x="0"
        y="0"
        width="100"
        height="100"
        fill="#166534" // dark green
        stroke="#14532d"
        strokeWidth="0.2"
      />
      {/* Center line */}
      <line
        x1="50"
        y1="0"
        x2="50"
        y2="100"
        stroke="#ffffff"
        strokeWidth="0.3"
        strokeDasharray="1,1"
      />
      {/* Center circle */}
      <circle
        cx="50"
        cy="50"
        r="9.15"
        fill="none"
        stroke="#ffffff"
        strokeWidth="0.3"
      />
      {/* Penalty areas */}
      <rect
        x="0"
        y="21"
        width="16.5"
        height="58"
        fill="none"
        stroke="#ffffff"
        strokeWidth="0.3"
      />
      <rect
        x="83.5"
        y="21"
        width="16.5"
        height="58"
        fill="none"
        stroke="#ffffff"
        strokeWidth="0.3"
      />
      {/* Goal areas */}
      <rect
        x="0"
        y="36"
        width="5.5"
        height="28"
        fill="none"
        stroke="#ffffff"
        strokeWidth="0.3"
      />
      <rect
        x="94.5"
        y="36"
        width="5.5"
        height="28"
        fill="none"
        stroke="#ffffff"
        strokeWidth="0.3"
      />
      {/* Penalty spots */}
      <circle cx="11" cy="50" r="0.5" fill="#ffffff" />
      <circle cx="89" cy="50" r="0.5" fill="#ffffff" />
      {/* Corner arcs (simplified as small circles) */}
      <circle cx="0" cy="0" r="1" fill="none" stroke="#ffffff" strokeWidth="0.3" />
      <circle cx="100" cy="0" r="1" fill="none" stroke="#ffffff" strokeWidth="0.3" />
      <circle cx="0" cy="100" r="1" fill="none" stroke="#ffffff" strokeWidth="0.3" />
      <circle cx="100" cy="100" r="1" fill="none" stroke="#ffffff" strokeWidth="0.3" />
    </>
  );

  return (
    <div className="relative w-full max-w-6xl mx-auto">
      {/* Header with match info */}
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-gray-900">
          {matchInfo
            ? `${matchInfo.home_team} vs ${matchInfo.away_team}`
            : "Shot Map"}
        </h2>
        <p className="text-sm text-gray-600">
          Each circle represents a shot. Color indicates result, size indicates xG.
        </p>
      </div>

      {/* Responsive container with aspect ratio */}
      <div className="relative w-full aspect-video bg-gray-100 rounded-lg overflow-hidden shadow-lg">
        <svg
          viewBox={viewBox}
          preserveAspectRatio="xMidYMid meet"
          className="w-full h-full"
        >
          {pitchLines}

          {/* Render shots */}
          {shots.map((shot, idx) => {
            const cx = shot.X;
            const cy = mapY(shot.Y);
            const r = getRadius(shot.xG);
            const fill = getColor(shot.result);
            return (
              <g key={idx}>
                <circle
                  cx={cx}
                  cy={cy}
                  r={r}
                  fill={fill}
                  fillOpacity={0.7}
                  stroke="#fff"
                  strokeWidth="0.2"
                  onMouseEnter={() => setHoveredShot(shot)}
                  onMouseLeave={() => setHoveredShot(null)}
                  className="cursor-pointer transition-opacity hover:opacity-90"
                />
              </g>
            );
          })}

          {/* Goal labels */}
          <text x="2" y="10" fill="white" fontSize="2" textAnchor="start">
            {matchInfo?.home_team || "Home"}
          </text>
          <text x="98" y="10" fill="white" fontSize="2" textAnchor="end">
            {matchInfo?.away_team || "Away"}
          </text>
        </svg>

        {/* Tooltip */}
        {hoveredShot && (
          <div
            className="absolute z-10 px-3 py-2 text-sm font-medium text-white bg-gray-900 rounded-lg shadow-lg pointer-events-none"
            style={{
              left: `${hoveredShot.X}%`,
              top: `${100 - hoveredShot.Y}%`,
              transform: "translate(-50%, -100%)",
              marginTop: "-10px",
            }}
          >
            <div className="font-bold">{hoveredShot.player}</div>
            <div>
              xG: <span className="font-mono">{hoveredShot.xG.toFixed(2)}</span>
            </div>
            <div className="capitalize">{hoveredShot.result}</div>
            <div className="text-xs opacity-75">
              ({hoveredShot.X.toFixed(1)}, {hoveredShot.Y.toFixed(1)})
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap items-center gap-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[#db2777]"></div>
          <span>Goal</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[#3b82f6]"></div>
          <span>Saved</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[#f59e0b]"></div>
          <span>Blocked</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[#9ca3af]"></div>
          <span>Missed / Off Target</span>
        </div>
        <div className="text-gray-500 text-xs">
          Circle size proportional to xG (expected goals).
        </div>
      </div>
    </div>
  );
};

export default TacticalBoard;