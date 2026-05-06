"use client";

interface NewsCardProps {
  title: string;
  excerpt: string;
  imageUrl?: string;
}

export default function NewsCard({ title, excerpt, imageUrl }: NewsCardProps) {
  const imgSrc = imageUrl || "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?q=80&w=800";

  return (
    <div className="group bg-white border border-zinc-200 rounded-lg overflow-hidden shadow-md hover:shadow-lg transition-shadow duration-300 flex flex-col h-full">
      {/* Image Container */}
      <div className="relative h-48 w-full overflow-hidden">
        <div
          className="h-full w-full bg-cover bg-center group-hover:scale-105 transition-transform duration-300"
          style={{ backgroundImage: `url(${imgSrc})` }}
        />
      </div>

      {/* Body */}
      <div className="p-6 flex flex-col flex-grow">
        <h3 className="text-xl font-bold text-zinc-950 uppercase tracking-tight mb-3">
          {title}
        </h3>
        <p className="text-zinc-600 text-sm leading-relaxed mb-6 flex-grow">
          {excerpt}
        </p>

        {/* Action Button */}
        <div className="flex justify-end">
          <button className="bg-zinc-900 hover:bg-pink-600 text-white font-semibold py-2 px-5 rounded-md text-sm uppercase tracking-wider transition-colors duration-300">
            Leggi Tutto
          </button>
        </div>
      </div>
    </div>
  );
}