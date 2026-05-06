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
const playerRadarData = [
  { subject: 'Non-Penalty xG', A: 85, fullMark: 100 },
  { subject: 'xA', A: 70, fullMark: 100 },
  { subject: 'Shots', A: 90, fullMark: 100 },
  { subject: 'Key Passes', A: 65, fullMark: 100 },
  { subject: 'Touches in Box', A: 80, fullMark: 100 },
  { subject: 'Progressive Passes', A: 75, fullMark: 100 },
  { subject: 'Successful Dribbles', A: 60, fullMark: 100 },
  { subject: 'Defensive Actions', A: 50, fullMark: 100 },
];

export default function PlayerRadarPink() {
  return (
    <div className="h-full w-full rounded-xl border border-pink-900 bg-black/50 p-4 shadow-lg">
      <h3 className="mb-4 text-lg font-semibold text-pink-200">
        Player Profile – Percentile Ranks (Palermo Edition)
      </h3>
      <ResponsiveContainer width="100%" height={400}>
        <RadarChart data={playerRadarData}>
          <PolarGrid stroke="#4c0519" />
          <PolarAngleAxis
            dataKey="subject"
            stroke="#f9a8d4"
            tick={{ fill: '#fbcfe8', fontSize: 12 }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 100]}
            stroke="#9d174d"
            tick={{ fill: '#f9a8d4', fontSize: 10 }}
          />
          <Radar
            name="Player"
            dataKey="A"
            stroke="#db2777"
            fill="#db2777"
            fillOpacity={0.4}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #831843',
              borderRadius: '0.5rem',
              color: '#fce7f3',
            }}
            labelStyle={{ color: '#fbcfe8', fontWeight: 'bold' }}
            itemStyle={{ color: '#db2777' }}
            formatter={(value: any, name: any) => [`${value}%`, 'Percentile']}
          />
        </RadarChart>
      </ResponsiveContainer>
      <p className="mt-4 text-sm text-pink-300">
        Radar shows percentile rank across key metrics (0‑100). Higher values indicate stronger relative performance.
      </p>
    </div>
  );
}