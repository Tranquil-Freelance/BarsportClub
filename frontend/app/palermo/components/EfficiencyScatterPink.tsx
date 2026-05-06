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

// Mock data: 14 players with xG and actual goals – all pink/black theme
const playerScatterData = [
  { name: 'Player A', xG: 5.2, goals: 7, fill: '#db2777' },
  { name: 'Player B', xG: 8.1, goals: 9, fill: '#db2777' },
  { name: 'Player C', xG: 3.5, goals: 4, fill: '#db2777' },
  { name: 'Player D', xG: 6.7, goals: 6, fill: '#db2777' },
  { name: 'Player E', xG: 9.0, goals: 8, fill: '#db2777' },
  { name: 'Player F', xG: 4.3, goals: 5, fill: '#db2777' },
  { name: 'Player G', xG: 7.8, goals: 6, fill: '#db2777' },
  { name: 'Player H', xG: 2.9, goals: 3, fill: '#db2777' },
  { name: 'Player I', xG: 10.5, goals: 11, fill: '#db2777' },
  { name: 'Player J', xG: 6.1, goals: 5, fill: '#db2777' },
  { name: 'Player K', xG: 5.8, goals: 6, fill: '#db2777' },
  { name: 'Player L', xG: 4.0, goals: 2, fill: '#db2777' },
  { name: 'Player M', xG: 8.7, goals: 10, fill: '#db2777' },
  { name: 'Palermo Striker', xG: 12.3, goals: 15, fill: '#831843' }, // darker pink
];

export default function EfficiencyScatterPink() {
  return (
    <div className="h-full w-full rounded-xl border border-pink-900 bg-black/50 p-4 shadow-lg">
      <h3 className="mb-4 text-lg font-semibold text-pink-200">
        xG vs Actual Goals – Palermo‑Centric View
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
          <CartesianGrid stroke="#4c0519" strokeDasharray="3 3" />
          <XAxis
            type="number"
            dataKey="xG"
            name="Expected Goals"
            unit=" xG"
            stroke="#f9a8d4"
            tick={{ fill: '#fbcfe8' }}
            label={{
              value: 'Expected Goals (xG)',
              position: 'insideBottom',
              offset: -5,
              fill: '#f9a8d4',
            }}
          />
          <YAxis
            type="number"
            dataKey="goals"
            name="Actual Goals"
            unit=" goals"
            stroke="#f9a8d4"
            tick={{ fill: '#fbcfe8' }}
            label={{
              value: 'Actual Goals',
              angle: -90,
              position: 'insideLeft',
              fill: '#f9a8d4',
            }}
          />
          <ReferenceLine
            stroke="#9d174d"
            strokeDasharray="5 5"
            strokeWidth={1.5}
            segment={[
              { x: 0, y: 0 },
              { x: 15, y: 15 },
            ]}
            label={{
              value: 'y = x (parity)',
              position: 'right',
              fill: '#f9a8d4',
              fontSize: 12,
            }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #831843',
              borderRadius: '0.5rem',
              color: '#fce7f3',
            }}
            labelStyle={{ color: '#fbcfe8', fontWeight: 'bold' }}
            formatter={(value: any, name: any) => [value, name]}
            cursor={{ strokeDasharray: '3 3' }}
          />
          <Legend
            wrapperStyle={{ color: '#fbcfe8', fontSize: '0.875rem' }}
            iconType="circle"
          />
          <Scatter
            name="League Players"
            data={playerScatterData.filter((p) => p.fill === '#db2777')}
            fill="#db2777"
            fillOpacity={0.7}
            stroke="#be185d"
            strokeWidth={1}
          />
          <Scatter
            name="Palermo Striker"
            data={playerScatterData.filter((p) => p.fill === '#831843')}
            fill="#831843"
            fillOpacity={1}
            stroke="#500724"
            strokeWidth={2}
            shape="star"
          />
        </ScatterChart>
      </ResponsiveContainer>
      <div className="mt-4 flex flex-wrap items-center justify-between gap-4 text-sm text-pink-300">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-pink-500"></div>
          <span>League average performers</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-pink-900"></div>
          <span>Palermo striker (over‑performing)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full border border-pink-700"></div>
          <span>Parity line y = x</span>
        </div>
      </div>
      <p className="mt-4 text-sm text-pink-400">
        Points above the diagonal line indicate over‑performance (goals greater than xG); points below indicate under‑performance.
      </p>
    </div>
  );
}