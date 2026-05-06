"use client";

import React, { useState } from 'react';
import Link from 'next/link';

export interface HeroSectionProps {
  heroStats: {
    possession: string;
    xg: string;
  };
  chartPoints: Array<{ cx: number; cy: number }>;
  chartValues: string[];
  totalXg: number;
  isLoading: boolean;
  matchInfo?: {
    home_team: string;
    away_team: string;
  } | null;
}

const HeroSection: React.FC<HeroSectionProps> = ({
  heroStats,
  chartPoints,
  chartValues,
  totalXg,
  isLoading,
  matchInfo,
}) => {
  const [hoveredCircleIndex, setHoveredCircleIndex] = useState<number | null>(null);

  return (
    <header className="bg-palermo-dark relative h-[520px] overflow-hidden flex items-center">
      
      <img src="/AL1_0070-1920x1060.jpg" alt="Palermo Esultanza" className="absolute inset-0 w-full h-full object-cover object-[80%_center] opacity-70" />
      <div className="absolute inset-0 bg-gradient-to-r from-palermo-dark via-palermo-dark/70 to-transparent"></div>
      
      <div className="relative z-10 pl-14 w-full">
        <h1 className="font-heading uppercase text-7xl font-bold text-white leading-[0.9] tracking-tight drop-shadow-lg">
          INSIDE {matchInfo?.home_team?.toUpperCase() || 'PALERMO'}:
        </h1>
        <h2 className="font-heading uppercase text-4xl text-palermo-pink mt-2 font-bold drop-shadow-md">
          ANALISI E STATISTICHE
        </h2>
        <p className="text-zinc-200 text-lg mt-3 tracking-wide drop-shadow max-w-xl">
          Approfondimenti e dati avanzati sul Palermo Calcio
        </p>
        
        <div className="mt-10 bg-[#111111]/90 border-t-[3px] border-palermo-pink p-6 flex gap-8 w-fit shadow-2xl rounded-sm">
          <div className="flex flex-col gap-5 min-w-[150px]">
            <div className="bg-white/5 p-4 border border-white/5 rounded-sm">
              <p className="text-xs text-zinc-400 font-bold mb-1 uppercase tracking-wider">Possesso Palla</p>
              <p className="font-heading text-[48px] font-bold text-white leading-none">{heroStats.possession}</p>
            </div>
            <div className="bg-white/5 p-4 border border-white/5 rounded-sm">
              <p className="text-xs text-zinc-400 font-bold mb-1 uppercase tracking-wider">xG di Squadra</p>
              <p className="font-heading text-4xl font-bold text-white leading-none">
                {isLoading ? '...' : totalXg.toFixed(2)}
              </p>
            </div>
          </div>
          
          <div className="border-l border-zinc-700/80 pl-8 w-[340px] flex flex-col justify-between">
            <div className="flex justify-between items-center mb-2">
              <p className="text-xs text-zinc-300 font-bold flex items-center gap-2 uppercase tracking-wider">
                <span className="w-2 h-2 rounded-full bg-palermo-pink"></span>
                Rendimento Ultime 5 Partite
              </p>
              <div className="text-xs text-palermo-pink font-bold uppercase tracking-wider">
                {hoveredCircleIndex !== null ? chartValues[hoveredCircleIndex] : 'Passa il mouse sopra i punti'}
              </div>
            </div>
            
            <div className="h-28 relative mb-5">
              <svg viewBox="0 0 100 40" className="w-full h-full overflow-visible">
                <polyline points="0,30 20,15 40,35 60,10 80,25 100,5" fill="none" stroke="#eb3b81" strokeWidth="1.5" strokeLinejoin="round" />
                {chartPoints.map((point, index) => (
                  <circle
                    key={index}
                    cx={point.cx}
                    cy={point.cy}
                    r={hoveredCircleIndex === index ? 4 : 2.5}
                    fill="#eb3b81"
                    onMouseEnter={() => setHoveredCircleIndex(index)}
                    onMouseLeave={() => setHoveredCircleIndex(null)}
                    style={{ cursor: 'pointer' }}
                  />
                ))}
              </svg>
            </div>
            
            <Link href="/article/hero-analysis" className="w-full bg-palermo-pink text-white font-heading uppercase py-3 text-sm font-bold tracking-wider hover:bg-pink-600 transition shadow-md flex items-center justify-center">
              Scopri di Più &#11163;
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
};

export default HeroSection;