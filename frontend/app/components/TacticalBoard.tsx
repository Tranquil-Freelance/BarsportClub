"use client";

import React, { useState } from 'react';

export interface TacticalBoardProps {
  tacticalNodes: Array<{
    id: number;
    top?: string;
    left?: string;
    right?: string;
    playerLabel: string;
  }>;
  matchInfo?: {
    home_team: string;
    away_team: string;
  } | null;
  topPlayers?: string[];
}

const TacticalBoard: React.FC<TacticalBoardProps> = ({ tacticalNodes, matchInfo, topPlayers = [] }) => {
  const [activeNode, setActiveNode] = useState<number | null>(null);

  // Merge topPlayers into tacticalNodes, preserving coordinates
  const mergedNodes = tacticalNodes.map((node, index) => ({
    ...node,
    playerLabel: topPlayers[index] || node.playerLabel,
  }));

  return (
    <div className="bg-white shadow-lg flex flex-col rounded-sm overflow-hidden">
      {/* MODIFICA QUI: aumentato padding a destra per evitare taglio testo */}
      <div className="bg-palermo-pink text-white font-heading text-[15px] pl-5 pr-10 py-1.5 w-fit font-bold tracking-wider relative -top-4 left-5 shadow-md" style={{ clipPath: 'polygon(0 0, calc(100% - 20px) 0, 100% 100%, 0% 100%)' }}>
        ANALISI TATTICA
      </div>
      <div className="px-7 pt-1 pb-5 border-b-[5px] border-palermo-dark">
        <h3 className="font-heading text-4xl text-black uppercase leading-none font-bold tracking-tight">
          COME ATTACCA IL {matchInfo?.home_team?.toUpperCase() || 'PALERMO'}
        </h3>
        <p className="text-zinc-600 mt-2 text-sm">Focus sulle strategie offensive dei rosanero.</p>
      </div>
      <div className="relative w-full h-56 bg-green-800 flex items-center justify-center">
        <div className="absolute inset-0 bg-black/30"></div>
        {mergedNodes.map((node) => (
          <div
            key={node.id}
            className={`absolute w-7 h-7 bg-palermo-pink/90 rounded-full border-2 border-white flex items-center justify-center shadow-lg cursor-pointer ${activeNode === node.id ? 'ring-2 ring-white ring-offset-1' : ''}`}
            style={{
              top: node.top,
              left: node.left,
              right: node.right
            }}
            onClick={() => setActiveNode(node.id)}
          >
            <span className="text-white text-xs font-bold">{node.id}</span>
          </div>
        ))}
        {activeNode !== null && (() => {
          const node = mergedNodes.find(n => n.id === activeNode);
          const style: any = { bottom: 'calc(100% + 5px)' };
          if (node?.left) {
            style.left = node.left;
            style.transform = 'translateX(-50%)';
          } else if (node?.right) {
            style.right = node.right;
            style.transform = 'translateX(50%)';
          }
          return (
            <div
              className="absolute bg-white text-black text-xs font-bold px-2 py-1 rounded shadow-lg z-20 whitespace-nowrap"
              style={style}
            >
              {node?.playerLabel}
            </div>
          );
        })()}
        <button className="relative z-10 bg-palermo-dark text-white font-heading uppercase px-8 py-2 text-sm font-bold border-b-2 border-palermo-pink shadow-2xl mt-32 hover:bg-black transition cursor-pointer">
          Leggi l'Analisi &#11163;
        </button>
      </div>
    </div>
  );
};

export default TacticalBoard;