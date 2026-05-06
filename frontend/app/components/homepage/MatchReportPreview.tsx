import React from 'react';
import TeamLogo from '../../../components/TeamLogo';

export interface MatchReportPreviewProps {
  homeTeam?: string;
  awayTeam?: string;
  homeScore?: number;
  awayScore?: number;
  matchDate?: string;
  competition?: string;
}

const MatchReportPreview: React.FC<MatchReportPreviewProps> = ({
  homeTeam = 'Palermo',
  awayTeam = 'Cagliari',
  homeScore = 2,
  awayScore = 1,
  matchDate = '2023-10-15',
  competition = 'Serie B',
}) => {
  return (
    <section className="match-report-preview p-8 bg-gradient-to-br from-zinc-900 to-zinc-950 rounded-2xl border border-zinc-800 shadow-2xl">
      <header className="flex justify-between items-center mb-10">
        <div>
          <span className="inline-block px-4 py-2 bg-palermo-pink/20 text-palermo-pink font-heading font-bold uppercase tracking-wider rounded-full text-sm">
            Featured Match Report
          </span>
          <h2 className="text-4xl font-heading font-bold mt-4">
            Analisi Tattica Dettagliata
          </h2>
        </div>
        <span className="text-sm font-heading font-bold px-4 py-2 bg-zinc-800 text-zinc-300 rounded-full uppercase tracking-wide">
          {competition}
        </span>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10 mb-10">
        {/* Shot map visual preview */}
        <div className="lg:col-span-2">
          <div className="bg-zinc-800/50 border border-zinc-700 rounded-2xl p-6">
            <h3 className="text-xl font-heading font-bold mb-6 flex items-center gap-3">
              <span className="w-3 h-3 rounded-full bg-palermo-pink"></span>
              Mappa dei Tiri (Shot Map)
            </h3>
            <div className="relative h-64 bg-gradient-to-br from-zinc-900 to-black rounded-xl overflow-hidden border border-zinc-800 flex items-center justify-center">
              {/* Placeholder for shot map visualization */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-full h-full relative">
                  {/* Mock field */}
                  <div className="absolute inset-4 border-2 border-zinc-700 rounded-lg"></div>
                  <div className="absolute top-1/2 left-0 right-0 border-t-2 border-zinc-700"></div>
                  <div className="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 w-12 h-12 border-2 border-zinc-700 rounded-full"></div>
                  {/* Shots */}
                  <div className="absolute top-1/4 left-1/4 w-3 h-3 rounded-full bg-palermo-pink shadow-lg"></div>
                  <div className="absolute top-1/3 left-2/3 w-3 h-3 rounded-full bg-blue-500 shadow-lg"></div>
                  <div className="absolute top-2/3 left-1/3 w-3 h-3 rounded-full bg-palermo-pink shadow-lg"></div>
                  <div className="absolute bottom-1/4 right-1/4 w-3 h-3 rounded-full bg-palermo-pink shadow-lg"></div>
                  <div className="absolute bottom-1/3 left-1/2 w-3 h-3 rounded-full bg-blue-500 shadow-lg"></div>
                </div>
              </div>
              <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 text-zinc-400 text-sm">
                Interattivo • Clicca per esplorare
              </div>
            </div>
            <div className="flex justify-between items-center mt-6 text-sm">
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-3">
                  <TeamLogo teamName={homeTeam} size={24} />
                  <span className="text-zinc-300 font-bold uppercase">{homeTeam}</span>
                </div>
                <div className="flex items-center gap-3">
                  <TeamLogo teamName={awayTeam} size={24} />
                  <span className="text-zinc-300 font-bold uppercase">{awayTeam}</span>
                </div>
              </div>
              <div className="text-zinc-500">5 tiri totali</div>
            </div>
          </div>
        </div>

        {/* Tactical paragraph and stats */}
        <div className="space-y-8">
          <div className="bg-zinc-800/30 p-6 rounded-2xl border border-zinc-800">
            <h3 className="text-xl font-heading font-bold mb-4">Sintesi Tattica</h3>
            <p className="text-zinc-300 font-body leading-relaxed">
              Palermo ha dominato la fase di possesso (58%) ma ha sofferto nella
              fase di transizione. La squadra ha creato occasioni da area
              centrale, sfruttando le sovrapposizioni dei terzini. Il Cagliari ha
              tentato di contrastare con un pressing alto, risultando in
              diversi contropiedi pericolosi.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-zinc-800/50 p-4 rounded-xl text-center">
              <div className="text-3xl font-heading font-bold text-palermo-pink">
                {homeScore}
              </div>
              <div className="text-xs uppercase tracking-wider text-zinc-400 mt-2">
                Gol {homeTeam}
              </div>
            </div>
            <div className="bg-zinc-800/50 p-4 rounded-xl text-center">
              <div className="text-3xl font-heading font-bold text-blue-500">
                {awayScore}
              </div>
              <div className="text-xs uppercase tracking-wider text-zinc-400 mt-2">
                Gol {awayTeam}
              </div>
            </div>
          </div>

          <div className="bg-zinc-900/70 p-5 rounded-xl">
            <h4 className="font-heading font-bold text-sm uppercase tracking-wider text-zinc-400 mb-3">
              Statistiche Rapide
            </h4>
            <ul className="space-y-3">
              <li className="flex justify-between">
                <span className="text-zinc-300">Possesso</span>
                <span className="font-bold">58% - 42%</span>
              </li>
              <li className="flex justify-between">
                <span className="text-zinc-300">xG Totale</span>
                <span className="font-bold">2.0 - 1.3</span>
              </li>
              <li className="flex justify-between">
                <span className="text-zinc-300">Passaggi Chiave</span>
                <span className="font-bold">8 - 4</span>
              </li>
              <li className="flex justify-between">
                <span className="text-zinc-300">Falli Commessi</span>
                <span className="font-bold">12 - 18</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <footer className="flex flex-col sm:flex-row justify-between items-center pt-8 border-t border-zinc-800">
        <div className="text-zinc-400 font-body text-sm mb-4 sm:mb-0">
          <span className="font-bold">Data Partita:</span>{' '}
          {new Date(matchDate).toLocaleDateString('it-IT', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
        </div>
        <button className="px-10 py-4 bg-gradient-to-r from-palermo-pink to-purple-600 hover:from-pink-600 hover:to-purple-700 text-white font-heading font-bold uppercase tracking-wider rounded-xl transition-all duration-300 shadow-lg hover:shadow-pink-900/50 hover:scale-105">
          Leggi l’Analisi Completa →
        </button>
      </footer>
    </section>
  );
};

export default MatchReportPreview;