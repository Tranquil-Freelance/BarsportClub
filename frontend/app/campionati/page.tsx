"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Trophy, Globe, Calendar, Activity, ChevronRight, LayoutDashboard } from "lucide-react";
import { useTranslation } from "react-i18next";
import "../i18n/config";
import TeamLogo from "../../components/TeamLogo";

type Match = {
  id: string; 
  home: string; 
  away: string; 
  scoreH: number; 
  scoreA: number; 
  xGH: number; 
  xGA: number; 
  status: string; 
  round: number;
};

const LEAGUES_DATA = [
  { name: "Serie A", logo: "/leagues/seriea.png" },
  { name: "Premier League", logo: "/leagues/premierleague.png" },
  { name: "La Liga", logo: "/leagues/laliga.png" },
  { name: "Bundesliga", logo: "/leagues/bundesliga.png" },
  { name: "Ligue 1", logo: "/leagues/ligue1.png" },
];

// Impostiamo la stagione corrente per forzare il backend a filtrare la spazzatura
const CURRENT_SEASON = "2025/2026"; 

export default function CampionatiPage() {
  const { t } = useTranslation();
  const [activeLeague, setActiveLeague] = useState<string>("Serie A");
  const [matches, setMatches] = useState<Match[]>([]);
  const [standings, setStandings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedLeague = sessionStorage.getItem("barsport_currentLeague");
    if (savedLeague && LEAGUES_DATA.some(l => l.name === savedLeague) && savedLeague !== "Serie A") {
      setActiveLeague(savedLeague);
    }
  }, []);

  useEffect(() => {
    let ignore = false; 
    setLoading(true);
    sessionStorage.setItem("barsport_currentLeague", activeLeague);

    const fetchLeagueData = async () => {
      try {
        // FORZIAMO IL PARAMETRO SEASON PER EVITARE I 491 PUNTI STORICI
        const [matchRes, standingsRes] = await Promise.all([
          fetch(`http://localhost:8000/api/meritometro/season?league=${encodeURIComponent(activeLeague)}&season=${encodeURIComponent(CURRENT_SEASON)}`),
          fetch(`http://localhost:8000/api/meritometro/standings?league=${encodeURIComponent(activeLeague)}&season=${encodeURIComponent(CURRENT_SEASON)}`)
        ]);

        if (ignore) return;

        if (matchRes.ok) {
            const matchData = await matchRes.json();
            const safeMatches = Array.isArray(matchData) ? matchData.map((m: any) => ({
                id: m.id ? String(m.id) : String(Math.random()),
                home: m.home || "Home",
                away: m.away || "Away",
                scoreH: m.scoreH ?? 0,
                scoreA: m.scoreA ?? 0,
                xGH: m.xGH ?? 0,
                xGA: m.xGA ?? 0,
                status: m.status || "Pre",
                round: m.round ?? 1
            })) : [];
            setMatches(safeMatches);
        }

        if (standingsRes.ok) {
            const standData = await standingsRes.json();
            setStandings(Array.isArray(standData) ? standData : []);
        }
      } catch (err) {
        if (!ignore) console.error("Errore critico di connessione:", err);
      } finally {
        if (!ignore) setLoading(false);
      }
    };
    
    fetchLeagueData();

    return () => { ignore = true; };
  }, [activeLeague]);

  useEffect(() => {
    if (!loading && matches.length > 0) {
      const savedScroll = sessionStorage.getItem('barsport_scrollPos');
      if (savedScroll) {
        setTimeout(() => {
            window.scrollTo(0, parseInt(savedScroll));
            sessionStorage.removeItem('barsport_scrollPos');
        }, 100);
      }
    }
  }, [loading, matches.length]);

  const matchesByRound = matches.reduce((acc, match) => {
    const round = match.round;
    if (!acc[round]) acc[round] = [];
    acc[round].push(match);
    return acc;
  }, {} as Record<number, Match[]>);

  let currentRound = 1;
  const playedRounds = Object.keys(matchesByRound)
    .map(Number)
    .filter(roundNum => matchesByRound[roundNum].some(m => m.status === 'FT'));
    
  if (playedRounds.length > 0) {
      currentRound = Math.max(...playedRounds);
  }
  
  const sortedRounds = Object.keys(matchesByRound)
    .map(Number)
    .filter(r => r <= currentRound + 1)
    .sort((a, b) => b - a);

  const handleMatchClick = () => {
      sessionStorage.setItem('barsport_scrollPos', window.scrollY.toString());
  };

  return (
    <div suppressHydrationWarning className="min-h-screen bg-[#F1F5F9] text-[#1E293B] font-sans pb-20 selection:bg-[#FF2A6D] selection:text-white">

      {/* ⚠️ DISCLAIMER BARSPORT */}
      <div className="w-full bg-[#0a192f] py-3 px-4 shadow-lg border-b border-[#FF2A6D]/30 z-[70] relative">
          <p className="text-[10px] font-black uppercase tracking-[0.3em] text-[#FF2A6D] text-center">
             {t("league.disclaimer")}
          </p>
      </div>

      {/* FILTER BAR: SELEZIONE DATABASE HD */}
      <div className="w-full bg-white border-b border-slate-200 py-4 px-4 sticky top-0 z-50 shadow-sm">
        <div className="max-w-[1400px] mx-auto flex justify-start md:justify-center gap-4 overflow-x-auto no-scrollbar">
          {LEAGUES_DATA.map((league) => (
            <button key={league.name} onClick={() => {
                  sessionStorage.removeItem('barsport_scrollPos'); 
                  setActiveLeague(league.name);
              }}
              className={`flex items-center gap-3 px-6 py-2.5 rounded-full transition-all border-2 whitespace-nowrap ${
                activeLeague === league.name ? "bg-[#0a192f] border-[#FF2A6D] text-white shadow-md" : "bg-white border-slate-100 text-slate-400 hover:border-slate-300"
              }`}
            >
              <img src={league.logo} alt="" className="w-4 h-4 object-contain" />
              <span className="text-[11px] font-black uppercase tracking-widest">{league.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* MAIN CONTENT */}
      <main className="max-w-[1500px] mx-auto pt-10 px-4 grid grid-cols-1 xl:grid-cols-12 gap-10 items-start">
        
        {/* COLONNA SINISTRA: CALENDARIO PARTITE */}
        <div className="xl:col-span-8 space-y-8">
            <div className="flex items-center gap-6 bg-[#0a192f] p-8 rounded-[32px] border-b-8 border-[#FF2A6D] shadow-2xl">
                <div className="p-4 bg-white/10 text-[#FF2A6D] rounded-2xl border border-white/10">
                  <LayoutDashboard size={40} />
                </div>
                <div>
                    <h1 className="text-4xl md:text-5xl font-black italic uppercase tracking-tighter text-white leading-none">{activeLeague}</h1>
                    <span className="text-[11px] font-black uppercase tracking-[0.4em] text-slate-400">{t("league.match_center_title")} • {CURRENT_SEASON}</span>
                </div>
            </div>

            {loading ? (
                <div className="h-[400px] flex flex-col items-center justify-center bg-white rounded-[40px] border-2 border-dashed border-slate-200 animate-pulse">
                   <Activity className="text-[#FF2A6D] mb-4" size={48} />
                   <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{t("league.syncing")}</span>
                </div>
            ) : sortedRounds.length > 0 ? (
                <div className="space-y-8">
                    {sortedRounds.map((round) => (
                        <div key={round} className="bg-[#0a192f] rounded-[32px] shadow-2xl border border-white/5 overflow-hidden">
                            <div className="bg-white/5 px-8 py-5 flex items-center justify-between border-b border-white/10">
                                <span className="text-sm font-black italic uppercase tracking-[0.3em] text-[#FF2A6D]">{t("league.round", { round })}</span>
                                <Calendar size={18} className="text-slate-400" />
                            </div>
                            
                            <div className="divide-y divide-white/5">
                                {matchesByRound[round].map((match) => (
                                    <Link 
                                        href={`/${activeLeague.toLowerCase().replace(' ', '-')}/match/${match.id}`} 
                                        key={match.id} 
                                        onClick={handleMatchClick}
                                        className="group block p-6 hover:bg-white/5 transition-colors cursor-pointer"
                                    >
                                        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                                            
                                            {/* Casa */}
                                            <div className="flex items-center gap-5 flex-1 justify-end w-full md:w-auto">
                                                <div className="text-right">
                                                    <h3 className="text-lg md:text-xl font-black uppercase text-white group-hover:text-[#FF2A6D] transition-colors truncate">{match.home}</h3>
                                                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mt-1">xG {match.xGH.toFixed(2)}</span>
                                                </div>
                                                <div className="bg-white p-2 rounded-full border-2 border-slate-800"><TeamLogo teamName={match.home} size={36} /></div>
                                            </div>
                                            
                                            {/* Risultato / Status */}
                                            <div className="flex justify-center items-center shrink-0 w-32">
                                                {match.status === 'FT' ? (
                                                    <div className="bg-slate-900 text-white px-6 py-3 rounded-2xl text-2xl font-black italic shadow-inner border border-white/10">
                                                        {match.scoreH} <span className="text-[#FF2A6D] mx-1">-</span> {match.scoreA}
                                                    </div>
                                                ) : (
                                                    <div className="bg-white/5 text-slate-400 border border-white/10 px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest">
                                                        {t("league.status_pre")}
                                                    </div>
                                                )}
                                            </div>

                                            {/* Trasferta */}
                                            <div className="flex items-center gap-5 flex-1 justify-start w-full md:w-auto">
                                                <div className="bg-white p-2 rounded-full border-2 border-slate-800"><TeamLogo teamName={match.away} size={36} /></div>
                                                <div className="text-left">
                                                    <h3 className="text-lg md:text-xl font-black uppercase text-white group-hover:text-[#FF2A6D] transition-colors truncate">{match.away}</h3>
                                                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mt-1">xG {match.xGA.toFixed(2)}</span>
                                                </div>
                                            </div>

                                        </div>
                                    </Link>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="h-[400px] flex flex-col items-center justify-center bg-white rounded-[40px] border-2 border-slate-100 text-center p-8">
                   <Calendar size={64} className="text-slate-200 mb-6" />
                   <h3 className="text-xl font-black text-[#0a192f] uppercase italic">{t("league.no_matches")}</h3>
                   <p className="text-slate-400 text-xs mt-2 uppercase tracking-widest">{t("league.no_data_season", { season: CURRENT_SEASON })}</p>
                </div>
            )}
        </div>

        {/* COLONNA DESTRA: CLASSIFICA DARK MODE */}
        <div className="xl:col-span-4 w-full sticky top-[100px]">
          <div className="bg-[#0a192f] rounded-[32px] shadow-2xl border-b-8 border-[#FF2A6D] overflow-hidden">
             <div className="p-8 flex justify-between items-center text-white border-b border-white/10">
                <div className="flex items-center gap-4">
                    <Trophy size={28} className="text-[#FF2A6D]" />
                    <h2 className="text-xl font-black italic uppercase tracking-tighter">{t("league.ranking_base")}</h2>
                </div>
                <div className="flex items-center gap-2 bg-white/5 px-4 py-2 rounded-full border border-white/10">
                    <div className="w-2 h-2 rounded-full bg-yellow-400 shadow-[0_0_8px_#facc15] animate-pulse" />
                    <span className="text-[9px] font-black uppercase tracking-widest text-slate-300">{t("league.status_live")}</span>
                </div>
             </div>
             
             <div className="p-0 max-h-[850px] overflow-y-auto no-scrollbar">
                 <table className="w-full text-left table-fixed">
                     <thead>
                         <tr className="border-b border-white/5 bg-white/5 sticky top-0 z-10">
                             <th className="py-5 pl-8 w-16 text-[9px] font-black uppercase tracking-widest text-slate-500">Pos</th>
                             <th className="py-5 text-[9px] font-black uppercase tracking-widest text-slate-500">Club</th>
                             <th className="py-5 pr-8 w-24 text-right text-[9px] font-black uppercase tracking-widest text-[#FF2A6D]">Punti</th>
                         </tr>
                     </thead>
                     <tbody className="divide-y divide-white/5 bg-[#0a192f]">
                         {loading ? (
                             <tr><td colSpan={3} className="py-20 text-center text-[10px] font-black text-slate-500 tracking-widest uppercase animate-pulse">{t("league.syncing_ranking")}</td></tr>
                         ) : standings.length > 0 ? (
                             standings.map((team, idx) => (
                                 <tr key={idx} className="hover:bg-white/5 transition-colors group">
                                     <td className="py-5 pl-8 text-sm font-black text-slate-500">{idx + 1}</td>
                                     <td className="py-5">
                                        <div className="flex items-center gap-4">
                                            <div className="bg-white p-2 rounded-full"><TeamLogo teamName={team.name} size={32} /></div>
                                            <span className="text-[13px] font-black text-white uppercase tracking-tight truncate group-hover:text-[#FF2A6D] transition-colors">{team.name}</span>
                                        </div>
                                     </td>
                                     <td className="py-5 pr-8 text-right text-xl font-black italic text-yellow-400">{team.points ?? 0}</td>
                                 </tr>
                             ))
                         ) : (
                             <tr><td colSpan={3} className="py-20 text-center text-[10px] font-black text-slate-500 uppercase tracking-widest">{t("league.no_standings")}</td></tr>
                         )}
                     </tbody>
                 </table>
             </div>
          </div>
        </div>

      </main>
    </div>
  );
}