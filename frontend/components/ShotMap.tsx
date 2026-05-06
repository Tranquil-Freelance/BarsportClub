'use client';
import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Target, Zap, Circle } from 'lucide-react';

interface Shot {
  minute: number;
  player: string;
  xG: number;
  X: number;
  Y: number;
  result: string;
  team_type: string;
}

interface ShotMapProps {
  matchId: number;
}

export default function ShotMap({ matchId }: ShotMapProps) {
  const [shots, setShots] = useState<Shot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchShots = async () => {
      try {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const response = await fetch(`${apiBase}/api/v1/analytics/match/${matchId}/shots`);
        if (!response.ok) {
          throw new Error("Errore nel recupero dei tiri o match non trovato.");
        }
        const data = await response.json();
        setShots(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchShots();
  }, [matchId]);

  const getShotColor = (result: string, teamType: string) => {
    if (result === 'Goal') return '#10b981';
    if (result === 'OwnGoal') return '#ef4444';
    return teamType === 'h' ? '#3b82f6' : '#f59e0b';
  };

  // FIX 1: Restituisce ESATTAMENTE l'ID definito nel blocco <defs>
  const getShotGradientId = (shot: Shot) => {
    if (shot.result === 'Goal') return 'gradient-goal';
    if (shot.result === 'OwnGoal') return 'gradient-owngoal';
    return shot.team_type === 'h' ? 'gradient-home' : 'gradient-away';
  };

  const getShotRadius = (xG: number) => {
    // Gestione difensiva: se l'API manda una stringa, la converto
    const validXG = typeof xG === 'string' ? parseFloat(xG) : xG;
    return 2 + (validXG * 6);
  };

  const toSvgCoords = (shot: Shot): [number, number] => {
    const validX = typeof shot.X === 'string' ? parseFloat(shot.X) : shot.X;
    const validY = typeof shot.Y === 'string' ? parseFloat(shot.Y) : shot.Y;
    
    let x = validX * 100;
    let y = validY * 100;
    
    if (shot.team_type === 'a') {
      x = 100 - x;
      y = 100 - y;
    }
    return [x, y];
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64 bg-gradient-to-br from-slate-900 via-black to-black rounded-2xl border border-slate-800 shadow-2xl">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-emerald-500"></div>
        <p className="mt-4 text-slate-300 text-lg font-medium">Caricamento mappa tiri...</p>
        <p className="text-sm text-slate-500">Preparazione dati in corso</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="bg-red-950/30 border border-red-800 text-red-300 p-6 rounded-2xl shadow-xl">
      <div className="flex items-center gap-3">
        <Circle className="w-6 h-6" />
        <div>
          <h3 className="font-bold">Errore di caricamento</h3>
          <p>{error}</p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-4xl font-black tracking-tight text-white mb-2">
          MASTER SHOT MAP <span className="text-emerald-400 font-bold">[SVG Precision]</span>
        </h2>
        <p className="text-slate-400 text-lg max-w-3xl mx-auto">
          Jeder Schuss ist ein Kunstwerk: Radialverläufe, Smaragd-Glow und pulsierende Aura für xG {'>'} 0.4.
          <br />
          <span className="text-sm text-slate-500">Koordinaten auf viewBox 0&#8209;100 millimetergenau abgebildet.</span>
        </p>
      </div>

      {/* SVG Field Container */}
      <div className="relative w-full bg-gradient-to-br from-slate-900 via-black to-black rounded-3xl border border-slate-800 shadow-2xl shadow-black/70 overflow-hidden">
        <svg
          viewBox="0 0 100 100"
          className="w-full h-auto"
          preserveAspectRatio="xMidYMid meet"
        >
          <defs>
            <radialGradient id="field-bg" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#0f172a" stopOpacity="1" />
              <stop offset="100%" stopColor="#020617" stopOpacity="1" />
            </radialGradient>

            <radialGradient id="gradient-goal" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0.1" />
            </radialGradient>
            
            <radialGradient id="gradient-home" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.1" />
            </radialGradient>
            
            <radialGradient id="gradient-away" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.1" />
            </radialGradient>
            
            <radialGradient id="gradient-owngoal" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#ef4444" stopOpacity="0.1" />
            </radialGradient>

            <filter id="goal-glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Field background */}
          <rect x="0" y="0" width="100" height="100" fill="url(#field-bg)" />

          {/* Field lines */}
          <g stroke="white" strokeWidth="0.5" strokeOpacity="0.15" strokeDasharray="1,1">
            <rect x="0" y="0" width="100" height="100" fill="none" />
            <line x1="50" y1="0" x2="50" y2="100" />
            <circle cx="50" cy="50" r="9.15" fill="none" />
            <rect x="0" y="21" width="16.5" height="58" fill="none" />
            <rect x="83.5" y="21" width="16.5" height="58" fill="none" />
            <rect x="0" y="36" width="5.5" height="28" fill="none" />
            <rect x="94.5" y="36" width="5.5" height="28" fill="none" />
            <circle cx="11" cy="50" r="0.6" fill="white" />
            <circle cx="89" cy="50" r="0.6" fill="white" />
            <circle cx="50" cy="50" r="0.6" fill="white" />
          </g>

          {/* Shots */}
          {shots.map((shot, index) => {
            const [x, y] = toSvgCoords(shot);
            const rawXG = typeof shot.xG === 'string' ? parseFloat(shot.xG) : shot.xG;
            const radius = getShotRadius(rawXG);
            const isGoal = shot.result === 'Goal';
            const isHighXG = rawXG > 0.4;
            const gradientId = getShotGradientId(shot);

            return (
              <g key={index}>
                {/* Pulsating aura for high xG */}
                {isHighXG && (
                  <motion.circle
                    cx={x}
                    cy={y}
                    r={radius + 3}
                    stroke={getShotColor(shot.result, shot.team_type)}
                    strokeWidth="1"
                    fill="none"
                    initial={{ opacity: 0.6, scale: 1 }}
                    animate={{ opacity: [0.2, 0.6, 0.2], scale: [1, 1.3, 1] }}
                    transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
                    style={{ transformOrigin: `${x}px ${y}px` }}
                  />
                )}

                {/* Glow effect for goals */}
                {isGoal && (
                  <circle
                    cx={x}
                    cy={y}
                    r={radius + 2}
                    fill="url(#gradient-goal)"
                    opacity="0.7"
                    filter="url(#goal-glow)"
                  />
                )}

                {/* FIX 2: Correct Scaling on Hover using standard CSS scale + transformOrigin */}
                <circle
                  cx={x}
                  cy={y}
                  r={radius}
                  fill={`url(#${gradientId})`}
                  stroke="rgba(255,255,255,0.9)"
                  strokeWidth="0.4"
                  className="transition-transform duration-300 hover:scale-125 cursor-pointer"
                  style={{ transformOrigin: `${x}px ${y}px` }}
                />

                {/* Central number for high xG */}
                {isHighXG && (
                  <text
                    x={x}
                    y={y}
                    textAnchor="middle"
                    dy="0.3em"
                    fontSize="3.5"
                    fill="white"
                    fontWeight="900"
                    className="select-none pointer-events-none"
                  >
                    {rawXG.toFixed(2)}
                  </text>
                )}

                {/* Tooltip equivalent */}
                <title>
                  {shot.player} ({shot.minute}') - xG: {rawXG.toFixed(2)} - {shot.result}
                </title>
              </g>
            );
          })}
        </svg>

        {/* Animated corner badges */}
        <div className="absolute top-4 left-4 bg-gradient-to-r from-emerald-900/30 to-emerald-800/20 border border-emerald-700/40 rounded-full px-4 py-2 backdrop-blur-sm pointer-events-none">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-emerald-400" />
            <span className="text-sm font-semibold text-emerald-300">SVG Precision Layer</span>
          </div>
        </div>
        <div className="absolute top-4 right-4 bg-gradient-to-r from-blue-900/30 to-blue-800/20 border border-blue-700/40 rounded-full px-4 py-2 backdrop-blur-sm pointer-events-none">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-blue-400" />
            <span className="text-sm font-semibold text-blue-300">Live xG Mapping</span>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 justify-center">
        <div className="flex items-center gap-3 px-5 py-3 bg-gradient-to-r from-slate-900/60 to-black/60 rounded-xl border border-slate-800 backdrop-blur-sm">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-800 shadow-[0_0_15px_rgba(16,185,129,0.7)]"></div>
          <span className="text-white font-bold">Gol (Glow smeraldo)</span>
        </div>
        <div className="flex items-center gap-3 px-5 py-3 bg-gradient-to-r from-slate-900/60 to-black/60 rounded-xl border border-slate-800 backdrop-blur-sm">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-blue-800"></div>
          <span className="text-white font-bold">Tiri Casa</span>
        </div>
        <div className="flex items-center gap-3 px-5 py-3 bg-gradient-to-r from-slate-900/60 to-black/60 rounded-xl border border-slate-800 backdrop-blur-sm">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-amber-500 to-amber-800"></div>
          <span className="text-white font-bold">Tiri Ospite</span>
        </div>
        <div className="flex items-center gap-3 px-5 py-3 bg-gradient-to-r from-slate-900/60 to-black/60 rounded-xl border border-slate-800 backdrop-blur-sm">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-red-500 to-red-800"></div>
          <span className="text-white font-bold">Autogol</span>
        </div>
        <div className="flex items-center gap-3 px-5 py-3 bg-gradient-to-r from-slate-900/60 to-black/60 rounded-xl border border-slate-800 backdrop-blur-sm">
          <div className="w-6 h-6 rounded-full border-2 border-white/60 bg-transparent"></div>
          <span className="text-slate-300 font-medium">Dimensione = xG</span>
        </div>
        <div className="flex items-center gap-3 px-5 py-3 bg-gradient-to-r from-slate-900/60 to-black/60 rounded-xl border border-slate-800 backdrop-blur-sm">
          <div className="w-6 h-6 rounded-full border-2 border-emerald-500/60 bg-transparent animate-pulse"></div>
          <span className="text-emerald-300 font-medium">Aura (xG &gt; 0.4)</span>
        </div>
      </div>

      <p className="text-center text-sm text-slate-500 mt-6">
        *Coordinate mappate in SVG (0–100) con precisione millimetrica. Passa il cursore sui cerchi per i dettagli.
      </p>
    </div>
  );
}
