import React from 'react';

export interface TopBarProps {
  className?: string;
}

const TopBar: React.FC<TopBarProps> = ({ className = '' }) => {
  return (
    <header
      className={`top-bar ${className} bg-zinc-950 border-b border-zinc-800/80 py-2 text-xs md:text-sm font-body`}
      role="banner"
    >
      <div className="container mx-auto px-4 flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <span className="text-palermo-pink font-bold">ULTIMA PARTITA:</span>
            <span className="font-heading font-bold">Palermo 2–1 Cagliari</span>
            <span className="text-zinc-400">|</span>
            <span className="text-zinc-400">Serie B</span>
            <span className="hidden md:inline text-zinc-500">· Matchday 28</span>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <div className="hidden md:flex items-center space-x-3">
            <span className="text-zinc-500">Data live:</span>
            <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></span>
            <span className="text-zinc-300">Aggiornato ora</span>
          </div>
          <button className="text-palermo-pink hover:text-pink-400 font-medium transition-colors">
            Notifiche
          </button>
        </div>
      </div>
    </header>
  );
};

export default TopBar;