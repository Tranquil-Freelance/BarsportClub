"use client";

import React, { useEffect, useState } from 'react';

// ==========================================
// 1. DEFINIZIONE DEI TIPI TYPESCRIPT
// ==========================================
interface TeamDetails {
  occasioni_nitide: number;
  azioni_promettenti: number;
  tiri_in_area: number;
  tiri_fuori_area: number;
  rigori: number;
}

interface ImrScore {
  home: number;
  away: number;
}

interface TimelinePoint {
  minute: number;
  home_imr: number;
  away_imr: number;
}

interface GoalEvent {
  minute: number;
  team: 'h' | 'a';
}

interface MeritometroData {
  match_id?: number;
  home_name?: string;
  away_name?: string;
  home_score?: number;
  away_score?: number;
  home_xG?: number;
  away_xG?: number;
  imr_score: ImrScore;
  timeline: TimelinePoint[];
  goals_timeline?: GoalEvent[];
  dettagli_home: TeamDetails;
  dettagli_away: TeamDetails;
  error?: string;
}

interface MeritometroCardProps {
  matchId: string | number;
}

// ==========================================
// 2. MOTORE DEL COMMENTO A CALDO (FILOSOFIA IMR)
// ==========================================
const generaCommentoACaldo = (data: MeritometroData) => {
  const { home_name, away_name, home_score, away_score, imr_score } = data;
  
  if (home_score === undefined || away_score === undefined) return "In attesa dei dati completi per l'analisi...";

  const hName = home_name || "La squadra di casa";
  const aName = away_name || "La formazione ospite";
  const diffIMR = Math.abs(imr_score.home - imr_score.away);
  
  let testo = "";

  // Scenario 1: Sconfitta Immeritata (Risultato e IMR in disaccordo netto)
  if (home_score < away_score && imr_score.home > imr_score.away + 5) {
    testo = `La cronaca parla di una vittoria per ${aName}, ma il nostro algoritmo decreta un'altra verità. Ai punti, il Meritometro assegna la partita senza appello a ${hName} (${imr_score.home} a ${imr_score.away}). Chi ha vinto ha avuto il solo merito di trovare il gol e resistere, ma la supremazia in campo e la mole di gioco raccontano un assedio che non è stato premiato dal tabellone.`;
  } else if (away_score < home_score && imr_score.away > imr_score.home + 5) {
    testo = `Il tabellino sorride a ${hName}, ma l'Indice di Merito non fa sconti. Secondo il nostro algoritmo, ai punti avrebbe meritato nettamente ${aName} (${imr_score.away} a ${imr_score.home}). I padroni di casa vincono capitalizzando gli episodi e difendendo il fortino, ma la reale produzione offensiva è stata dominata dagli avversari.`;
  } 
  // Scenario 2: Vittoria Assoluta (Risultato e IMR d'accordo)
  else if (home_score > away_score && imr_score.home > imr_score.away + 5) {
    testo = `Vittoria ineccepibile e certificata dall'algoritmo. ${hName} non solo porta a casa il risultato, ma lo fa legittimando il punteggio con un dominio assoluto nella produzione offensiva (IMR ${imr_score.home} a ${imr_score.away}). ${aName} si è limitata a subire le iniziative avversarie.`;
  } else if (away_score > home_score && imr_score.away > imr_score.home + 5) {
    testo = `Una supremazia totale da parte di ${aName}, che s'impone nel risultato e nei numeri. Il Meritometro conferma che la vittoria esterna è frutto di un controllo totale della produzione offensiva (IMR ${imr_score.away} a ${imr_score.home}), togliendo respiro a ${hName}.`;
  }
  // Scenario 3: Pareggio o vittoria sofferta (IMR equilibrato)
  else if (home_score === away_score) {
    if (diffIMR > 10) {
      const domName = imr_score.home > imr_score.away ? hName : aName;
      testo = `Un pareggio profondamente bugiardo. Il Meritometro parla chiaro: ai punti la partita è stata vinta da ${domName}. Nonostante il volume di gioco e la superiorità schiacciante, l'algoritmo non è bastato a piegare un avversario bravo unicamente a fare muro e portare via un punto.`;
    } else {
      testo = `Una gara sul filo del rasoio. Il pareggio sul campo riflette un sostanziale equilibrio anche nei valori dell'Indice di Merito (${imr_score.home} a ${imr_score.away}). Le due formazioni si sono annullate a vicenda senza riuscire a prendere il sopravvento.`;
    }
  } 
  // Scenario 4: Altri casi (Vittoria di misura coerente)
  else {
    const winnerName = home_score > away_score ? hName : aName;
    testo = `${winnerName} conquista i tre punti con estremo realismo. Anche l'algoritmo conferma che, al netto delle emozioni della gara, il successo è coerente con la spinta offensiva espressa sul rettangolo verde.`;
  }

  return testo;
};

// ==========================================
// 3. COMPONENTE PRINCIPALE
// ==========================================
const MeritometroCard: React.FC<MeritometroCardProps> = ({ matchId }) => {
  const [data, setData] = useState<MeritometroData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`http://127.0.0.1:8000/api/matches/${matchId}/imr`)
      .then(res => {
        if (!res.ok) throw new Error("Dati non trovati o match non processato.");
        return res.json();
      })
      .then((json: MeritometroData) => {
        if (json.error) throw new Error(json.error);
        setData(json);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [matchId]);

  if (loading) return <div className="p-6 text-slate-400 font-mono text-sm animate-pulse bg-white rounded-md border border-slate-200">📡 Calcolo algoritmo IMR in corso...</div>;
  if (error) return <div className="p-6 text-red-500 font-mono text-sm border border-red-900 bg-white rounded-md">⚠️ Errore Critico: {error}</div>;
  if (!data) return null;

  const { imr_score, dettagli_home, dettagli_away, home_name, away_name, home_score, away_score, home_xG, away_xG, timeline, goals_timeline } = data;

  const totalScore = imr_score.home + imr_score.away;
  const homePercent = totalScore > 0 ? (imr_score.home / totalScore) * 100 : 50;
  const awayPercent = totalScore > 0 ? (imr_score.away / totalScore) * 100 : 50;

  return (
    <div className="bg-white p-10 rounded-xl shadow-2xl border border-slate-200 max-w-4xl mx-auto font-sans text-slate-900">
      
      {/* ------------------------------------- */}
      {/* SCOREBOARD (Risultato + xG)           */}
      {/* ------------------------------------- */}
      <div className="flex items-center justify-between mb-8 pb-6 border-b border-slate-100">
        <div className="w-1/3 text-left">
          <h2 className="text-3xl font-black text-[#C90076] uppercase tracking-wider truncate">{home_name || "HOME"}</h2>
        </div>
        <div className="w-1/3 flex flex-col items-center">
          <div className="flex items-center gap-4 text-5xl font-black text-slate-900">
            <span>{home_score ?? "-"}</span>
            <span className="text-slate-300 font-normal">-</span>
            <span>{away_score ?? "-"}</span>
          </div>
          <div className="flex items-center gap-3 mt-3 text-sm font-bold">
            <span className="text-slate-500">{home_xG?.toFixed(2)}</span>
            <span className="text-slate-300 text-xs font-black tracking-widest uppercase">xG</span>
            <span className="text-[#10b981]">{away_xG?.toFixed(2)}</span>
          </div>
        </div>
        <div className="w-1/3 text-right">
          <h2 className="text-3xl font-black text-slate-800 uppercase tracking-wider truncate">{away_name || "AWAY"}</h2>
        </div>
      </div>

      {/* ------------------------------------- */}
      {/* COMMENTO A CALDO (IL VERDETTO IMR)    */}
      {/* ------------------------------------- */}
      <div className="bg-slate-900 text-white rounded-xl p-6 mb-10 shadow-md">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse"></div>
          <h3 className="text-xs font-black uppercase tracking-widest text-slate-400">Verdetto xPalermoStat</h3>
        </div>
        <p className="text-sm leading-relaxed font-medium text-slate-200 italic border-l-2 border-[#C90076] pl-4">
          "{generaCommentoACaldo(data)}"
        </p>
      </div>

      {/* ------------------------------------- */}
      {/* IMR BAR E PUNTEGGI                    */}
      {/* ------------------------------------- */}
      <div className="grid grid-cols-[1fr_2fr_1fr] items-center gap-10 mb-12">
        <div className="text-center">
          <div className="text-[10px] font-bold text-[#C90076] uppercase tracking-widest mb-2">Merito Casa</div>
          <div className="text-6xl font-black text-[#C90076] drop-shadow-sm">{imr_score.home}</div>
        </div>
        <div className="flex flex-col gap-3 relative mt-2">
          <div className="h-12 w-full bg-slate-100 rounded-full flex items-end relative overflow-hidden shadow-inner border border-slate-200">
            <div className="bg-[#C90076] transition-all duration-1000 ease-out absolute bottom-0 left-0" style={{ width: '49%', height: `${homePercent}%`, borderTopRightRadius: '10px' }}></div>
            <div className="bg-slate-500 transition-all duration-1000 ease-out absolute bottom-0 right-0" style={{ width: '49%', height: `${awayPercent}%`, borderTopLeftRadius: '10px' }}></div>
          </div>
        </div>
        <div className="text-center">
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Merito Ospiti</div>
          <div className="text-6xl font-black text-slate-700 drop-shadow-sm">{imr_score.away}</div>
        </div>
      </div>

      {/* ------------------------------------- */}
      {/* TIMING CHART (GRAFICO CON GOL)        */}
      {/* ------------------------------------- */}
      <div className="mb-12 border border-slate-200 rounded-xl p-8 bg-slate-50 shadow-inner">
        <div className="mb-6 flex justify-between items-end">
          <div>
            <h4 className="font-black text-lg uppercase tracking-wider text-slate-800">Timing Chart</h4>
            <p className="text-xs text-slate-500 font-mono mt-1">Sviluppo dell'assedio e impatto dei Gol (⚽)</p>
          </div>
          <div className="flex gap-4 text-xs font-bold uppercase tracking-widest bg-white py-2 px-4 rounded-lg border border-slate-200 shadow-sm">
            <span className="text-[#C90076] flex items-center gap-2"><div className="w-3 h-3 bg-[#C90076] rounded-sm"></div> Casa</span>
            <span className="text-slate-500 flex items-center gap-2"><div className="w-3 h-3 bg-slate-500 rounded-sm"></div> Ospiti</span>
          </div>
        </div>
        <TimingChartSvg timeline={timeline} goals={goals_timeline} />
      </div>

      {/* ------------------------------------- */}
      {/* TABELLA DETTAGLI                      */}
      {/* ------------------------------------- */}
      <div className="grid grid-cols-2 gap-10">
        <StatTable title="Costruzione Merito (Casa)" stats={dettagli_home} accentColor="text-white" headerBg="bg-[#C90076]" borderColor="border-[#C90076]/30" />
        <StatTable title="Costruzione Merito (Ospiti)" stats={dettagli_away} accentColor="text-white" headerBg="bg-slate-600" borderColor="border-slate-500/30" />
      </div>
    </div>
  );
};

// ==========================================
// 4. SOTTO-COMPONENTI (GRAFICO E TABELLE)
// ==========================================

const TimingChartSvg: React.FC<{ timeline: TimelinePoint[], goals?: GoalEvent[] }> = ({ timeline, goals }) => {
  if (!timeline || timeline.length === 0) return <div className="text-sm text-slate-400 font-mono py-10 text-center">Nessun dato temporale registrato dal Backend.</div>;

  const maxMin = Math.max(90, timeline[timeline.length - 1]?.minute || 90);
  const maxImr = Math.max(10, ...timeline.map(t => t.home_imr), ...timeline.map(t => t.away_imr));
  
  const svgWidth = 1000;
  const svgHeight = 250;
  const paddingY = 20;

  const mapX = (min: number) => (min / maxMin) * svgWidth;
  const mapY = (val: number) => svgHeight - (val / maxImr) * (svgHeight - paddingY * 2) - paddingY;

  const buildStepPath = (key: 'home_imr' | 'away_imr') => {
    let path = `M 0 ${mapY(0)}`;
    let lastY = mapY(0);
    
    timeline.forEach(pt => {
      const x = mapX(pt.minute);
      const y = mapY(pt[key]);
      path += ` L ${x} ${lastY} L ${x} ${y}`;
      lastY = y;
    });
    path += ` L ${svgWidth} ${lastY}`;
    return path;
  };

  const homePath = buildStepPath('home_imr');
  const awayPath = buildStepPath('away_imr');
  const xTicks = [15, 30, 45, 60, 75, 90];

  return (
    <div className="w-full overflow-hidden">
      <svg viewBox={`0 0 ${svgWidth} ${svgHeight + 30}`} className="w-full h-auto drop-shadow-sm overflow-visible">
        
        <line x1="0" y1={mapY(maxImr)} x2={svgWidth} y2={mapY(maxImr)} stroke="#f1f5f9" strokeWidth="2" strokeDasharray="5,5" />
        <line x1="0" y1={mapY(maxImr / 2)} x2={svgWidth} y2={mapY(maxImr / 2)} stroke="#f1f5f9" strokeWidth="2" strokeDasharray="5,5" />
        <line x1="0" y1={mapY(0)} x2={svgWidth} y2={mapY(0)} stroke="#cbd5e1" strokeWidth="3" />

        <line x1={mapX(45)} y1="0" x2={mapX(45)} y2={mapY(0)} stroke="#94a3b8" strokeWidth="2" strokeDasharray="6,4" />
        <text x={mapX(45)} y={mapY(0) + 20} fontSize="12" fill="#64748b" fontWeight="bold" textAnchor="middle">HT</text>

        {xTicks.map(min => (
          min !== 45 && (
            <g key={min}>
              <line x1={mapX(min)} y1={mapY(0)} x2={mapX(min)} y2={mapY(0) + 5} stroke="#cbd5e1" strokeWidth="2" />
              <text x={mapX(min)} y={mapY(0) + 20} fontSize="12" fill="#94a3b8" fontWeight="bold" textAnchor="middle">{min}'</text>
            </g>
          )
        ))}

        <path d={`${homePath} L ${svgWidth} ${mapY(0)} L 0 ${mapY(0)} Z`} fill="#C90076" opacity="0.05" />
        <path d={`${awayPath} L ${svgWidth} ${mapY(0)} L 0 ${mapY(0)} Z`} fill="#64748b" opacity="0.05" />

        <path d={awayPath} fill="none" stroke="#64748b" strokeWidth="4" strokeLinejoin="round" strokeLinecap="round" />
        <path d={homePath} fill="none" stroke="#C90076" strokeWidth="4" strokeLinejoin="round" strokeLinecap="round" />

        {/* AGGIUNTA INDICATORI DEI GOL SUL GRAFICO */}
        {goals && goals.map((g, idx) => {
          const x = mapX(g.minute);
          // Troviamo a che altezza si trovava la linea del merito in quel momento
          const point = timeline.slice().reverse().find(t => t.minute <= g.minute);
          const yVal = point ? (g.team === 'h' ? point.home_imr : point.away_imr) : 0;
          const y = mapY(yVal);
          const color = g.team === 'h' ? '#C90076' : '#64748b';

          return (
            <g key={`goal-${idx}`}>
              <circle cx={x} cy={y} r="8" fill="#fff" stroke={color} strokeWidth="3" />
              <text x={x} y={y - 12} fontSize="14" textAnchor="middle">⚽</text>
            </g>
          );
        })}

      </svg>
    </div>
  );
};

interface StatTableProps {
  title: string;
  stats: TeamDetails;
  accentColor: string;
  headerBg: string;
  borderColor: string;
}

const StatTable: React.FC<StatTableProps> = ({ title, stats, accentColor, headerBg, borderColor }) => (
  <div className={`w-full text-sm bg-white rounded-xl border ${borderColor} p-6 shadow-md`}>
    <div className={`font-black text-[12px] uppercase tracking-widest px-4 py-3 ${headerBg} ${accentColor} rounded-lg mb-5 shadow-sm`}>
      {title}
    </div>
    <div className="space-y-2 px-1">
      <Row label="Occasioni Nitide (5 pt)" val={stats.occasioni_nitide} />
      <Row label="Azioni Promettenti (2 pt)" val={stats.azioni_promettenti} />
      <Row label="Tiri da Dentro l'Area (3 pt)" val={stats.tiri_in_area} />
      <Row label="Tiri da Fuori Area (1 pt)" val={stats.tiri_fuori_area} />
      <Row label="Rigori (0 pt)" val={stats.rigori} isLast />
    </div>
  </div>
);

interface RowProps {
  label: string;
  val: number;
  isLast?: boolean;
}

const Row: React.FC<RowProps> = ({ label, val, isLast }) => (
  <div className={`flex justify-between py-3 ${!isLast ? 'border-b border-slate-100' : ''} hover:bg-slate-50 transition-colors rounded-md px-2 -mx-2`}>
    <span className="text-slate-600 font-medium">{label}</span>
    <span className="font-mono font-black text-slate-900 text-lg">{val}</span>
  </div>
);

export default MeritometroCard;