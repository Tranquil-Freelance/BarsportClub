'use client';
import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Shot {
  minute: number;
  player: string;
  xG: number;
  X: number; // 0-1
  Y: number; // 0-1
  result: string;
  team_type: string; // 'h' | 'a'
}

export default function PremiumShotMap({ matchId }: { matchId: number }) {
  const [shots, setShots] = useState<Shot[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`http://127.0.0.1:8001/api/v1/analytics/match/${matchId}/shots`)
      .then(res => res.json())
      .then(data => { setShots(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [matchId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 text-white/30 font-mono">
        <div className="animate-pulse">Caricamento dati avanzati...</div>
      </div>
    );
  }

  // Funzione di mapping coordinate Understat (0-1) a SVG (0-100) con orientamento squadra
  const mapCoordinates = (shot: Shot) => {
    const scaleX = shot.X * 100; // 0-100
    const scaleY = shot.Y * 100; // 0-100

    let x, y;
    if (shot.team_type === 'h') {
      // Casa: porta a sinistra, tiri verso destra
      x = 50 + scaleX / 2;
      y = scaleY;
    } else {
      // Trasferta: porta a destra, tiri verso sinistra
      x = 50 - scaleX / 2;
      y = 100 - scaleY;
    }
    return { x, y };
  };

  // Colore in gradiente da bianco (xG=0) a rosso (xG=1)
  const getShotColor = (xG: number) => {
    const gb = Math.floor(255 * (1 - xG));
    return `rgb(255, ${gb}, ${gb})`;
  };

  // Dimensione proporzionale alla radice di xG (per attenuare)
  const getShotSize = (xG: number) => Math.sqrt(xG) * 7;

  // Trova un tiro ad alto xG per mostrare il tooltip simulato (per demo)
  const highlightedShot = shots.find(s => s.xG > 0.8) || shots[0];

  return (
    <div className="relative w-full max-w-6xl mx-auto p-6 bg-slate-900/80 backdrop-blur-sm rounded-2xl border border-white/5 shadow-2xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white tracking-tight">PREMIUM MATCH ANALYSIS</h1>
        <p className="text-white/60 text-sm font-mono mt-1">Genoa vs Lecce • Serie B 2025/26 • Match ID: {matchId}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Campo centrale */}
        <div className="lg:col-span-2 relative">
          <div className="relative w-full aspect-[105/68] bg-emerald-900 rounded-xl border border-white/10 overflow-hidden shadow-[0_10px_50px_rgba(0,0,0,0.5)]">
            {/* SVG del campo */}
            <svg viewBox="0 0 100 100" className="absolute inset-0 w-full h-full stroke-white/10 fill-none">
              {/* Rettangolo esterno */}
              <rect x="0" y="0" width="100" height="100" strokeWidth="0.3" />
              {/* Linea centrale */}
              <line x1="50" y1="0" x2="50" y2="100" strokeWidth="0.3" />
              {/* Cerchio centrale */}
              <circle cx="50" cy="50" r="8" strokeWidth="0.3" />
              {/* Aree di porta sinistra (casa) */}
              <rect x="0" y="20" width="16" height="60" strokeWidth="0.3" />
              <rect x="0" y="36" width="5.5" height="28" strokeWidth="0.3" />
              {/* Aree di porta destra (trasferta) */}
              <rect x="84" y="20" width="16" height="60" strokeWidth="0.3" />
              <rect x="94.5" y="36" width="5.5" height="28" strokeWidth="0.3" />
              {/* Punti del dischetto */}
              <circle cx="11" cy="50" r="0.8" fill="white" />
              <circle cx="89" cy="50" r="0.8" fill="white" />
              <circle cx="50" cy="50" r="0.8" fill="white" />

              {/* Definizione simbolo pallone */}
              <defs>
                <symbol id="soccer-ball" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="10" fill="white" stroke="black" strokeWidth="0.8" />
                  <path d="M12 7 L14 10 L12 13 L10 10 Z" fill="black" />
                  <path d="M17 10 L15 13 L17 16 L19 13 Z" fill="black" />
                  <path d="M7 10 L5 13 L7 16 L9 13 Z" fill="black" />
                  <path d="M12 17 L10 20 L12 23 L14 20 Z" fill="black" />
                  <path d="M12 2 L10 5 L12 8 L14 5 Z" fill="black" />
                </symbol>
              </defs>

              {/* Layer tiri */}
              <AnimatePresence>
                {shots.map((shot, i) => {
                  const { x, y } = mapCoordinates(shot);
                  const isGoal = shot.result === 'Goal';
                  const size = getShotSize(shot.xG);
                  const color = getShotColor(shot.xG);

                  return (
                    <motion.g
                      key={i}
                      initial={{ scale: 0, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ delay: i * 0.02, type: 'spring', stiffness: 250 }}
                    >
                      {/* Aura pulsante per i gol */}
                      {isGoal && (
                        <circle cx={x} cy={y} r={size * 1.8} fill="#10b981" opacity="0.3">
                          <animate attributeName="r" values={`${size*1.8};${size*2.5};${size*1.8}`} dur="2s" repeatCount="indefinite" />
                          <animate attributeName="opacity" values="0.3;0.6;0.3" dur="2s" repeatCount="indefinite" />
                        </circle>
                      )}

                      {isGoal ? (
                        // Icona pallone per i gol
                        <use href="#soccer-ball" x={x - 1.2} y={y - 1.2} width="2.4" height="2.4" className="drop-shadow-lg" />
                      ) : (
                        // Cerchio colorato per i tiri non gol
                        <circle
                          cx={x} cy={y} r={size}
                          fill={color} fillOpacity={0.85}
                          stroke="white" strokeWidth="0.15"
                          className="cursor-pointer hover:stroke-[0.3] transition-all"
                        />
                      )}

                      {/* Etichetta xG per tiri pericolosi (xG > 0.3) */}
                      {shot.xG > 0.3 && (
                        <text
                          x={x}
                          y={y - size - 1.5}
                          fontSize="1.8"
                          fill="white"
                          textAnchor="middle"
                          fontWeight="bold"
                          className="font-mono pointer-events-none"
                        >
                          {shot.xG.toFixed(2)}
                        </text>
                      )}
                    </motion.g>
                  );
                })}
              </AnimatePresence>
            </svg>

            {/* Tooltip simulato sul tiro evidenziato */}
            {highlightedShot && (
              <div
                className="absolute transform -translate-x-1/2 -translate-y-full"
                style={{
                  left: `${mapCoordinates(highlightedShot).x}%`,
                  top: `${mapCoordinates(highlightedShot).y}%`,
                }}
              >
                <div className="relative bg-black/90 backdrop-blur-sm text-white text-xs p-3 rounded-lg border border-white/20 shadow-2xl min-w-[200px]">
                  <div className="font-bold mb-1 text-emerald-300">Player: {highlightedShot.player}</div>
                  <div className="grid grid-cols-2 gap-1">
                    <span className="text-white/70">Minute:</span>
                    <span className="font-mono">{highlightedShot.minute}'</span>
                    <span className="text-white/70">xG:</span>
                    <span className="font-mono text-red-300 font-bold">{highlightedShot.xG.toFixed(3)}</span>
                    <span className="text-white/70">Result:</span>
                    <span className="font-mono">{highlightedShot.result}</span>
                    <span className="text-white/70">Body Part:</span>
                    <span className="font-mono">Foot</span>
                  </div>
                  <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-full w-0 h-0 border-l-8 border-r-8 border-t-8 border-l-transparent border-r-transparent border-t-black/90"></div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Legenda e statistiche */}
        <div className="space-y-6">
          <div className="bg-white/5 rounded-xl p-5 border border-white/10">
            <h3 className="text-lg font-bold text-white mb-3">Shot Gradient Legend</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-white/70 text-sm">Low xG (0.0)</span>
                <span className="text-white/70 text-sm">High xG (1.0)</span>
              </div>
              <div className="h-4 rounded-full overflow-hidden bg-gradient-to-r from-white via-red-200 to-red-600" />
              <div className="grid grid-cols-5 text-xs text-white/50 text-center mt-1">
                <span>0.0</span>
                <span>0.25</span>
                <span>0.5</span>
                <span>0.75</span>
                <span>1.0</span>
              </div>
            </div>
            <div className="mt-6">
              <h4 className="text-white font-bold mb-2">Icons Meaning</h4>
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <div className="w-4 h-4 rounded-full bg-white/80"></div>
                  <span className="text-white/80 text-sm">Shot (circle)</span>
                </div>
                <div className="flex items-center gap-3">
                  <svg width="20" height="20" viewBox="0 0 24 24" className="fill-white stroke-black stroke-1">
                    <use href="#soccer-ball" />
                  </svg>
                  <span className="text-white/80 text-sm">Goal (soccer ball)</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-4 h-4 rounded-full bg-emerald-500/30 relative">
                    <div className="absolute inset-0 rounded-full border border-emerald-500/50 animate-ping"></div>
                  </div>
                  <span className="text-white/80 text-sm">Goal aura (pulsing)</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white/5 rounded-xl p-5 border border-white/10">
            <h3 className="text-lg font-bold text-white mb-3">Match Summary</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-white/70">Total Shots</span>
                <span className="text-white font-mono">{shots.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">Goals</span>
                <span className="text-white font-mono">{shots.filter(s => s.result === 'Goal').length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">Total xG</span>
                <span className="text-white font-mono">{shots.reduce((acc, s) => acc + s.xG, 0).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">Average xG per Shot</span>
                <span className="text-white font-mono">{(shots.reduce((acc, s) => acc + s.xG, 0) / shots.length || 0).toFixed(3)}</span>
              </div>
            </div>
          </div>

          <div className="text-white/50 text-xs font-mono text-center pt-4">
            Advanced Analytics Engine • Precision mapping
          </div>
        </div>
      </div>
    </div>
  );
}