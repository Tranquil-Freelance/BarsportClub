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

interface PressingVsSoliditaScatterProps {
  data: TeamStanding[];
}

export default function PressingVsSoliditaScatter({ data }: PressingVsSoliditaScatterProps) {
  // Data already contains ppda and xga
  const processedData = data.map(team => ({
    ...team,
    label: team.name,
  }));

  // Compute averages for reference lines
  const avgPpda = processedData.reduce((sum, team) => sum + team.ppda, 0) / processedData.length;
  const avgXga = processedData.reduce((sum, team) => sum + team.xga, 0) / processedData.length;

  // Determine Como team
  const comoTeam = processedData.find(team => team.isComo);
  const otherTeams = processedData.filter(team => !team.isComo);

  // Invert PPDA axis? Lower PPDA = higher pressing, so we keep as is but note that lower is left.
  // We'll keep natural order.

  return (
    <div className="h-full w-full rounded-3xl border border-[#2a2d35] bg-[#11141a] p-6 shadow-lg">
      <h3 className="mb-2 text-xl font-black text-white uppercase">Pressing vs Solidità (PPDA vs xGA)</h3>
      <p className="mb-6 text-sm text-gray-400">
        Asse X: PPDA (intensità del pressing – più basso è, più pressano!). Asse Y: xGA (pericolosità subita).
        Vedere se il pressing alto (PPDA basso) correla con una difesa che subisce meno xG.
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
            dataKey="ppda"
            name="PPDA"
            unit=""
            stroke="#94a3b8"
            tick={{ fill: '#cbd5e1' }}
            label={{
              value: 'PPDA (Passes per Defensive Action)',
              position: 'insideBottom',
              offset: -5,
              fill: '#94a3b8',
              fontSize: 12,
            }}
            // Reverse scale? Keep normal (higher PPDA to the right)
            domain={['dataMin - 1', 'dataMax + 1']}
          />
          <YAxis
            type="number"
            dataKey="xga"
            name="Expected Goals Against"
            unit=" xGA"
            stroke="#94a3b8"
            tick={{ fill: '#cbd5e1' }}
            label={{
              value: 'xGA (Expected Goals Against)',
              angle: -90,
              position: 'insideLeft',
              fill: '#94a3b8',
              fontSize: 12,
            }}
            domain={['dataMin - 2', 'dataMax + 2']}
          />
          {/* Reference lines for average PPDA and average xGA */}
          <ReferenceLine
            x={avgPpda}
            stroke="#4a5568"
            strokeDasharray="5 5"
            strokeWidth={1.5}
            label={{
              value: `Media PPDA: ${avgPpda.toFixed(1)}`,
              position: 'top',
              fill: '#94a3b8',
              fontSize: 10,
            }}
          />
          <ReferenceLine
            y={avgXga}
            stroke="#4a5568"
            strokeDasharray="5 5"
            strokeWidth={1.5}
            label={{
              value: `Media xGA: ${avgXga.toFixed(1)}`,
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
              if (name === 'ppda') return [value.toFixed(2), 'PPDA'];
              if (name === 'xga') return [value.toFixed(2), 'xGA'];
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
          <span>Linee di media (PPDA, xGA)</span>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-4 text-xs text-gray-500">
        <div>
          <strong className="text-gray-300">Quadrante Basso‑Sinistra:</strong> Elite pressing e difesa solida (PPDA basso, xGA basso)
        </div>
        <div>
          <strong className="text-gray-300">Quadrante Basso‑Destra:</strong> Difesa solida ma pressing basso (PPDA alto, xGA basso)
        </div>
        <div>
          <strong className="text-gray-300">Quadrante Alto‑Sinistra:</strong> Pressing alto ma difesa fragile (PPDA basso, xGA alto)
        </div>
        <div>
          <strong className="text-gray-300">Quadrante Alto‑Destra:</strong> In difficoltà (pressing basso, difesa fragile)
        </div>
      </div>
      <p className="mt-4 text-xs text-gray-500">
        <strong>Nota:</strong> PPDA (Passes per Defensive Action) misura l'intensità del pressing: valori più bassi indicano un pressing più aggressivo.
      </p>
    </div>
  );
}