"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Trophy, Calendar, Activity, LayoutDashboard } from "lucide-react";
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

const LEAGUE_NAME = "Bundesliga";
const LEAGUE_SLUG = "bundesliga";
const CURRENT_SEASON = "2025/2026";

export default function LeaguePage() {
  const { t } = useTranslation();
  const [matches, setMatches] = useState<Match[]>([]);
  const [standings, setStandings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [matchRes, standRes] = await Promise.all([
          fetch(`http://localhost:8000/api/meritometro/season?league=${encodeURIComponent(LEAGUE_NAME)}&season=${encodeURIComponent(CURRENT_SEASON)}`),
          fetch(`http://localhost:8000/api/meritometro/standings?league=${encodeURIComponent(LEAGUE_NAME)}&season=${encodeURIComponent(CURRENT_SEASON)}`)
        ]);
        if (matchRes.ok) {
          const data = await matchRes.json();
          setMatches(Array.isArray(data) ? data.map((m: any) => ({
            id: m.id ? String(m.id) : String(Math.random()),
            home: m.home || "Home", away: m.away || "Away",
            scoreH: m.scoreH ?? 0, scoreA: m.scoreA ?? 0,
            xGH: m.xGH ?? 0, xGA: m.xGA ?? 0,
            status: m.status || "Pre", round: m.round ?? 1
          })) : []);
        }
        if (standRes.ok) {
          const data = await standRes.json();
          setStandings(Array.isArray(data) ? data : []);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const matchesByRound = matches.reduce((acc, m) => {
    if (!acc[m.round]) acc[m.round] = [];
    acc[m.round].push(m);
    return acc;
  }, {} as Record<number, Match[]>);

  const playedRounds = Object.keys(matchesByRound).map(Number).filter(r => matchesByRound[r].some(m => m.status === 'FT'));
  const currentRound = playedRounds.length > 0 ? Math.max(...playedRounds) : 1;
  const sortedRounds = Object.keys(matchesByRound).map(Number).filter(r => r <= currentRound + 1).sort((a, b) => b - a);

  return (
    <div suppressHydrationWarning className="min-h-screen bg-[#F1F5F9] text-[#1E293B] font-sans pb-20 selection:bg-[#FF2A6D] selection:text-white">

      <div className="w-full bg-[#0a192f] py-3 px-4 border-b border-[#FF2A6D]/30">
        <p className="text-[10px] font-black uppercase tracking-[0.3em] text-[#FF2A6D] text-center">
          {t("league.disclaimer")}
        </p>
      </div>

      <main className="max-w-[1500px] mx-auto pt-10 px-4 grid grid-cols-1 xl:grid-cols-12 gap-10 items-start">

        <div className="xl:col-span-8 space-y-8">
          <div className="flex items-center gap-6 bg-[#0a192f] p-8 rounded-[32px] border-b-8 border-[#FF2A6D] shadow-2xl">
            <div className="p-4 bg-white/10 text-[#FF2A6D] rounded-2xl border border-white/10">
              <LayoutDashboard size={40} />
            </div>
            <div>
              <h1 className="text-4xl md:text-5xl font-black italic uppercase tracking-tighter text-white leading-none"
                style={{ fontFamily: "var(--font-oswald, sans-serif)" }}>
                {LEAGUE_NAME}
              </h1>
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
                      <Link href={`/${LEAGUE_SLUG}/match/${match.id}`} key={match.id}
                        className="group block p-6 hover:bg-white/5 transition-colors cursor-pointer">
                        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                          <div className="flex items-center gap-5 flex-1 justify-end w-full md:w-auto">
                            <div className="text-right">
                              <h3 className="text-lg md:text-xl font-black uppercase text-white group-hover:text-[#FF2A6D] transition-colors truncate"
                                style={{ fontFamily: "var(--font-oswald, sans-serif)" }}>
                                {match.home}
                              </h3>
                              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mt-1">xG {match.xGH.toFixed(2)}</span>
                            </div>
                            <div className="bg-white p-2 rounded-full border-2 border-slate-800"><TeamLogo teamName={match.home} size={36} /></div>
                          </div>

                          <div className="flex justify-center items-center shrink-0 w-32">
                            {match.status === 'FT' ? (
                              <div className="bg-slate-900 text-white px-6 py-3 rounded-2xl text-2xl font-black italic shadow-inner border border-white/10"
                                style={{ fontFamily: "var(--font-oswald, sans-serif)" }}>
                                {match.scoreH} <span className="text-[#FF2A6D] mx-1">-</span> {match.scoreA}
                              </div>
                            ) : (
                              <div className="bg-white/5 text-slate-400 border border-white/10 px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest">{t("league.status_pre")}</div>
                            )}
                          </div>

                          <div className="flex items-center gap-5 flex-1 justify-start w-full md:w-auto">
                            <div className="bg-white p-2 rounded-full border-2 border-slate-800"><TeamLogo teamName={match.away} size={36} /></div>
                            <div className="text-left">
                              <h3 className="text-lg md:text-xl font-black uppercase text-white group-hover:text-[#FF2A6D] transition-colors truncate"
                                style={{ fontFamily: "var(--font-oswald, sans-serif)" }}>
                                {match.away}
                              </h3>
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

        <div className="xl:col-span-4 w-full sticky top-[100px]">
          <div className="bg-[#0a192f] rounded-[32px] shadow-2xl border-b-8 border-[#FF2A6D] overflow-hidden">
            <div className="p-8 flex justify-between items-center text-white border-b border-white/10">
              <div className="flex items-center gap-4">
                <Trophy size={28} className="text-[#FF2A6D]" />
                <h2 className="text-xl font-black italic uppercase tracking-tighter" style={{ fontFamily: "var(--font-oswald, sans-serif)" }}>{t("league.standings")}</h2>
              </div>
              <div className="flex items-center gap-2 bg-white/5 px-4 py-2 rounded-full border border-white/10">
                <div className="w-2 h-2 rounded-full bg-yellow-400 shadow-[0_0_8px_#facc15] animate-pulse" />
                <span className="text-[9px] font-black uppercase tracking-widest text-slate-300">{t("league.status_live")}</span>
              </div>
            </div>
            <div className="max-h-[850px] overflow-y-auto no-scrollbar">
              <table className="w-full text-left table-fixed">
                <thead>
                  <tr className="border-b border-white/5 bg-white/5 sticky top-0">
                    <th className="py-5 pl-8 w-16 text-[9px] font-black uppercase tracking-widest text-slate-500">Pos</th>
                    <th className="py-5 text-[9px] font-black uppercase tracking-widest text-slate-500">Club</th>
                    <th className="py-5 pr-8 w-24 text-right text-[9px] font-black uppercase tracking-widest text-[#FF2A6D]">Punti</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {loading ? (
                    <tr><td colSpan={3} className="py-20 text-center text-[10px] font-black text-slate-500 uppercase animate-pulse">{t("common.loading")}</td></tr>
                  ) : standings.length > 0 ? standings.map((team, idx) => (
                    <tr key={idx} className="hover:bg-white/5 transition-colors group">
                      <td className="py-5 pl-8 text-sm font-black text-slate-500">{idx + 1}</td>
                      <td className="py-5">
                        <div className="flex items-center gap-4">
                          <div className="bg-white p-1.5 rounded-full"><TeamLogo teamName={team.name} size={32} /></div>
                          <span className="text-[13px] font-black text-white uppercase tracking-tight truncate group-hover:text-[#FF2A6D] transition-colors">{team.name}</span>
                        </div>
                      </td>
                      <td className="py-5 pr-8 text-right text-xl font-black italic text-yellow-400">{team.points ?? 0}</td>
                    </tr>
                  )) : (
                    <tr><td colSpan={3} className="py-20 text-center text-[10px] font-black text-slate-500 uppercase">{t("league.no_standings")}</td></tr>
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
