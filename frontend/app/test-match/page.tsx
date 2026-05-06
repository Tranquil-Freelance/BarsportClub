"use client"

import React, { useEffect, useState } from "react"
import dynamic from "next/dynamic"
import { motion, AnimatePresence } from "framer-motion"

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false })

/* -------------------------------------------------- */
/* INTERFACCE AGGIORNATE: DEEP DATA SCHEMA */
/* -------------------------------------------------- */

interface Shot {
  minute: number
  X: number
  Y: number
  xG: number
  team_type: "h" | "a"
  player: string
  result: string
  situation: string       // ES: "OpenPlay", "FromCorner"
  shotType: string        // ES: "LeftFoot", "Head"
  assist: string | null   // Il nome di chi ha fatto il passaggio
}

/* -------------------------------------------------- */
/* MAIN DASHBOARD PAGE */
/* -------------------------------------------------- */

export default function DeepDataDashboard() {
  const matchId = 27362; // Genoa vs Inter (Dati Reali/Simulati da DB)
  const [shots, setShots] = useState<Shot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Usiamo l'URL che Roo ha confermato essere funzionante (Senza prefissi extra)
    fetch(`http://127.0.0.1:8001/match/${matchId}/shots`)
      .then(res => {
        if (!res.ok) throw new Error('Errore nella risposta del server.');
        return res.json();
      })
      .then((data: any) => {
        let rawShots: any[] = [];
        
        // Roo restituisce ora una struttura {match: ..., shots: {h: [...], a: [...]}}
        if (data && data.shots) {
          const home = data.shots.h.map((s: any) => ({ ...s, team_type: 'h' }));
          const away = data.shots.a.map((s: any) => ({ ...s, team_type: 'a' }));
          rawShots = [...home, ...away];
        } else {
          throw new Error("Formato dati non compatibile.");
        }

        const processedShots: Shot[] = rawShots.map(s => ({
          minute: Number(s.minute),
          X: Number(s.X),
          Y: Number(s.Y),
          xG: Number(s.xG),
          team_type: s.team_type,
          player: s.player,
          result: s.result,
          situation: s.situation || "N/A",
          shotType: s.shotType || "N/A",
          assist: s.player_assisted || s.assist || null
        })).sort((a, b) => a.minute - b.minute);

        setShots(processedShots);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [matchId]);

  const buildXGSeries = () => {
    let home = 0; let away = 0;
    const hData: any[] = [[0, 0]]; const aData: any[] = [[0, 0]];

    shots.forEach(s => {
      if (s.team_type === "h") {
        home += s.xG;
        hData.push([s.minute, parseFloat(home.toFixed(2))]);
        aData.push([s.minute, parseFloat(away.toFixed(2))]);
      } else {
        away += s.xG;
        aData.push([s.minute, parseFloat(away.toFixed(2))]);
        hData.push([s.minute, parseFloat(home.toFixed(2))]);
      }
    });

    const finalMin = Math.max(95, shots.length > 0 ? shots[shots.length - 1].minute : 90);
    hData.push([finalMin, parseFloat(home.toFixed(2))]);
    aData.push([finalMin, parseFloat(away.toFixed(2))]);

    return { hData, aData, finalMin, tH: home.toFixed(2), tA: away.toFixed(2) };
  };

  if (loading) return <div className="min-h-screen bg-[#05070a] flex items-center justify-center text-[#00FFA3] font-mono tracking-tighter text-2xl animate-pulse">CARICAMENTO DEEP DATA...</div>;
  if (error) return <div className="min-h-screen bg-[#05070a] flex items-center justify-center text-red-500 font-mono italic">ERRORE: {error}</div>;

  const { hData, aData, finalMin, tH, tA } = buildXGSeries();

  return (
    <div className="min-h-screen bg-[#05070a] text-slate-200 p-6 space-y-8 font-sans">
      
      {/* HEADER DINAMICO */}
      <header className="flex justify-between items-end border-b border-white/10 pb-6">
        <div>
          <h1 className="text-4xl font-black tracking-tighter text-white">X-PALERMO <span className="text-[#00FFA3]">ANALYTICS</span></h1>
          <p className="text-slate-500 text-sm font-mono mt-1">MATCH ENGINE V0.1 • DEEP DATA INTEGRATED</p>
        </div>
        <div className="flex gap-10 text-right">
          <div>
            <p className="text-xs text-white/40 uppercase">Expected Goals (H)</p>
            <p className="text-3xl font-bold text-[#00FFA3]">{tH}</p>
          </div>
          <div>
            <p className="text-xs text-white/40 uppercase">Expected Goals (A)</p>
            <p className="text-3xl font-bold text-[#FF3C6A]">{tA}</p>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* MAPPA TIRI (PROPRECISION) */}
        <div className="lg:col-span-7 bg-white/5 rounded-3xl p-6 border border-white/10 relative overflow-hidden">
          <h3 className="text-xs font-bold text-white/30 uppercase mb-4">Master Pitch Visualization</h3>
          <div className="aspect-[1.5/1] relative bg-[#0a1f16] rounded-xl border border-white/5">
            <svg viewBox="0 0 100 100" className="w-full h-full opacity-40">
               <rect x="0" y="0" width="100" height="100" fill="none" stroke="white" strokeWidth="0.5" />
               <line x1="50" y1="0" x2="50" y2="100" stroke="white" strokeWidth="0.5" />
               <circle cx="50" cy="50" r="9.15" fill="none" stroke="white" strokeWidth="0.5" />
               <rect x="0" y="21" width="16.5" height="58" fill="none" stroke="white" strokeWidth="0.5" />
               <rect x="83.5" y="21" width="16.5" height="58" fill="none" stroke="white" strokeWidth="0.5" />
            </svg>
            
            {shots.map((s, i) => (
              <motion.div
                key={i}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: i * 0.02 }}
                style={{
                  position: 'absolute',
                  left: `${s.team_type === 'h' ? s.X * 100 : (1 - s.X) * 100}%`,
                  top: `${s.team_type === 'h' ? s.Y * 100 : (1 - s.Y) * 100}%`,
                  width: `${8 + s.xG * 30}px`,
                  height: `${8 + s.xG * 30}px`,
                  backgroundColor: s.team_type === 'h' ? '#00FFA3' : '#FF3C6A',
                  borderRadius: '50%',
                  boxShadow: s.result === 'Goal' ? `0 0 20px ${s.team_type === 'h' ? '#00FFA3' : '#FF3C6A'}` : 'none',
                  border: '2px solid rgba(255,255,255,0.3)',
                  cursor: 'pointer'
                }}
                className="group z-10"
              >
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 bg-black/90 p-3 rounded-lg border border-white/20 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none text-xs">
                  <p className="font-bold text-white mb-1">{s.player}</p>
                  <p className="text-white/60">Minuto: <span className="text-white">{s.minute}'</span></p>
                  <p className="text-white/60">xG: <span className="text-white">{s.xG.toFixed(2)}</span></p>
                  <p className="text-white/60">Azione: <span className="text-white">{s.situation}</span></p>
                  <p className="text-white/60">Tiro: <span className="text-white">{s.shotType}</span></p>
                  {s.assist && <p className="text-blue-400 mt-1">Assist: {s.assist}</p>}
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* FEED EVENTI LATERALE */}
        <div className="lg:col-span-5 bg-white/5 rounded-3xl p-6 border border-white/10 flex flex-col">
          <h3 className="text-xs font-bold text-white/30 uppercase mb-4">Deep Data Shot Feed</h3>
          <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
            {shots.slice().reverse().map((s, i) => (
              <div key={i} className="bg-white/5 p-3 rounded-xl flex items-center justify-between border-l-4 border-l-white/10 hover:border-l-[#00FFA3] transition-colors">
                <div>
                  <p className="text-sm font-bold text-white">{s.player}</p>
                  <p className="text-[10px] text-white/40">{s.situation} • {s.shotType}</p>
                  {s.assist && <p className="text-[10px] text-blue-400/80 italic">Assist by {s.assist}</p>}
                </div>
                <div className="text-right">
                  <p className={`text-xs font-mono ${s.result === 'Goal' ? 'text-[#00FFA3]' : 'text-white/20'}`}>
                    {s.result === 'Goal' ? 'GOAL' : s.result}
                  </p>
                  <p className="text-[10px] font-mono text-white/40">{s.xG.toFixed(2)} xG</p>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* FOOTER: XG FLOW */}
      <div className="bg-white/5 rounded-3xl p-6 border border-white/10">
        <h3 className="text-xs font-bold text-white/30 uppercase mb-4">Expected Goals Flow (Meritometro)</h3>
        <ReactECharts 
          option={{
            backgroundColor: 'transparent',
            grid: { top: 20, bottom: 40, left: 50, right: 20 },
            xAxis: { type: 'value', min: 0, max: finalMin, splitLine: { show: false } },
            yAxis: { type: 'value', splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } } },
            series: [
              { name: 'Casa', type: 'line', step: 'end', data: hData, color: '#00FFA3', symbol: 'none', lineStyle: { width: 4 } },
              { name: 'Trasferta', type: 'line', step: 'end', data: aData, color: '#FF3C6A', symbol: 'none', lineStyle: { width: 4 } }
            ]
          }} 
          style={{ height: '250px' }} 
        />
      </div>
    </div>
  )
}