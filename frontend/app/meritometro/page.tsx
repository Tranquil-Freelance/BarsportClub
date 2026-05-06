"use client";

import React, { useEffect, useState } from "react";
import { ChevronRight, LayoutDashboard, Trophy } from "lucide-react";
import { useTranslation } from "react-i18next";
import "../i18n/config";
import TeamLogo from "../../components/TeamLogo";
export const dynamic = 'force-dynamic';

const LEAGUES = [
  { name: "Serie A", id: "Serie A", logo: "/leagues/seriea.png" },
  { name: "Premier League", id: "Premier League", logo: "/leagues/premierleague.png" },
  { name: "La Liga", id: "La Liga", logo: "/leagues/laliga.png" },
  { name: "Bundesliga", id: "Bundesliga", logo: "/leagues/bundesliga.png" },
  { name: "Ligue 1", id: "Ligue 1", logo: "/leagues/ligue1.png" },
];
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Match = {
  id: string; home: string; away: string;
  scoreH: number; scoreA: number; xGH: number; xGA: number;
  imrH: number; imrA: number; perc_H: number; perc_A: number;
  status: string; round: number;
  verdetto: string;
};

type ImrRankingData = {
  name: string;
  total_imr: number;
};

export default function MeritometroPage() {
  const { t } = useTranslation();
  const [activeLeague, setActiveLeague] = useState("Serie A");
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [imrRanking, setImrRanking] = useState<ImrRankingData[]>([]);

  useEffect(() => {
    const saved = localStorage.getItem("active_league_barsport");
    if (saved) setActiveLeague(saved);
  }, []);

  const handleLeagueChange = (leagueId: string) => {
    setActiveLeague(leagueId);
    localStorage.setItem("active_league_barsport", leagueId);
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [mRes, rRes] = await Promise.all([
          fetch(`${API_BASE}/api/meritometro/season?league=${encodeURIComponent(activeLeague)}`),
          fetch(`${API_BASE}/api/meritometro/imr_standings?league=${encodeURIComponent(activeLeague)}`)
        ]);
        if (mRes.ok) setMatches(await mRes.json());
        if (rRes.ok) setImrRanking(await rRes.json());
      } catch (err) {
        console.error("Errore fetch dati:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [activeLeague]);

  return (
    <div suppressHydrationWarning className="min-h-screen bg-[#F1F5F9] text-[#1E293B] font-sans pb-20">
      
      {/* SELETTORE LEGHE LOCALE */}
      <div className="w-full bg-white border-b border-slate-200 py-6 px-4 shadow-sm">
        <div className="max-w-[1200px] mx-auto flex justify-start md:justify-center gap-6 md:gap-12 overflow-x-auto no-scrollbar scroll-smooth py-2">
          {LEAGUES.map((l) => (
            <button
              key={l.id}
              onClick={() => handleLeagueChange(l.id)}
              className={`flex flex-col items-center gap-3 min-w-[100px] group transition-all duration-300 ${
                activeLeague === l.id ? "scale-105" : "opacity-40 hover:opacity-100 grayscale hover:grayscale-0"
              }`}
            >
              <div className={`p-3 rounded-2xl bg-slate-50 border-2 transition-all ${
                activeLeague === l.id ? "border-[#FF2A6D] bg-white shadow-lg" : "border-transparent"
              }`}>
                <img 
                    src={l.logo} 
                    alt={l.name} 
                    className="w-10 h-10 md:w-14 md:h-14 object-contain"
                    onError={(e) => {
                        (e.currentTarget as HTMLImageElement).src = "/leagues/default.png";
                    }}
                />
              </div>
              <span className={`text-[10px] font-black uppercase tracking-widest ${
                activeLeague === l.id ? "text-[#0a192f]" : "text-slate-400"
              }`}>{l.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* CONTENITORE DATI */}
      <div className="max-w-[1400px] mx-auto px-4 mt-10 grid grid-cols-1 lg:grid-cols-12 gap-10">
        
        {/* COLONNA SINISTRA: PARTITE */}
        <div className="lg:col-span-8 space-y-6">
          <div className="flex items-center gap-4 mb-8 px-2">
            <h2 className="text-3xl font-black italic uppercase tracking-tighter text-[#0a192f] flex items-center gap-3">
               Meritometro <ChevronRight className="text-[#FF2A6D]" size={32} /> <span className="text-[#FF2A6D]">{activeLeague}</span>
            </h2>
          </div>

          {loading ? (
             <div className="h-96 flex flex-col items-center justify-center bg-white rounded-3xl border-2 border-dashed border-slate-200 animate-pulse">
                <div className="w-12 h-12 border-4 border-[#FF2A6D] border-t-transparent rounded-full animate-spin mb-4"></div>
                <span className="text-slate-400 font-black uppercase tracking-widest text-[10px]">{t("meritometro.db_loading")}</span>
             </div>
          ) : matches.length > 0 ? (
            matches.map((match) => (
              <div key={match.id} className="bg-white border-b-4 border-slate-200 rounded-3xl p-6 md:p-8 hover:border-[#FF2A6D] transition-all shadow-lg hover:shadow-2xl group relative overflow-hidden">
                 <div className="absolute top-0 left-0 bg-slate-100 text-slate-400 text-[9px] font-black px-4 py-1 rounded-br-xl uppercase tracking-tighter">{t("meritometro.round")} {match.round}</div>
                 
                 <div className="flex flex-col md:flex-row items-center gap-8">
                    
                    {/* Scoreboard Centrale */}
                    <div className="w-full md:w-2/5 flex items-center justify-between border-r-0 md:border-r-2 border-slate-100 md:pr-10">
                      <div className="flex flex-col items-center text-center gap-3 w-24">
                          <TeamLogo teamName={match.home} size={54} />
                          <span className="text-[10px] font-black uppercase text-[#0a192f] leading-none truncate w-full">{match.home}</span>
                      </div>
                      
                      <div className="flex flex-col items-center">
                          <div className="text-5xl font-black text-[#0a192f] italic tracking-tighter">{match.scoreH} <span className="text-slate-200">-</span> {match.scoreA}</div>
                          <div className="bg-[#0a192f] text-white text-[8px] font-bold px-3 py-1 rounded-full mt-2 uppercase tracking-widest">{t("meritometro.final")}</div>
                      </div>

                      <div className="flex flex-col items-center text-center gap-3 w-24">
                          <TeamLogo teamName={match.away} size={54} />
                          <span className="text-[10px] font-black uppercase text-[#0a192f] leading-none truncate w-full">{match.away}</span>
                      </div>
                    </div>

                    {/* Analisi del Merito */}
                    <div className="w-full md:flex-1">
                      <div className="flex justify-between items-end mb-4">
                          <div className="flex flex-col">
                              <span className="text-[11px] font-black text-[#FF2A6D] uppercase tracking-widest mb-1">{match.verdetto}</span>
                              <div className="flex items-baseline gap-2">
                                <span className="text-4xl font-black text-[#0a192f] tracking-tighter">{match.perc_H}%</span>
                                <span className="text-sm font-bold text-slate-300 uppercase">vs</span>
                                <span className="text-4xl font-black text-[#0a192f] tracking-tighter opacity-30">{match.perc_A}%</span>
                              </div>
                          </div>
                          <div className="text-right">
                             <div className="text-[9px] font-black text-[#FF2A6D] uppercase italic border-b-2 border-[#FF2A6D] inline-block">IMR: {match.imrH} - {match.imrA}</div>
                          </div>
                      </div>
                      
                      {/* LA BARRA DOPPIA - ROSA VS BLU NOTTE */}
                      <div className="relative h-6 bg-[#0a192f] rounded-full overflow-hidden flex p-0 border border-slate-200 shadow-inner">
                          <div 
                            className="h-full bg-gradient-to-r from-[#FF2A6D] to-[#ff5d92] transition-all duration-1000 shadow-[0_0_15px_rgba(255,42,109,0.4)]" 
                            style={{ width: `${match.perc_H}%` }}
                          ></div>
                      </div>
                    </div>

                 </div>
              </div>
            ))
          ) : (
             <div className="bg-white p-20 rounded-3xl border-2 border-slate-100 text-center flex flex-col items-center gap-4">
                <LayoutDashboard size={64} className="text-slate-200" />
                <span className="text-slate-400 font-black uppercase tracking-widest">{t("common.no_data")}</span>
             </div>
          )}
        </div>

        {/* COLONNA DESTRA: CLASSIFICA IMR (Stile Dark) */}
        <div className="lg:col-span-4 w-full sticky top-[40px]">
          <div className="bg-[#0a192f] rounded-[32px] shadow-2xl border-b-8 border-[#FF2A6D] overflow-hidden">
             
             <div className="p-8 flex justify-between items-center text-white border-b border-white/10">
                <div className="flex items-center gap-4">
                    <Trophy size={28} className="text-[#FF2A6D]" />
                    <h2 className="text-xl font-black italic uppercase tracking-tighter">{t("meritometro.ranking")}</h2>
                </div>
             </div>
             
             <div className="p-0 max-h-[850px] overflow-y-auto no-scrollbar">
                 <table className="w-full text-left table-fixed">
                     <thead>
                         <tr className="border-b border-white/5 bg-white/5 sticky top-0 z-10">
                             <th className="py-5 pl-8 w-16 text-[9px] font-black uppercase tracking-widest text-slate-500">{t("meritometro.pos")}</th>
                             <th className="py-5 text-[9px] font-black uppercase tracking-widest text-slate-500">{t("meritometro.club")}</th>
                             <th className="py-5 pr-8 w-32 text-right text-[9px] font-black uppercase tracking-widest text-[#FF2A6D]">{t("meritometro.imr_total")}</th>
                         </tr>
                     </thead>
                     <tbody className="divide-y divide-white/5 bg-[#0a192f]">
                         {loading ? (
                             <tr><td colSpan={3} className="py-20 text-center text-[10px] font-black text-slate-500 tracking-widest uppercase animate-pulse">{t("meritometro.computing")}</td></tr>
                         ) : imrRanking.length > 0 ? (
                             imrRanking.map((team, idx) => (
                                 <tr key={idx} className="hover:bg-white/5 transition-colors group">
                                     <td className="py-5 pl-8 text-sm font-black text-slate-500">{idx + 1}</td>
                                     <td className="py-5">
                                        <div className="flex items-center gap-4">
                                            <div className="bg-white p-1.5 rounded-full"><TeamLogo teamName={team.name} size={20} /></div>
                                            <span className="text-[13px] font-black text-white uppercase tracking-tight truncate group-hover:text-[#FF2A6D] transition-colors">{team.name}</span>
                                        </div>
                                     </td>
                                     <td className="py-5 pr-8 text-right text-xl font-black italic text-yellow-400">{team.total_imr.toFixed(1)}</td>
                                 </tr>
                             ))
                         ) : (
                             <tr><td colSpan={3} className="py-20 text-center text-[10px] font-black text-slate-500 uppercase tracking-widest">{t("meritometro.no_ranking")}</td></tr>
                         )}
                     </tbody>
                 </table>
             </div>
             
          </div>
        </div>

      </div>
    </div>
  );
}