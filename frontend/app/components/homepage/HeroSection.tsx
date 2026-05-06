'use client';

import React from 'react';

export interface HeroSectionProps {
  // Optional props for future customization
  matchScore?: string;
  subheadline?: string;
  xgHome?: number;
  xgAway?: number;
}

const HeroSection: React.FC<HeroSectionProps> = ({
  matchScore = 'PALERMO 2 – 1 CAGLIARI',
  subheadline = 'A dramatic comeback sealed by an 89th‑minute winner. Dive into the xG story, possession dominance, and key moments.',
  xgHome = 2.0,
  xgAway = 1.3,
}) => {
  return (
    <section className="min-h-[95vh] bg-zinc-950 relative overflow-hidden">
      {/* Subtle pink radial glow from top center */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(236,72,153,0.15),transparent_60%)]" />

      {/* Main container */}
      <div className="max-w-7xl mx-auto px-10 h-full flex items-center">
        <div className="grid grid-cols-[55%_45%] items-center gap-16 h-full">
          {/* LEFT COLUMN */}
          <div className="flex flex-col justify-center h-full py-20">
            {/* Headline */}
            <h1 className="text-[110px] leading-[0.9] font-extrabold uppercase tracking-tight text-white">
              {matchScore}
            </h1>

            {/* Subheadline */}
            <p className="text-2xl opacity-80 mt-6 max-w-xl text-zinc-300">
              {subheadline}
            </p>

            {/* Stats row: Big xG numbers */}
            <div className="mt-12">
              <div className="flex items-end justify-between">
                <div className="text-7xl font-bold text-[#ec4899]">{xgHome.toFixed(1)}</div>
                <div className="text-7xl font-bold text-white">{xgAway.toFixed(1)}</div>
              </div>
              {/* Horizontal comparison bar */}
              <div className="h-3 rounded-full bg-zinc-800 overflow-hidden flex mt-4">
                <div
                  className="h-full bg-[#ec4899] rounded-l-full"
                  style={{ width: `${(xgHome / (xgHome + xgAway)) * 100}%` }}
                />
                <div
                  className="h-full bg-zinc-600 rounded-r-full"
                  style={{ width: `${(xgAway / (xgHome + xgAway)) * 100}%` }}
                />
              </div>
              <div className="flex justify-between mt-2 text-sm text-zinc-400">
                <span>Palermo xG</span>
                <span>Opponent xG</span>
              </div>
            </div>

            {/* CTA button */}
            <div className="mt-10">
              <button className="h-16 px-12 text-lg uppercase bg-[#ec4899] hover:bg-pink-600 transition text-white font-bold tracking-wide">
                Explore Full Match Report →
              </button>
            </div>
          </div>

          {/* RIGHT COLUMN */}
          <div className="relative h-full overflow-hidden">
            {/* Gradient overlay */}
            <div className="absolute inset-0 bg-gradient-to-l from-black via-black/70 to-transparent z-10" />

            {/* Image */}
            <div className="absolute right-0 bottom-0 h-[120%] translate-y-8">
              <img
                src="https://images.unsplash.com/photo-1543326727-cf6c39e8f84c?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80"
                alt="Football player celebrating"
                className="h-full w-auto object-contain"
              />
            </div>

            {/* Optional badge (optional, can be removed) */}
            <div className="absolute bottom-32 left-8 z-20">
              <div className="inline-block px-6 py-3 bg-white/10 backdrop-blur-md rounded-full text-white text-sm font-bold uppercase tracking-wider">
                Player of the Match · Matteo Brunori
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;