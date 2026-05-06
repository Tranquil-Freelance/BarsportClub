"use client";

import React from 'react';
import TeamLogo from '../../components/TeamLogo';

export interface MatchReport {
  homeTeam: string;
  awayTeam: string;
  homeScore: number;
  awayScore: number;
  possession: string;
  xg: string;
  shotsOnTarget: number;
}

export interface MatchReportFooterProps {
  matchReport: MatchReport;
}

const MatchReportFooter: React.FC<MatchReportFooterProps> = ({ matchReport }) => {
  return (
    <div className="mt-14 bg-white text-slate-800 p-8 shadow-lg border border-slate-100 rounded-2xl relative">
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-[#0a192f] via-[#FF2A6D] to-[#0a192f] rounded-t-2xl"></div>
      <div className="flex items-center gap-5 border-b border-slate-200 pb-5 mb-5">
        <span className="font-black uppercase text-[#FF2A6D] text-2xl tracking-widest border-r border-slate-300 pr-5 leading-none">MATCH REPORT</span>
        <span className="text-slate-500 uppercase tracking-widest text-sm leading-none mt-1">ULTIMA PARTITA : {matchReport.homeTeam} vs {matchReport.awayTeam}</span>
      </div>
      <div className="flex justify-between items-center px-4">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-4">
            <TeamLogo teamName={matchReport.homeTeam} size={56} />
            <span className="font-black text-3xl uppercase tracking-tight">{matchReport.homeTeam}</span>
          </div>
          <span className="font-black text-[56px] font-bold text-slate-900 mx-4">{matchReport.homeScore} - {matchReport.awayScore}</span>
          <div className="flex items-center gap-4">
            <span className="font-black text-3xl uppercase tracking-tight text-slate-700">{matchReport.awayTeam}</span>
            <TeamLogo teamName={matchReport.awayTeam} size={56} />
          </div>
        </div>
        <button className="bg-[#FF2A6D] text-white font-black uppercase px-8 py-3 text-sm font-bold tracking-wider hover:bg-[#e6005c] transition shadow-lg cursor-pointer rounded-lg">
          Vedi il Report Completo
        </button>
      </div>
      <div className="flex text-[13px] font-bold uppercase text-slate-500 mt-8 gap-10 px-4">
        <span className="flex items-center gap-2.5"><span className="w-2.5 h-2.5 rounded-full bg-[#3b82f6]"></span> Possesso {matchReport.possession}</span>
        <span className="flex items-center gap-2.5"><span className="w-2.5 h-2.5 rounded-full bg-[#FF2A6D]"></span> xG fino {matchReport.xg}</span>
        <span className="flex items-center gap-2.5"><span className="w-2.5 h-2.5 rounded-full bg-[#FF2A6D]"></span> Tiri in Porta {matchReport.shotsOnTarget}</span>
      </div>
    </div>
  );
};

export default MatchReportFooter;