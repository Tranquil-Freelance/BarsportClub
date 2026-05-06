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
  Label,
} from 'recharts';

interface TeamStanding {
  pos: number;
  name: string;
  season: string;
  matches: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  pts: number;
  gd: string;
  xg: number;
  xga: number;
  xpts: number;
  ppda: number;
  xg_diff: number;
  xga_diff: number;
  xpts_diff: number;
  isComo: boolean;
}

interface VolumeVsCinismoScatterProps {
  data: TeamStanding[];
}

export default function VolumeVsCinismoScatter({ data }: VolumeVsCinismoScatterProps) {
  // Calculate efficiency (goals_for / xg)
  const processedData = data.map(team => ({
    ...team,
    efficiency: team.xg > 0 ? team.goals_for / team.xg : 0,
    label: team.name,
  }));

  // Compute averages for reference lines
  const avgXg = processedData.reduce((sum, team) => sum + team.xg, 0) / processedData.length;
  const avgEfficiency = processedData.reduce((sum, team) => sum + team.efficiency, 0) / processedData.length;

  // Determine Como team
  const comoTeam = processedData.find(team => team.isComo);
  const otherTeams = processedData.filter(team => !team.isComo);

  return (
    <div className="h-full w-full rounded-3xl border border-[#2a2d35] bg-[#11141a] p-6 shadow-lg">
      <h3 className="mb-2 text-xl font-black text-white uppercase">Volume vs Cinismo (xG vs Efficiency)</h3>
      <p className="mb-6 text-sm text-gray-400">
        Asse X: xG (volume di occasioni create). Asse Y: Goals / xG (rapporto di conversione).
        Identifica chi crea tanto ma spreca (basso in classifica Y) e chi segna con mezzo tiro (alto in classifica Y).
      </p>
      <ResponsiveContainer width="100%" height={450}>
        <ScatterChart
          margin={{
            top: 20,
            right: 20,
            bottom: 30,
            left: 20,
          }}
        >
          <CartesianGrid stroke="#2a2d35" strokeDasharray="3 3" />
          <XAxis
            type="number"
            dataKey="xg"
            name="Expected Goals"
            unit=" xG"
            stroke="#94a3b8"
            tick={{ fill: '#cbd5e1' }}
            label={{
              value: 'Expected Goals (xG)',
              position: 'insideBottom',
              offset: -5,
              fill: '#94a3b8',
              fontSize: 12,
            }}
          />
          <YAxis
            type="number"
            dataKey="efficiency"
            name="Efficiency"
            unit=""
            stroke="#94a3b8"
            tick={{ fill: '#cbd5e1' }}
            label={{
              value: 'Goals / xG',
              angle: -90,
              position: 'insideLeft',
              fill: '#94a3b8',
              fontSize: 12,
            }}
            domain={[0, 'dataMax + 0.2']}
          />
          {/* Reference lines for average xG and average efficiency */}
          <ReferenceLine
            x={avgXg}
            stroke="#4a5568"
            strokeDasharray="5 5"
            strokeWidth={1.5}
            label={{
              value: `Media xG: ${avgXg.toFixed(1)}`,
              position: 'top',
              fill: '#94a3b8',
              fontSize: 10,
            }}
          />
          <ReferenceLine
            y={avgEfficiency}
            stroke="#4a5568"
            strokeDasharray="5 5"
            strokeWidth={1.5}
            label={{
              value: `Media Eff: ${avgEfficiency.toFixed(2)}`,
              position: 'right',
              fill: '#94a3b8',
              fontSize: 10,
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
            formatter={(value: any, name: any) => {
              if (name === 'xg') return [value.toFixed(2), 'xG'];
              if (name === 'efficiency') return [value.toFixed(2), 'Goals/xG'];
              return [value, name];
            }}
            cursor={{ strokeDasharray: '3 3' }}
            labelFormatter={(label) => `Squadra: ${label}`}
          />
          <Legend
            wrapperStyle={{ color: '#cbd5e1', fontSize: '0.875rem' }}
            iconType="circle"
          />
          {/* Scatter for other teams */}
          <Scatter
            name="Altre squadre"
            data={otherTeams}
            fill="#94a3b8"
            fillOpacity={0.7}
            stroke="#64748b"
            strokeWidth={1}
            shape="circle"
          />
          {/* Scatter for Como */}
          {comoTeam && (
            <Scatter
              name="Como"
              data={[comoTeam]}
              fill="#00529F"
              fillOpacity={1}
              stroke="#003B73"
              strokeWidth={2}
              shape="star"
            />
          )}
        </ScatterChart>
      </ResponsiveContainer>
      <div className="mt-6 flex flex-wrap items-center justify-between gap-4 text-sm text-gray-400">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-gray-500"></div>
          <span>Altre squadre</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-[#00529F]"></div>
          <span>Como (squadra di riferimento)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full border border-gray-500"></div>
          <span>Linee di media (xG, Efficiency)</span>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-4 text-xs text-gray-500">
        <div>
          <strong className="text-gray-300">Quadrante Alto‑Destra:</strong> Elite (creano tanto e segnano molto)
        </div>
        <div>
          <strong className="text-gray-300">Quadrante Alto‑Sinistra:</strong> Overperformer (segna con poco xG)
        </div>
        <div>
          <strong className="text-gray-300">Quadrante Basso‑Destra:</strong> Spreconi (creano tanto ma segnano poco)
        </div>
        <div>
          <strong className="text-gray-300">Quadrante Basso‑Sinistra:</strong> In difficoltà (poco xG, bassa efficienza)
        </div>
      </div>
    </div>
  );
}