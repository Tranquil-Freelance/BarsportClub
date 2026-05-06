'use client';

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
} from 'recharts';

// Mock data: 14 players with xG and actual goals
const defaultScatterData = [
  { name: 'Player A', xG: 5.2, goals: 7, fill: '#10b981' },
  { name: 'Player B', xG: 8.1, goals: 9, fill: '#10b981' },
  { name: 'Player C', xG: 3.5, goals: 4, fill: '#10b981' },
  { name: 'Player D', xG: 6.7, goals: 6, fill: '#10b981' },
  { name: 'Player E', xG: 9.0, goals: 8, fill: '#10b981' },
  { name: 'Player F', xG: 4.3, goals: 5, fill: '#10b981' },
  { name: 'Player G', xG: 7.8, goals: 6, fill: '#10b981' },
  { name: 'Player H', xG: 2.9, goals: 3, fill: '#10b981' },
  { name: 'Player I', xG: 10.5, goals: 11, fill: '#10b981' },
  { name: 'Player J', xG: 6.1, goals: 5, fill: '#10b981' },
  { name: 'Player K', xG: 5.8, goals: 6, fill: '#10b981' },
  { name: 'Player L', xG: 4.0, goals: 2, fill: '#10b981' },
  { name: 'Player M', xG: 8.7, goals: 10, fill: '#10b981' },
  { name: 'Palermo Striker', xG: 12.3, goals: 15, fill: '#f472b6' }, // highlighted
];

interface ScatterDataPoint {
  name: string;
  xG: number;
  goals: number;
  fill: string;
}

interface EfficiencyScatterProps {
  data?: ScatterDataPoint[];
}

export default function EfficiencyScatter({ data = defaultScatterData }: EfficiencyScatterProps) {
  const leaguePlayers = data.filter((p) => p.fill === '#10b981');
  const highlightedPlayers = data.filter((p) => p.fill === '#f472b6');

  return (
    <div className="h-full w-full rounded-xl border border-slate-800 bg-slate-900/50 p-4 shadow-lg">
      <h3 className="mb-4 text-lg font-semibold text-slate-200">
        xG vs Actual Goals – League Comparison
      </h3>
      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart
          margin={{
            top: 20,
            right: 20,
            bottom: 20,
            left: 20,
          }}
        >
          <CartesianGrid stroke="#475569" strokeDasharray="3 3" />
          <XAxis
            type="number"
            dataKey="xG"
            name="Expected Goals"
            unit=" xG"
            stroke="#94a3b8"
            tick={{ fill: '#cbd5e1' }}
            label={{
              value: 'Expected Goals (xG)',
              position: 'insideBottom',
              offset: -5,
              fill: '#94a3b8',
            }}
          />
          <YAxis
            type="number"
            dataKey="goals"
            name="Actual Goals"
            unit=" goals"
            stroke="#94a3b8"
            tick={{ fill: '#cbd5e1' }}
            label={{
              value: 'Actual Goals',
              angle: -90,
              position: 'insideLeft',
              fill: '#94a3b8',
            }}
          />
          <ReferenceLine
            stroke="#64748b"
            strokeDasharray="5 5"
            strokeWidth={1.5}
            segment={[
              { x: 0, y: 0 },
              { x: 15, y: 15 },
            ]}
            label={{
              value: 'y = x (parity)',
              position: 'right',
              fill: '#94a3b8',
              fontSize: 12,
            }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #475569',
              borderRadius: '0.5rem',
              color: '#f1f5f9',
            }}
            labelStyle={{ color: '#cbd5e1', fontWeight: 'bold' }}
            formatter={(value: any, name: any) => [value, name]}
            cursor={{ strokeDasharray: '3 3' }}
          />
          <Legend
            wrapperStyle={{ color: '#cbd5e1', fontSize: '0.875rem' }}
            iconType="circle"
          />
          <Scatter
            name="League Players"
            data={leaguePlayers}
            fill="#10b981"
            fillOpacity={0.7}
            stroke="#059669"
            strokeWidth={1}
          />
          <Scatter
            name="Palermo Striker"
            data={highlightedPlayers}
            fill="#f472b6"
            fillOpacity={1}
            stroke="#db2777"
            strokeWidth={2}
            shape="star"
          />
        </ScatterChart>
      </ResponsiveContainer>
      <div className="mt-4 flex flex-wrap items-center justify-between gap-4 text-sm text-slate-400">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-emerald-500"></div>
          <span>League average performers</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-pink-500"></div>
          <span>Highlighted star (over‑performing)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full border border-slate-500"></div>
          <span>Parity line y = x</span>
        </div>
      </div>
      <p className="mt-4 text-sm text-slate-400">
        Points above the diagonal line indicate over-performance (goals greater than xG); points below indicate under-performance.
      </p>
    </div>
  );
}