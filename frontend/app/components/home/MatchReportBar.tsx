"use client";

export default function MatchReportBar() {
  return (
    <div className="sticky bottom-0 z-50 bg-palermo-dark border-t-2 border-palermo-pink p-6 mt-12">
      <div className="max-w-7xl mx-auto">
        {/* Header Area */}
        <div className="flex flex-wrap items-center mb-6">
          <div className="bg-palermo-pink text-white font-heading uppercase px-3 py-1 mr-4">
            MATCH REPORT
          </div>
          <div className="text-zinc-400 font-heading text-sm md:text-base">
            ULTIMA PARTITA: PALERMO vs COSENZA
          </div>
        </div>

        {/* Score Area */}
        <div className="flex flex-col md:flex-row items-center justify-center mb-6">
          {/* Team Palermo */}
          <div className="text-white font-heading text-3xl md:text-4xl mb-4 md:mb-0 md:mr-8">
            Palermo
          </div>

          {/* Score */}
          <div className="flex items-center justify-center my-4 md:my-0">
            <span className="text-white font-heading text-6xl md:text-7xl mx-4 md:mx-8 text-shadow-pink">
              2
            </span>
            <span className="text-white font-heading text-4xl md:text-5xl mx-2">-</span>
            <span className="text-white font-heading text-6xl md:text-7xl mx-4 md:mx-8 text-shadow-pink">
              1
            </span>
          </div>

          {/* Team Cosenza */}
          <div className="text-white font-heading text-3xl md:text-4xl mt-4 md:mt-0 md:ml-8">
            Cosenza
          </div>
        </div>

        {/* Bottom Stats */}
        <div className="flex flex-wrap items-center justify-center gap-4 md:gap-8 text-zinc-400 text-sm md:text-base mb-6">
          <div className="flex items-center">
            <span className="text-palermo-pink mr-2">•</span>
            <span>Possesso</span>
            <span className="ml-2 text-white">57%</span>
          </div>
          <div className="flex items-center">
            <span className="text-palermo-pink mr-2">•</span>
            <span>xG fino</span>
            <span className="ml-2 text-white">1.92</span>
          </div>
          <div className="flex items-center">
            <span className="text-palermo-pink mr-2">•</span>
            <span>Tiri in Porta</span>
            <span className="ml-2 text-white">6</span>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex justify-end">
          <button className="bg-palermo-pink text-white font-heading uppercase px-6 py-2 hover:bg-pink-600 transition-colors">
            Vedi il Report Completo
          </button>
        </div>
      </div>
    </div>
  );
}