"use client";
import React from "react";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Legend,
} from "recharts";

export interface RadarPlayer {
  name: string;
  color: string;
  axes: Record<string, { label: string; percentile: number }>;
}

interface Props {
  players: RadarPlayer[];
  height?: number;
}

export default function LaserRadar({ players, height = 320 }: Props) {
  if (players.length === 0) return null;

  const axisKeys = Object.keys(players[0].axes);
  const data = axisKeys.map(k => {
    const point: Record<string, any> = { axis: players[0].axes[k].label };
    players.forEach(p => { point[p.name] = p.axes[k]?.percentile ?? 0; });
    return point;
  });

  return (
    <div style={{ position: "relative" }}>
      <svg width="0" height="0" style={{ position: "absolute" }}>
        <defs>
          {players.map(p => (
            <filter key={p.name} id={`laser-glow-${p.name.replace(/\s/g, "_")}`} x="-40%" y="-40%" width="180%" height="180%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          ))}
        </defs>
      </svg>

      <ResponsiveContainer width="100%" height={height}>
        <RadarChart data={data} margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
          <PolarGrid stroke="#e2e8f0" strokeWidth={0.8} />
          <PolarAngleAxis
            dataKey="axis"
            tick={{ fill: "#64748b", fontSize: 11, fontFamily: "Inter" }}
          />
          <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />

          {players.map(p => {
            const filterId = `laser-glow-${p.name.replace(/\s/g, "_")}`;
            const alphaFill = p.color + "33"; // 20% alpha
            return (
              <Radar
                key={p.name}
                name={p.name}
                dataKey={p.name}
                stroke={p.color}
                fill={alphaFill}
                strokeWidth={2.5}
                dot={{ r: 5, fill: p.color, stroke: p.color, strokeWidth: 1,
                  style: { filter: `url(#${filterId})` } }}
                style={{ filter: `url(#${filterId})` }}
              />
            );
          })}

          {players.length > 1 && (
            <Legend
              iconType="line"
              iconSize={16}
              wrapperStyle={{ fontFamily: "Inter", fontSize: 12, color: "#64748b", paddingTop: 8 }}
            />
          )}
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
