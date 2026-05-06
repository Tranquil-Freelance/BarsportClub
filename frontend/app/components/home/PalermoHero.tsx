"use client";

import { LineChart, Line, ResponsiveContainer, Tooltip } from "recharts";
import Link from "next/link";

const performanceData = [
  { match: "Match 1", performance: 65 },
  { match: "Match 2", performance: 70 },
  { match: "Match 3", performance: 85 },
  { match: "Match 4", performance: 80 },
  { match: "Match 5", performance: 90 },
];

const PalermoHero = () => {
  return (
    <section className="relative min-h-[90vh] overflow-hidden">
      {/* Background Image with Aggressive Dark Overlay */}
      <img
        src="https://images.unsplash.com/photo-1518605368461-1e1e1a4253db?q=60&w=1200"
        alt="Stadium crowd"
        className="absolute inset-0 w-full h-full object-cover"
      />
      <div className="absolute inset-0 bg-gradient-to-r from-palermo-dark via-palermo-dark/90 to-transparent" />

      {/* Right Side Player Cut-out */}
      <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1/3 h-3/4 overflow-hidden z-0">
        <img
          src="https://images.unsplash.com/photo-1511886929837-354d827aae26?q=60&w=600"
          alt="Palermo player"
          className="w-full h-full object-cover opacity-90"
        />
      </div>

      {/* Left Content */}
      <div className="relative z-10 mx-auto max-w-7xl px-8 pt-24 pb-16">
        <div className="max-w-2xl">
          <h1 className="font-heading uppercase text-white text-6xl font-bold tracking-tighter leading-none">
            INSIDE PALERMO:
          </h1>
          <h2 className="font-heading text-palermo-pink text-4xl mt-4 font-bold tracking-tight">
            ANALISI E STATISTICHE ROSANERO
          </h2>
          <p className="text-zinc-300 text-lg mt-6">
            Approfondimenti e dati avanzati sul Palermo Calcio
          </p>

          {/* Stats Widget (Bottom Left Glassmorphism Box) */}
          <div className="bg-palermo-gray/80 backdrop-blur-md border-t-2 border-palermo-pink p-4 mt-8 flex gap-4 w-fit">
            {/* Left Column */}
            <div className="space-y-2">
              <div>
                <div className="text-xs uppercase tracking-wider text-zinc-400">
                  Possesso Palla
                </div>
                <div className="font-heading text-5xl text-white">58%</div>
              </div>
              <div>
                <div className="text-xs uppercase tracking-wider text-zinc-400">
                  xG del Palermo
                </div>
                <div className="font-heading text-5xl text-white">1.85</div>
              </div>
            </div>

            {/* Right Column: Line Chart */}
            <div className="w-64">
              <div className="text-xs uppercase tracking-wider text-zinc-400 mb-2">
                Rendimento Ultime 5 Partite
              </div>
              <div className="h-32">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={performanceData}>
                    <Line
                      type="monotone"
                      dataKey="performance"
                      stroke="#ec4899"
                      strokeWidth={3}
                      dot={{ r: 4, fill: "#ec4899" }}
                      activeDot={{ r: 6, fill: "#ffffff", stroke: "#ec4899" }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#18181b",
                        border: "1px solid #ec4899",
                        borderRadius: "0.25rem",
                        color: "#f4f4f5",
                      }}
                      labelStyle={{ color: "#f4f4f5", fontWeight: "bold" }}
                      formatter={(value: any, name: any) => [value, name]}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Full width pink button */}
          <Link
            href="/analisi"
            className="mt-8 block w-full max-w-md bg-palermo-pink text-white font-heading py-4 text-center text-lg font-bold hover:bg-pink-600 transition-colors"
          >
            Scopri di Più
          </Link>
        </div>
      </div>
    </section>
  );
};

export default PalermoHero;