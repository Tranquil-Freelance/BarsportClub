"use client";

import { LineChart, Line } from 'recharts';

const mockChartData = [
  { name: 'Match 1', xG: 1.2 },
  { name: 'Match 2', xG: 1.8 },
  { name: 'Match 3', xG: 1.4 },
  { name: 'Match 4', xG: 2.1 },
  { name: 'Match 5', xG: 1.9 },
];

export default function MiniChart() {
  return (
    <LineChart width={200} height={80} data={mockChartData}>
      <Line
        type="monotone"
        dataKey="xG"
        stroke="#ec4899"
        strokeWidth={3}
        dot={{ r: 4, fill: '#ec4899' }}
        activeDot={{ r: 6 }}
      />
    </LineChart>
  );
}