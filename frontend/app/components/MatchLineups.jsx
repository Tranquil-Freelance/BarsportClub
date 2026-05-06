import React, { useState, useEffect } from 'react';
import { API_BASE } from '@/app/lib/apiClient';

export default function MatchLineups({ matchId, homeTeam, awayTeam }) {
  const [lineups, setLineups] = useState(null);
  const [activeTab, setActiveTab] = useState('starters'); // 'starters' o 'bench'
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLineups = async () => {
      try {
        // Chiamata con URL assoluto verso il server Python
        const response = await fetch(`${API_BASE}/api/v1/matches/${matchId}/lineups`);
        
        if (!response.ok) {
          throw new Error(`Errore HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        setLineups(data);
      } catch (error) {
        console.error("Errore formazioni:", error);
        setLineups(null);
      } finally {
        setLoading(false);
      }
    };

    if (matchId) fetchLineups();
  }, [matchId]);

  if (loading) return <div className="p-6 text-center text-slate-400">Caricamento formazioni...</div>;

  // CONTROLLO DI SICUREZZA BLINDATO
  // Se la risposta è vuota, o non ha 'home', o non ha 'away', ci fermiamo subito.
  if (!lineups || !lineups.home || !lineups.away) {
    return <div className="p-6 text-center text-slate-500">Formazioni non disponibili.</div>;
  }

  // Se i dati ci sono ma le liste dei titolari sono vuote (array vuoti)
  if ((!lineups.home.starters || lineups.home.starters.length === 0) && 
      (!lineups.away.starters || lineups.away.starters.length === 0)) {
    return <div className="p-6 text-center text-slate-500">Formazioni non disponibili.</div>;
  }

  const currentHome = activeTab === 'starters' ? (lineups.home.starters || []) : (lineups.home.bench || []);
  const currentAway = activeTab === 'starters' ? (lineups.away.starters || []) : (lineups.away.bench || []);

  const PlayerEvents = ({ player }) => (
    <div className="flex items-center gap-1.5">
      {player.subbed_in && <span className="text-green-400 font-bold" title="Entrato">↑</span>}
      {player.goals > 0 && [...Array(player.goals)].map((_, i) => (
        <span key={`g-${i}`} title="Gol">⚽</span>
      ))}
      {player.yellow_cards > 0 && (
        <div className="w-2.5 h-3.5 bg-yellow-400 rounded-sm" title="Ammonito" />
      )}
      {player.red_cards > 0 && (
        <div className="w-2.5 h-3.5 bg-red-600 rounded-sm" title="Espulso" />
      )}
    </div>
  );

  return (
    <div className="bg-[#0f172a] rounded-xl border border-slate-800 text-sm">
      
      {/* TABS */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-[#0B1120]">
        <div className="flex items-center gap-4">
          <div className="w-8 h-8 rounded-full bg-blue-900/30 text-blue-400 flex items-center justify-center font-bold text-xs">
            {homeTeam?.substring(0, 2).toUpperCase() || 'HO'}
          </div>
          
          <div className="flex gap-4">
            <button
              onClick={() => setActiveTab('starters')}
              className={`font-semibold tracking-wider text-xs ${activeTab === 'starters' ? 'text-white' : 'text-slate-500 hover:text-slate-300'}`}
            >
              TITOLARI
            </button>
            <button
              onClick={() => setActiveTab('bench')}
              className={`font-semibold tracking-wider text-xs ${activeTab === 'bench' ? 'text-white' : 'text-slate-500 hover:text-slate-300'}`}
            >
              PANCHINA
            </button>
          </div>

          <div className="w-8 h-8 rounded-full bg-red-900/30 text-red-400 flex items-center justify-center font-bold text-xs">
            {awayTeam?.substring(0, 2).toUpperCase() || 'AW'}
          </div>
        </div>
      </div>

      {/* TITOLI SQUADRE */}
      <div className="grid grid-cols-2 bg-[#0B1120]/50 border-b border-slate-800/50">
        <div className="px-6 py-2.5 font-bold text-xs text-blue-400 tracking-wider uppercase border-r border-slate-800/50">
          {homeTeam}
        </div>
        <div className="px-6 py-2.5 font-bold text-xs text-red-400 tracking-wider uppercase text-right">
          {awayTeam}
        </div>
      </div>

      {/* LISTA GIOCATORI */}
      <div className="grid grid-cols-2 relative">
        <div className="absolute top-0 bottom-0 left-1/2 w-px bg-slate-800/50 -translate-x-1/2" />
        
        {/* LATO CASA */}
        <div className="flex flex-col py-2">
          {currentHome.map((player, idx) => (
            <div key={`h-${idx}`} className="px-6 py-2 flex items-center gap-3 border-b border-slate-800/20">
              <PlayerEvents player={player} />
              <span className="text-slate-200 font-medium">{player.name}</span>
              {player.minutes > 0 && activeTab === 'starters' && player.minutes < 90 && (
                <span className="text-red-400 font-bold ml-auto" title="Sostituito">↓</span>
              )}
            </div>
          ))}
        </div>

        {/* LATO TRASFERTA */}
        <div className="flex flex-col py-2">
          {currentAway.map((player, idx) => (
            <div key={`a-${idx}`} className="px-6 py-2 flex items-center justify-end gap-3 border-b border-slate-800/20">
              {player.minutes > 0 && activeTab === 'starters' && player.minutes < 90 && (
                <span className="text-red-400 font-bold mr-auto" title="Sostituito">↓</span>
              )}
              <span className="text-slate-200 font-medium">{player.name}</span>
              <PlayerEvents player={player} />
            </div>
          ))}
        </div>
      </div>
      
    </div>
  );
}