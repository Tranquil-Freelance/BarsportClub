"use client";

interface NewsItem {
  id: number;
  title: string;
  subtitle: string;
  imageUrl: string;
}

const mockNews: NewsItem[] = [
  {
    id: 1,
    title: "LA STELLA DEL MOMENTO: BRUNORI IN CIFRE",
    subtitle: "I numeri e le prestazioni dell'attaccante rosanero.",
    imageUrl: "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?q=80&w=800",
  },
  {
    id: 2,
    title: "ANALISI TATTICA: LA PRESSIONE ALTA DI PALERMO",
    subtitle: "Come la squadra riconquista palla nei primi due terzi.",
    imageUrl: "https://images.unsplash.com/photo-1551958219-acbc608c6377?q=80&w=800",
  },
];

export default function NewsSection() {
  return (
    <div className="bg-palermo-dark">
      {/* Section Header */}
      <div className="bg-zinc-200 w-full">
        <h2 className="font-heading uppercase text-2xl text-black font-bold p-2 ml-4">
          NEWS E APPROFONDIMENTI
        </h2>
      </div>

      {/* News Grid */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
          {mockNews.map((item) => (
            <div
              key={item.id}
              className="bg-zinc-100 border border-zinc-300 rounded-lg overflow-hidden shadow-lg hover:shadow-xl transition-shadow duration-300"
            >
              {/* Image 16:9 */}
              <div className="relative w-full pt-[56.25%] overflow-hidden">
                <img
                  src={item.imageUrl}
                  alt={item.title}
                  className="absolute top-0 left-0 w-full h-full object-cover"
                />
              </div>

              {/* Body */}
              <div className="p-4">
                <h3 className="font-heading uppercase text-2xl text-black leading-tight">
                  {item.title}
                </h3>
                <p className="text-zinc-600 text-sm mt-2">
                  {item.subtitle}
                </p>

                {/* Footer Button */}
                <div className="flex justify-end mt-4">
                  <button className="bg-palermo-dark text-white font-heading px-4 py-1 hover:bg-zinc-900 transition-colors">
                    Leggi Tutto
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}