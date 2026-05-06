'use client';

import React, { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';

// Interfaccia espansa per intercettare vari formati JSON dal backend
interface Shot {
  minute: number | string;
  xG: number | string;
  team_type?: 'h' | 'a' | 'Home' | 'Away';
  h_a?: 'h' | 'a';
  player?: string;
  player_id?: string;
  result?: string;
  situation?: string;
  shotType?: string;
}

export default function XGFlowChart({ matchId }: { matchId: number }) {
  const [options, setOptions] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // 1. Fetching Maniacale
    fetch(`http://127.0.0.1:8001/api/v1/analytics/match/${matchId}/shots`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP Error: ${res.status} - Impossibile raggiungere il backend.`);
        return res.json();
      })
      .then((rawData: any) => {
        console.log("DATI GREZZI DAL BACKEND:", rawData); // LOG PER DEBUG OBBLIGATORIO

        // 2. Normalizzazione del dato (Fix per i formati strani di Understat)
        let processedShots: Shot[] = [];
        
        if (Array.isArray(rawData)) {
          processedShots = rawData;
        } else if (rawData && rawData.h && rawData.a) {
          // Formato nativo Understat
          const homeShots = Object.values(rawData.h).map((s: any) => ({ ...s, team_type: 'h' }));
          const awayShots = Object.values(rawData.a).map((s: any) => ({ ...s, team_type: 'a' }));
          processedShots = [...homeShots, ...awayShots] as Shot[];
        } else if (rawData && rawData.shots) {
          processedShots = rawData.shots;
        } else {
          throw new Error("Formato dati sconosciuto. Guarda la console del browser.");
        }

        if (processedShots.length === 0) {
          throw new Error("L'API ha restituito zero tiri. Il DB è vuoto per questo match ID.");
        }

        // 3. Ordinamento cronologico assoluto
        const sortedShots = processedShots.sort((a, b) => {
          const minA = typeof a.minute === 'string' ? parseInt(a.minute, 10) : a.minute;
          const minB = typeof b.minute === 'string' ? parseInt(b.minute, 10) : b.minute;
          return minA - minB;
        });

        // 4. Calcolo Cumulativo (Step Chart Logic)
        let homeXG = 0;
        let awayXG = 0;

        const homeData: number[][] = [[0, 0]];
        const awayData: number[][] = [[0, 0]];

        sortedShots.forEach(shot => {
          const min = typeof shot.minute === 'string' ? parseInt(shot.minute, 10) : shot.minute;
          const xgVal = typeof shot.xG === 'string' ? parseFloat(shot.xG) : shot.xG;
          const team = shot.team_type || shot.h_a;

          if (team === 'h' || team === 'Home') {
            homeXG += xgVal;
            homeData.push([min, parseFloat(homeXG.toFixed(2))]);
            awayData.push([min, parseFloat(awayXG.toFixed(2))]);
          } else {
            awayXG += xgVal;
            awayData.push([min, parseFloat(awayXG.toFixed(2))]);
            homeData.push([min, parseFloat(homeXG.toFixed(2))]);
          }
        });

        // Chiusura del grafico al 90° (o oltre i minuti di recupero)
        const lastShotMin = sortedShots.length > 0 
          ? (typeof sortedShots[sortedShots.length - 1].minute === 'string' 
              ? parseInt(sortedShots[sortedShots.length - 1].minute as string, 10) 
              : sortedShots[sortedShots.length - 1].minute)
          : 90;
        const finalMin = Math.max(90, lastShotMin as number);
        
        homeData.push([finalMin, parseFloat(homeXG.toFixed(2))]);
        awayData.push([finalMin, parseFloat(awayXG.toFixed(2))]);

        // 5. Configurazione ECharts Premium (Design di Alto Livello)
        const chartOption = {
          backgroundColor: 'transparent',
          color: ['#10b981', '#f43f5e'], // Smeraldo per Home, Rosso Corsa per Away
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'cross',
              lineStyle: { color: '#334155', type: 'dashed' },
              crossStyle: { color: '#334155' }
            },
            backgroundColor: 'rgba(15, 23, 42, 0.95)',
            borderColor: '#334155',
            borderWidth: 1,
            padding: 16,
            textStyle: { color: '#f8fafc' },
            formatter: function (params: any) {
              const minute = params[0].axisValue;
              let html = `<div style="font-family: monospace; font-weight: bold; margin-bottom: 8px; border-bottom: 1px solid #334155; padding-bottom: 4px;">Minute: ${minute}'</div>`;
              params.forEach((param: any) => {
                const isHome = param.seriesName === 'Home xG';
                const color = isHome ? '#10b981' : '#f43f5e';
                html += `<div style="display: flex; justify-content: space-between; align-items: center; width: 140px; margin-top: 4px;">
                           <span style="color: ${color}; font-family: sans-serif; font-size: 12px;">${param.seriesName}</span>
                           <span style="font-family: monospace; font-weight: bold; color: #fff;">${param.data[1].toFixed(2)}</span>
                         </div>`;
              });
              return html;
            }
          },
          legend: {
            data: ['Home xG', 'Away xG'],
            textStyle: { color: '#94a3b8', fontFamily: 'sans-serif', fontWeight: 600 },
            icon: 'roundRect',
            top: 0,
            right: '2%'
          },
          grid: {
            left: '3%',
            right: '4%',
            bottom: '5%',
            top: '15%',
            containLabel: true
          },
          xAxis: {
            type: 'value',
            min: 0,
            max: finalMin,
            splitLine: { show: true, lineStyle: { color: '#1e293b', opacity: 0.5 } },
            axisLine: { lineStyle: { color: '#334155' } },
            axisLabel: { color: '#64748b', fontFamily: 'monospace', formatter: '{value}\'' },
            axisTick: { show: false }
          },
          yAxis: {
            type: 'value',
            name: 'Expected Goals',
            nameTextStyle: { color: '#64748b', padding: [0, 0, 0, 20] },
            splitLine: { show: true, lineStyle: { color: '#1e293b', type: 'dashed' } },
            axisLabel: { color: '#64748b', fontFamily: 'monospace', formatter: (val: number) => val.toFixed(1) }
          },
          series: [
            {
              name: 'Home xG',
              type: 'line',
              step: 'end',
              data: homeData,
              showSymbol: false,
              lineStyle: { width: 3, shadowColor: 'rgba(16, 185, 129, 0.5)', shadowBlur: 10, shadowOffsetY: 3 },
              areaStyle: {
                color: {
                  type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
                  colorStops: [
                    { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
                    { offset: 1, color: 'rgba(16, 185, 129, 0.0)' }
                  ]
                }
              }
            },
            {
              name: 'Away xG',
              type: 'line',
              step: 'end',
              data: awayData,
              showSymbol: false,
              lineStyle: { width: 3, shadowColor: 'rgba(244, 63, 94, 0.5)', shadowBlur: 10, shadowOffsetY: 3 },
              areaStyle: {
                color: {
                  type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
                  colorStops: [
                    { offset: 0, color: 'rgba(244, 63, 94, 0.3)' },
                    { offset: 1, color: 'rgba(244, 63, 94, 0.0)' }
                  ]
                }
              }
            }
          ]
        };

        setOptions(chartOption);
        setLoading(false);
      })
      .catch(err => {
        console.error("ERRORE XG FLOW CHART:", err);
        setError(err.message);
        setLoading(false);
      });
  }, [matchId]);

  if (loading) {
    return (
      <div className="w-full aspect-[21/9] bg-slate-950 flex flex-col items-center justify-center border border-white/10 rounded-xl shadow-2xl">
        <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mb-4"></div>
        <span className="text-emerald-500 font-mono text-sm tracking-widest uppercase animate-pulse">Inizializzazione Motore Grafico...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full aspect-[21/9] bg-slate-950 flex flex-col items-center justify-center border border-red-500/30 rounded-xl shadow-2xl p-6">
        <svg className="w-10 h-10 text-red-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
        <span className="text-red-500 font-mono text-sm text-center">ERRORE CRITICO DATI:<br/><br/>{error}</span>
        <span className="text-slate-500 font-mono text-xs mt-4">Premi F12 e controlla la Console per i dettagli del JSON.</span>
      </div>
    );
  }

  return (
    <div className="w-full bg-slate-950 rounded-xl border border-white/10 p-6 shadow-[0_0_40px_rgba(0,0,0,0.5)]">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
        <h3 className="text-white font-black uppercase tracking-[0.2em] text-sm">xG Match Flow</h3>
      </div>
      <ReactECharts 
        option={options} 
        style={{ height: '400px', width: '100%' }} 
        theme="dark"
        opts={{ renderer: 'svg' }}
      />
    </div>
  );
}