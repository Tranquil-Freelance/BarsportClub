import React from 'react';
import { getPalermoStats } from '../../lib/mockData';

export interface DataPanelProps {
  title?: string;
  description?: string;
}

const rankingBadgeColors = {
  top: 'bg-emerald-900/40 text-emerald-300 border-emerald-700',
  mid: 'bg-amber-900/40 text-amber-300 border-amber-700',
  low: 'bg-rose-900/40 text-rose-300 border-rose-700',
};

const RankingBadge: React.FC<{ level: 'top' | 'mid' | 'low' }> = ({ level }) => (
  <span
    className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border ${rankingBadgeColors[level]}`}
  >
    {level === 'top' && 'Top Tier'}
    {level === 'mid' && 'Mid Tier'}
    {level === 'low' && 'Lower Tier'}
  </span>
);

const DataPanel: React.FC<DataPanelProps> = ({
  title = 'Metriche Chiave',
  description = 'Indicatori avanzati per valutare le prestazioni del Palermo. Dati aggiornati ogni partita.',
}) => {
  const palermoStats = getPalermoStats();

  const metrics = [
    {
      label: 'xG per Partita',
      value: palermoStats.xgPerMatch.toFixed(1),
      change: '+0.2',
      badge: palermoStats.rankingBadge,
      description: 'Goal attesi generati a partita',
      icon: '📊',
    },
    {
      label: 'PPDA',
      value: palermoStats.ppda.toFixed(1),
      change: '-0.3',
      badge: palermoStats.rankingBadge,
      description: 'Passaggi per azione difensiva (meno = pressing più aggressivo)',
      icon: '⚡',
    },
    {
      label: 'Possesso %',
      value: palermoStats.possession.toFixed(1),
      change: '+1.5',
      badge: palermoStats.rankingBadge,
      description: 'Percentuale media di possesso palla',
      icon: '🔄',
    },
    {
      label: 'Ranking',
      value: palermoStats.rankingBadge === 'top' ? 'Alto' : palermoStats.rankingBadge === 'mid' ? 'Medio' : 'Basso',
      change: '',
      badge: palermoStats.rankingBadge,
      description: 'Posizione nelle metriche avanzate della lega',
      icon: '🏆',
    },
  ];

  return (
    <section className="data-panel p-8 bg-gradient-to-br from-zinc-900 to-black rounded-2xl border border-zinc-800 shadow-2xl">
      <header className="mb-12">
        <h2 className="text-4xl font-heading font-bold mb-4">{title}</h2>
        <p className="text-zinc-300 text-lg max-w-2xl">{description}</p>
      </header>

      {/* Vertical elegant stats */}
      <div className="space-y-6">
        {metrics.map((metric) => (
          <div
            key={metric.label}
            className="bg-zinc-800/30 backdrop-blur-sm p-6 rounded-2xl border border-zinc-700 hover:border-palermo-pink/50 transition-all duration-300"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-5">
                <div className="text-3xl">{metric.icon}</div>
                <div>
                  <div className="flex items-center gap-4 mb-2">
                    <h3 className="text-xl font-heading font-bold">{metric.label}</h3>
                    <RankingBadge level={metric.badge} />
                  </div>
                  <p className="text-zinc-400 text-sm mb-4">{metric.description}</p>
                  <div className="flex items-baseline">
                    <span className="text-5xl font-heading font-bold">{metric.value}</span>
                    {metric.change && (
                      <span
                        className={`ml-4 text-lg font-semibold ${
                          metric.change.startsWith('+')
                            ? 'text-emerald-400'
                            : 'text-rose-400'
                        }`}
                      >
                        {metric.change}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-zinc-500">Ultimo aggiornamento</div>
                <div className="text-xs text-zinc-600">ieri</div>
              </div>
            </div>
            {/* Progress bar (optional) */}
            {metric.label.includes('Possesso') && (
              <div className="mt-6">
                <div className="flex justify-between text-sm text-zinc-400 mb-2">
                  <span>Palermo</span>
                  <span>Media Lega: 52.4%</span>
                </div>
                <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-palermo-pink to-purple-600"
                    style={{ width: `${palermoStats.possession}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer note */}
      <div className="mt-12 pt-8 border-t border-zinc-800 text-center">
        <p className="text-zinc-500 text-sm">
          Dati forniti da <span className="text-palermo-pink font-bold">Opta</span> e{' '}
          <span className="text-palermo-pink font-bold">Advanced Analytics Engine</span>. Aggiornati dopo ogni partita.
        </p>
        <button className="mt-6 px-8 py-3 border border-zinc-700 text-zinc-300 hover:text-white hover:border-palermo-pink font-heading font-bold uppercase tracking-wider rounded-xl transition-all duration-300">
          Scopri Tutte le Metriche
        </button>
      </div>
    </section>
  );
};

export default DataPanel;