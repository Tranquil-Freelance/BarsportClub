'use client';

import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

// Mock data for player percentile ranks
const defaultRadarData = [
  { subject: 'Non-Penalty xG', A: 85, fullMark: 100 },
  { subject: 'xA', A: 70, fullMark: 100 },
  { subject: 'Shots', A: 90, fullMark: 100 },
  { subject: 'Key Passes', A: 65, fullMark: 100 },
  { subject: 'Touches in Box', A: 80, fullMark: 100 },
  { subject: 'Progressive Passes', A: 75, fullMark: 100 },
  { subject: 'Successful Dribbles', A: 60, fullMark: 100 },
  { subject: 'Defensive Actions', A: 50, fullMark: 100 },
];

interface RadarDataPoint {
  subject: string;
  A: number;
  fullMark: number;
}

interface PlayerRadarProps {
  data?: RadarDataPoint[];
}

export default function PlayerRadar({ data = defaultRadarData }: PlayerRadarProps) {
  return (
    <div className="h-full w-full rounded-xl border border-slate-800 bg-slate-900/50 p-4 shadow-lg">
      <h3 className="mb-4 text-lg font-semibold text-slate-200">
        Player Profile – Percentile Ranks
      </h3>
      <ResponsiveContainer width="100%" height={400}>
        <RadarChart data={data}>
          <PolarGrid stroke="#475569" />
          <PolarAngleAxis
            dataKey="subject"
            stroke="#94a3b8"
            tick={{ fill: '#cbd5e1', fontSize: 12 }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 100]}
            stroke="#64748b"
            tick={{ fill: '#94a3b8', fontSize: 10 }}
          />
          <Radar
            name="Player"
            dataKey="A"
            stroke="#10b981"
            fill="#10b981"
            fillOpacity={0.4}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #475569',
              borderRadius: '0.5rem',
              color: '#f1f5f9',
            }}
            labelStyle={{ color: '#cbd5e1', fontWeight: 'bold' }}
            itemStyle={{ color: '#10b981' }}
            formatter={(value: any, name: any) => [`${value}%`, 'Percentile']}
          />
        </RadarChart>
      </ResponsiveContainer>
      <p className="mt-4 text-sm text-slate-400">
        Radar shows percentile rank across key metrics (0‑100). Higher values indicate stronger relative performance.
      </p>
    </div>
  );
}