"use client";

export default function TacticalCard() {
  return (
    <div className="bg-white rounded-lg overflow-hidden">
      {/* Category Badge */}
      <div className="bg-palermo-pink text-white font-heading italic px-4 py-1 -skew-x-12 inline-block ml-4 mt-2">
        ANALISI TATTICA
      </div>

      {/* Header Area (Light) */}
      <div className="px-4 pt-2">
        <h2 className="font-heading uppercase text-black text-3xl font-bold">
          COME ATTACCA IL PALERMO
        </h2>
        <p className="text-zinc-600 px-4 pb-4">
          Focus sulle strategie offensive dei rosanero.
        </p>
      </div>

      {/* Body Area (Visual) */}
      <div className="relative h-64 overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1551958219-acbc608c6377?q=80&w=800"
          alt="Tactical pitch"
          className="w-full h-full object-cover"
        />
        {/* Dark gradient overlay at bottom */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
        {/* Centered Action Button */}
        <div className="absolute inset-0 flex items-center justify-center">
          <button className="bg-black text-white font-heading px-6 py-2 border-b-2 border-palermo-pink hover:bg-zinc-900 transition-colors">
            Leggi l'Analisi
          </button>
        </div>
      </div>
    </div>
  );
}