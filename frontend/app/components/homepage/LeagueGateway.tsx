import React from 'react';
import Link from 'next/link';
import { featuredLeagues, LeagueGatewayCard } from '../../lib/mockData';

export interface LeagueGatewayProps {
  leagues?: LeagueGatewayCard[];
  title?: string;
}

const LeagueGateway: React.FC<LeagueGatewayProps> = ({
  leagues = featuredLeagues,
  title = 'Esplora le Leghe',
}) => {
  return (
    <section className="league-gateway py-24 bg-zinc-950">
      <div className="container mx-auto px-6">
        <header className="text-center mb-20">
          <h2 className="text-5xl font-heading font-bold mb-6">{title}</h2>
          <p className="text-zinc-400 text-xl max-w-3xl mx-auto">
            Approfondisci statistiche dettagliate, report partite e analisi tattiche per ogni competizione.
          </p>
        </header>

        {/* Two large gateway cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {leagues.map((league) => (
            <div
              key={league.id}
              className="group relative bg-gradient-to-br from-zinc-900 to-black rounded-3xl border border-zinc-800 p-10 text-white shadow-2xl hover:shadow-3xl transition-all duration-700 overflow-hidden"
            >
              {/* Animated background glow */}
              <div className="absolute -inset-4 bg-gradient-to-r from-palermo-pink/10 to-purple-900/10 opacity-0 group-hover:opacity-100 blur-3xl transition-opacity duration-700" />

              <div className="relative z-10">
                <div className="flex items-start justify-between mb-10">
                  <div className="flex items-center">
                    <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-palermo-pink/20 to-purple-600/30 flex items-center justify-center text-5xl mr-8">
                      {league.logoPlaceholder}
                    </div>
                    <div>
                      <h3 className="text-4xl font-heading font-bold">{league.name}</h3>
                      <div className="flex items-center text-lg text-zinc-300 mt-3">
                        <span>{league.country}</span>
                        <span className="mx-3">•</span>
                        <span className="font-bold">{league.level}</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-5xl font-heading font-bold">{league.stats.matchesAnalyzed}</div>
                    <div className="text-sm text-zinc-400 uppercase tracking-wider mt-2">Partite analizzate</div>
                  </div>
                </div>

                <p className="text-zinc-300 text-xl mb-12 leading-relaxed">{league.description}</p>

                {/* Simplified stats */}
                <div className="grid grid-cols-3 gap-6 mb-12">
                  <div className="bg-zinc-800/50 backdrop-blur-sm p-5 rounded-2xl border border-zinc-700">
                    <div className="text-sm text-zinc-400 mb-2">Squadra Top</div>
                    <div className="text-2xl font-heading font-bold">{league.stats.topTeam}</div>
                  </div>
                  <div className="bg-zinc-800/50 backdrop-blur-sm p-5 rounded-2xl border border-zinc-700">
                    <div className="text-sm text-zinc-400 mb-2">Goal Medi</div>
                    <div className="text-2xl font-heading font-bold">{league.stats.avgGoals.toFixed(1)}</div>
                  </div>
                  <div className="bg-zinc-800/50 backdrop-blur-sm p-5 rounded-2xl border border-zinc-700">
                    <div className="text-sm text-zinc-400 mb-2">Possesso Medio</div>
                    <div className="text-2xl font-heading font-bold">{league.stats.avgPossession.toFixed(1)}%</div>
                  </div>
                </div>

                <div className="flex justify-between items-center pt-10 border-t border-zinc-800">
                  <Link
                    href={`/leagues/${league.id}`}
                    className="px-10 py-5 bg-gradient-to-r from-palermo-pink to-purple-600 hover:from-pink-600 hover:to-purple-700 text-white font-heading font-bold uppercase tracking-wider rounded-2xl transition-all duration-300 shadow-lg hover:shadow-pink-900/50 hover:scale-105"
                  >
                    Esplora {league.name}
                  </Link>
                  <div className="text-right">
                    <div className="text-sm text-zinc-400">Dati aggiornati giornalmente</div>
                    <div className="text-xs text-zinc-600">via Opta & Advanced Analytics</div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Minimal CTA */}
        <div className="mt-24 text-center">
          <h3 className="text-3xl font-heading font-bold mb-8">
            Vuoi confrontare le leghe?
          </h3>
          <p className="text-zinc-400 text-lg max-w-2xl mx-auto mb-12">
            Usa il nostro strumento di comparazione interattivo per analizzare le differenze in goal per partita, possesso, xG e molto altro.
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-8">
            <button className="px-12 py-5 bg-gradient-to-r from-palermo-pink to-purple-600 hover:from-pink-600 hover:to-purple-700 text-white font-heading font-bold uppercase tracking-wider rounded-2xl transition-all duration-300 shadow-lg hover:shadow-pink-900/50 hover:scale-105">
              Avvia Strumento di Confronto
            </button>
            <button className="px-12 py-5 border-2 border-zinc-700 text-zinc-300 hover:text-white hover:border-palermo-pink font-heading font-bold uppercase tracking-wider rounded-2xl transition-all duration-300 hover:scale-105">
              Scarica Report Completo
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default LeagueGateway;