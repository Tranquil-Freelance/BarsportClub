"use client";

import React from 'react';

export interface AdvancedStatsProps {
  advancedStats: {
    xg: string;
    ppda: string;
    duelliVinti: string;
  };
  totalXg: number;
  isLoading: boolean;
}

const AdvancedStats: React.FC<AdvancedStatsProps> = ({
  advancedStats,
  totalXg,
  isLoading,
}) => {
  return (
    <div className="bg-white shadow-lg flex flex-col rounded-sm overflow-hidden">
      {/* MODIFICA QUI: aumentato padding a destra per evitare taglio testo */}
      <div className="bg-palermo-pink text-white font-heading text-[15px] pl-5 pr-10 py-1.5 w-fit font-bold tracking-wider relative -top-4 left-5 shadow-md" style={{ clipPath: 'polygon(0 0, calc(100% - 20px) 0, 100% 100%, 0% 100%)' }}>
        STATISTICHE AVANZATE
      </div>
      <div className="px-7 pt-1 pb-5 border-b-[5px] border-palermo-pink">
        <h3 className="font-heading text-4xl text-black uppercase leading-none font-bold tracking-tight">I NUMERI CHIAVE DEL PALERMO</h3>
        <p className="text-zinc-600 mt-2 text-sm">Dati approfonditi e metriche avanzate.</p>
      </div>
      <div className="bg-[#151518] p-8 flex-grow flex flex-col justify-center">
        <div className="flex justify-between items-center px-2">
          <div className="flex flex-col items-center">
            <span className="text-xs text-zinc-400 font-bold mb-2 uppercase tracking-widest">xG</span>
            <span className="font-heading text-[52px] text-white font-bold leading-none">
              {isLoading ? '...' : totalXg.toFixed(2)}
            </span>
          </div>
          <div className="w-px h-16 bg-zinc-700"></div>
          <div className="flex flex-col items-center">
            <span className="text-xs text-zinc-400 font-bold mb-2 uppercase tracking-widest">PPDA</span>
            <span className="font-heading text-[52px] text-white font-bold leading-none">{advancedStats.ppda}</span>
          </div>
          <div className="w-px h-16 bg-zinc-700"></div>
          <div className="flex flex-col items-center">
            <span className="text-xs text-zinc-400 font-bold mb-2 uppercase tracking-widest">Duelli Vinti</span>
            <span className="font-heading text-[52px] text-white font-bold leading-none">{advancedStats.duelliVinti}</span>
          </div>
        </div>
        <div className="mt-8 flex justify-center">
          <button className="bg-palermo-pink text-white font-heading uppercase px-14 py-2.5 text-sm font-bold tracking-wider hover:bg-pink-600 transition shadow-lg cursor-pointer">
            Scopri i Dati &#11163;
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdvancedStats;