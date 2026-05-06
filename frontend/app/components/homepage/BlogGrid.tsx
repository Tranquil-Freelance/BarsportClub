import React from 'react';
import Link from 'next/link';

export interface BlogArticle {
  id: number;
  title: string;
  excerpt: string;
  author: string;
  date: string;
  readTime: string;
  category: string;
  image?: string;
}

export interface BlogGridProps {
  articles?: BlogArticle[];
  title?: string;
}

const BlogGrid: React.FC<BlogGridProps> = ({
  articles = [
    {
      id: 1,
      title: 'PALERMO’S DEFENSIVE SOLIDITY: A DATA‑DRIVEN BREAKDOWN',
      excerpt: 'How the Rosanero have transformed into one of Serie B’s hardest teams to beat.',
      author: 'Marco Rossi',
      date: '2023-11-10',
      readTime: '8 min',
      category: 'Tactical Analysis',
      image: 'https://images.unsplash.com/photo-1575361204480-aadea25e6e68?auto=format&fit=crop&w=800&q=80',
    },
    {
      id: 2,
      title: 'THE RISE OF XG IN ITALIAN FOOTBALL',
      excerpt: 'Exploring how expected goals has changed the way we analyze matches in Italy.',
      author: 'Giulia Bianchi',
      date: '2023-11-05',
      readTime: '12 min',
      category: 'Data Science',
      image: 'https://images.unsplash.com/photo-1543326727-cf6c39e8f84c?auto=format&fit=crop&w=800&q=80',
    },
    {
      id: 3,
      title: 'MATTEO BRUNORI’S SCORING EFFICIENCY',
      excerpt: 'A deep dive into the numbers behind Brunori’s impressive goal‑per‑shot ratio.',
      author: 'Luca Ferrari',
      date: '2023-10-28',
      readTime: '6 min',
      category: 'Player Analysis',
      image: 'https://images.unsplash.com/photo-1599058917212-d750089bc07e?auto=format&fit=crop&w=800&q=80',
    },
    {
      id: 4,
      title: 'SET‑PIECES: PALERMO’S SECRET WEAPON',
      excerpt: 'Statistical review of dead‑ball situations and their impact on results.',
      author: 'Francesca Conti',
      date: '2023-10-20',
      readTime: '10 min',
      category: 'Set Pieces',
      image: 'https://images.unsplash.com/photo-1517466787929-bc90951d0974?auto=format&fit=crop&w=800&q=80',
    },
  ],
  title = 'Ultime Analisi',
}) => {
  return (
    <section className="blog-grid py-20 bg-zinc-950">
      <div className="container mx-auto px-6">
        <header className="flex justify-between items-center mb-16">
          <div>
            <h2 className="text-5xl font-heading font-bold tracking-tight">{title}</h2>
            <p className="text-xl text-zinc-400 font-body mt-4 max-w-3xl">
              Approfondimenti tattici, analisi statistiche e reportage esclusivi sul Palermo e sulle principali leghe europee.
            </p>
          </div>
          <Link
            href="/blog"
            className="text-palermo-pink hover:text-pink-400 font-heading font-bold uppercase tracking-wider text-lg transition-colors"
          >
            Vedi Tutti gli Articoli →
          </Link>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
          {articles.slice(0, 3).map((article) => (
            <article
              key={article.id}
              className="group relative bg-gradient-to-br from-zinc-900 to-black rounded-2xl overflow-hidden border border-zinc-800 hover:border-palermo-pink transition-all duration-500 hover:shadow-2xl hover:shadow-pink-900/30"
            >
              {/* Background image with overlay */}
              <div className="absolute inset-0 overflow-hidden">
                <div
                  className="w-full h-full bg-cover bg-center transition-transform duration-700 group-hover:scale-110"
                  style={{ backgroundImage: `url(${article.image})` }}
                >
                  <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/70 to-transparent" />
                  <div className="absolute inset-0 bg-gradient-to-r from-palermo-pink/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                </div>
              </div>

              {/* Content */}
              <div className="relative z-10 p-8 h-full flex flex-col justify-end min-h-[480px]">
                <div className="mb-6">
                  <span className="inline-block px-4 py-2 bg-palermo-pink/20 backdrop-blur-sm text-palermo-pink font-heading font-bold uppercase tracking-wider rounded-full text-sm">
                    {article.category}
                  </span>
                </div>
                <h3 className="text-2xl font-heading font-bold leading-tight mb-4 line-clamp-3">
                  {article.title}
                </h3>
                <p className="text-zinc-300 font-body mb-6 line-clamp-3">
                  {article.excerpt}
                </p>

                <div className="flex items-center justify-between text-sm text-zinc-400 mb-6">
                  <span className="font-medium">{article.author}</span>
                  <span>{article.readTime} lettura</span>
                </div>

                <div className="text-xs text-zinc-500 mb-6">
                  {new Date(article.date).toLocaleDateString('it-IT', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </div>

                <button className="w-full py-4 bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 text-white font-heading font-bold uppercase tracking-wider rounded-xl transition-all duration-300 group-hover:scale-[1.02]">
                  Leggi Articolo
                </button>
              </div>
            </article>
          ))}
        </div>

        {/* Featured article */}
        <div className="mt-24 p-12 bg-gradient-to-r from-zinc-900 to-black rounded-3xl border border-zinc-800 relative overflow-hidden">
          <div className="absolute -right-20 -top-20 w-64 h-64 bg-palermo-pink/10 rounded-full blur-3xl" />
          <div className="relative z-10 max-w-4xl">
            <span className="inline-block px-5 py-3 bg-palermo-pink text-white font-heading font-bold uppercase tracking-wider rounded-full text-sm">
              Analisi in Evidenza
            </span>
            <h3 className="text-5xl font-heading font-bold mt-8 mb-10 leading-tight">
              Il Futuro del Data Journalism nel Calcio: Dove Stiamo Andando?
            </h3>
            <p className="text-2xl text-zinc-300 mb-12">
              Uno sguardo approfondito sulle tendenze emergenti, gli strumenti e le narrative che daranno forma all'analisi calcistica nel prossimo decennio.
            </p>
            <div className="flex flex-col sm:flex-row gap-8">
              <button className="px-12 py-5 bg-palermo-pink hover:bg-pink-600 text-white font-heading font-bold uppercase tracking-wider rounded-xl transition-all duration-300 shadow-lg hover:shadow-pink-900/50 hover:scale-105">
                Leggi l'Analisi Completa
              </button>
              <button className="px-12 py-5 border-2 border-zinc-700 hover:border-palermo-pink text-zinc-300 hover:text-white font-heading font-bold uppercase tracking-wider rounded-xl transition-all duration-300 hover:scale-105">
                Scarica il Report (PDF)
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default BlogGrid;