"use client";

export default function StatsCard() {
  return (
    <div className="bg-white rounded-lg overflow-hidden">
      {/* Category Badge */}
      <div className="bg-palermo-pink text-white font-heading italic px-4 py-1 -skew-x-12 inline-block ml-4 mt-2">
        STATISTICHE AVANZATE
      </div>

      {/* Header Area (Light) */}
      <div className="px-4 pt-2">
        <h2 className="font-heading uppercase text-black text-3xl font-bold">
          I NUMERI CHIAVE DEL PALERMO
        </h2>
        <p className="text-zinc-600 px-4 pb-4">
          Dati approfonditi e metriche avanzate.
        </p>
      </div>

      {/* Body Area (Dark) */}
      <div className="bg-palermo-dark text-white p-6">
        {/* Data Grid */}
        <div className="flex justify-between">
          {/* Column 1 */}
          <div className="flex-1 text-center">
            <div className="text-zinc-400 text-sm uppercase tracking-wider">
              xG
            </div>
            <div className="font-heading text-5xl text-white mt-2">1.85</div>
          </div>

          {/* Column 2 with borders */}
          <div className="flex-1 text-center border-l border-r border-zinc-800">
            <div className="text-zinc-400 text-sm uppercase tracking-wider">
              PPDA
            </div>
            <div className="font-heading text-5xl text-white mt-2">8.2</div>
          </div>

          {/* Column 3 */}
          <div className="flex-1 text-center">
            <div className="text-zinc-400 text-sm uppercase tracking-wider">
              Duelli Vinti
            </div>
            <div className="font-heading text-5xl text-white mt-2">54%</div>
          </div>
        </div>

        {/* Thin pink horizontal line separator */}
        <div className="border-t border-palermo-pink my-6 mx-12" />

        {/* Centered Action Button */}
        <div className="flex justify-center">
          <button className="bg-palermo-pink text-white font-heading px-8 py-2 hover:bg-pink-600 transition-colors">
            Scopri i Dati
          </button>
        </div>
      </div>
    </div>
  );
}