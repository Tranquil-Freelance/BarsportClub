import React from 'react';
import MeritometroCard from '../../components/MeritometroCard';

export default function TestMeritometroPage() {
  // Usiamo l'ID 30135 perché il tuo backend lo ha già elaborato con successo.
  // Puoi cambiare questo numero per testare altre partite.
  const testMatchId = 30135;

  return (
    <div className="min-h-screen bg-slate-50 py-16 font-sans">
      <div className="max-w-5xl mx-auto px-4">
        
        <div className="mb-10 text-center">
          <h1 className="text-3xl font-black text-slate-900 uppercase tracking-widest mb-2">
            Laboratorio di Test
          </h1>
          <p className="text-slate-500">
            Visualizzazione del componente <span className="font-mono bg-slate-200 px-1 rounded text-[#C90076]">MeritometroCard.tsx</span>
          </p>
        </div>

        {/* Qui iniettiamo il nostro componente passandogli l'ID della partita */}
        <MeritometroCard matchId={testMatchId} />

      </div>
    </div>
  );
}