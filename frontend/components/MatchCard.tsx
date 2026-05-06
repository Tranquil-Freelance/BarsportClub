"use client";

import React from 'react';
import TeamLogo from './TeamLogo'; // Assicurati che il percorso di importazione sia corretto

interface MatchCardProps {
    date: string;
    time: string;
    homeTeam: string;
    awayTeam: string;
    isActive?: boolean;
    onClick?: () => void;
}

export default function MatchCard({ date, time, homeTeam, awayTeam, isActive = false, onClick }: MatchCardProps) {
    return (
        <div
            onClick={onClick}
            className={`w-full p-5 rounded-2xl cursor-pointer transition-all duration-300 border mb-4 transform
                ${isActive
                    ? 'bg-[#0a192f] border-[#FF2A6D] shadow-[0_0_25px_rgba(255,42,109,0.4)] text-white hover:-translate-y-1 hover:shadow-[0_0_30px_rgba(255,42,109,0.6)]'
                    : 'bg-white border-slate-200 shadow-sm text-slate-800 hover:border-slate-300 hover:shadow-xl hover:shadow-pink-500/20 hover:-translate-y-1'
                }
            `}
        >
            {/* Date & Time */}
            <div className={`text-xs font-bold tracking-widest mb-4 ${isActive ? 'text-slate-400' : 'text-slate-500'}`}>
                {date} {time}
            </div>

            {/* Teams & Logos */}
            <div className="flex flex-col gap-3">
                {/* Home Team */}
                <div className="flex items-center justify-between">
                    <span className="font-black italic tracking-tighter text-xl uppercase truncate pr-3">
                        {homeTeam}
                    </span>
                    <div className="flex-shrink-0 w-12 h-12 flex items-center justify-center">
                        <TeamLogo teamName={homeTeam} size={48} />
                    </div>
                </div>

                {/* VS divider */}
                <div className={`text-[10px] font-black tracking-widest ${isActive ? 'text-slate-500' : 'text-slate-300'}`}>
                    VS
                </div>

                {/* Away Team */}
                <div className="flex items-center justify-between">
                    <span className="font-black italic tracking-tighter text-xl uppercase truncate pr-3">
                        {awayTeam}
                    </span>
                    <div className="flex-shrink-0 w-12 h-12 flex items-center justify-center">
                        <TeamLogo teamName={awayTeam} size={48} />
                    </div>
                </div>
            </div>
        </div>
    );
}