import Link from "next/link";
import Image from "next/image";
import { notFound } from "next/navigation";
import { mockArticles, mockMatchData } from '../../lib/mockData';

interface Article {
  id: number;
  slug: string;
  title: string;
  author: string;
  content: string;
  hero_image: string | null;
  category: string | null;
  league: string | null;
  team: string | null;
  is_featured: boolean;
  match_id: number | null;
  created_at: string;
}

interface Shot {
  minute: number;
  player: string;
  xG: number;
  result: string;
  X: number;
  Y: number;
  team_type: 'h' | 'a';
}

interface MatchShots {
  match: {
    home_team: string;
    away_team: string;
  };
  shots: {
    h: Shot[];
    a: Shot[];
  };
}

async function getArticle(slug: string): Promise<Article | null> {
  // Temporarily use mock data while backend is unavailable
  const article = mockArticles.find(a => a.slug === slug);
  if (!article) return null;
  return article;
}

async function getMatchShots(matchId: number): Promise<MatchShots | null> {
  // Temporarily use mock data while backend is unavailable
  return mockMatchData;
}

// Mini Tactical Board component for shot visualization
function MiniTacticalBoard({ matchShots }: { matchShots: MatchShots }) {
  const { home_team, away_team } = matchShots.match;
  const allShots = [...matchShots.shots.h, ...matchShots.shots.a];

  return (
    <div className="my-12 p-8 bg-palermo-dark/50 rounded-xl border border-zinc-800">
      <h3 className="text-2xl font-bold text-palermo-pink mb-6">🎯 Mini Tactical Board</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-2">
          <div className="relative w-full h-64 bg-gradient-to-br from-zinc-900 to-black rounded-lg overflow-hidden border border-zinc-700">
            {/* Football pitch outline */}
            <div className="absolute inset-2 border-2 border-zinc-700 rounded-lg"></div>
            <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-zinc-700"></div>
            <div className="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 w-12 h-12 border-2 border-zinc-700 rounded-full"></div>
            {/* Render shots as dots */}
            {allShots.map((shot, idx) => {
              const x = shot.X; // 0-100
              const y = shot.Y; // 0-100
              const isHome = shot.team_type === 'h';
              return (
                <div
                  key={idx}
                  className={`absolute w-3 h-3 rounded-full ${isHome ? 'bg-palermo-pink' : 'bg-blue-500'} shadow-lg`}
                  style={{
                    left: `${x}%`,
                    top: `${y}%`,
                    transform: 'translate(-50%, -50%)',
                  }}
                  title={`${shot.player} - ${shot.minute}' - xG: ${shot.xG}`}
                />
              );
            })}
          </div>
          <div className="mt-4 flex items-center justify-center gap-6 text-sm text-zinc-400">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-palermo-pink"></div>
              <span>{home_team} shots</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <span>{away_team} shots</span>
            </div>
          </div>
        </div>
        <div className="space-y-4">
          <h4 className="text-lg font-bold text-white">Shot Summary</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-zinc-400">Total Shots</span>
              <span className="text-white font-bold">{allShots.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-400">Home Shots</span>
              <span className="text-palermo-pink font-bold">{matchShots.shots.h.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-400">Away Shots</span>
              <span className="text-blue-400 font-bold">{matchShots.shots.a.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-400">Total xG</span>
              <span className="text-white font-bold">
                {allShots.reduce((sum, shot) => sum + shot.xG, 0).toFixed(2)}
              </span>
            </div>
          </div>
          <div className="pt-4 border-t border-zinc-800">
            <h5 className="text-sm font-bold text-zinc-300 mb-2">Top Shooters</h5>
            <ul className="text-sm text-zinc-400 space-y-1">
              {Object.entries(
                allShots.reduce<Record<string, number>>((acc, shot) => {
                  acc[shot.player] = (acc[shot.player] || 0) + shot.xG;
                  return acc;
                }, {})
              )
                .sort(([, a], [, b]) => b - a)
                .slice(0, 3)
                .map(([player, xg]) => (
                  <li key={player} className="flex justify-between">
                    <span>{player}</span>
                    <span className="text-palermo-pink">{xg.toFixed(2)} xG</span>
                  </li>
                ))}
            </ul>
          </div>
        </div>
      </div>
      <p className="mt-6 text-sm text-zinc-500">
        Shot data from advanced analytics. Coordinates represent approximate location on the pitch.
      </p>
    </div>
  );
}

export default async function ArticlePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const article = await getArticle(slug);

  if (!article) {
    notFound();
  }

  // Format date
  const date = new Date(article.created_at).toLocaleDateString("it-IT", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
  const readTime = Math.ceil(article.content.split(" ").length / 200); // rough estimate

  // Fetch match shots if article has a match_id
  let matchShots: MatchShots | null = null;
  if (article.match_id) {
    matchShots = await getMatchShots(article.match_id);
  }

  return (
    <div className="min-h-screen bg-palermo-dark text-white">
      {/* Hero Section */}
      <div className="relative h-[60vh] overflow-hidden">
        <Image
          src={article.hero_image || "/AL1_0070-1920x1060.jpg"}
          alt={article.title}
          fill
          className="object-cover object-center opacity-50"
          priority
        />
        <div className="absolute inset-0 bg-gradient-to-t from-palermo-dark via-palermo-dark/70 to-transparent" />
        <div className="relative z-10 container mx-auto px-8 h-full flex flex-col justify-end pb-16">
          <div className="max-w-4xl">
            <div className="inline-flex items-center gap-4 text-sm text-zinc-300 mb-6">
              {article.category && (
                <span className="bg-palermo-pink/20 text-palermo-pink px-3 py-1 rounded-full font-bold uppercase tracking-wider">
                  {article.category}
                </span>
              )}
              {article.league && (
                <span className="bg-zinc-800 text-zinc-300 px-3 py-1 rounded-full font-bold uppercase tracking-wider">
                  {article.league}
                </span>
              )}
              {article.team && (
                <span className="bg-zinc-700 text-zinc-200 px-3 py-1 rounded-full font-bold uppercase tracking-wider">
                  {article.team}
                </span>
              )}
              <span>{date}</span>
              <span>•</span>
              <span>{readTime} min lettura</span>
            </div>
            <h1 className="font-heading text-5xl md:text-6xl lg:text-7xl font-bold leading-tight tracking-tight">
              {article.title}
            </h1>
            <div className="mt-8 flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-palermo-pink/30 flex items-center justify-center text-xl font-bold">
                {article.author.substring(0, 2).toUpperCase()}
              </div>
              <div>
                <p className="font-bold text-lg">{article.author}</p>
                <p className="text-zinc-400 text-sm">Autore</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Article Content */}
      <div className="container mx-auto px-8 py-16 max-w-4xl">
        <div className="prose prose-lg prose-invert max-w-none">
          <div className="bg-palermo-dark/50 p-8 rounded-xl border border-zinc-800 mb-12">
            <h3 className="text-2xl font-bold text-palermo-pink mb-4">📊 In sintesi</h3>
            <ul className="text-zinc-300 space-y-2">
              <li>Articolo di <strong>{article.author}</strong></li>
              <li>Pubblicato il <strong>{date}</strong></li>
              <li>Tempo di lettura stimato: <strong>{readTime} minuti</strong></li>
              {article.category && <li>Categoria: <strong>{article.category}</strong></li>}
              {article.league && <li>Lega: <strong>{article.league}</strong></li>}
              {article.team && <li>Squadra: <strong>{article.team}</strong></li>}
              {article.is_featured && <li><span className="text-palermo-pink font-bold">⭐ Articolo in evidenza</span></li>}
            </ul>
          </div>
          <div dangerouslySetInnerHTML={{ __html: article.content }} />

          {/* Match Data Section */}
          {matchShots && (
            <MiniTacticalBoard matchShots={matchShots} />
          )}
        </div>

        {/* Back to Home Button */}
        <div className="mt-16 pt-8 border-t border-zinc-800 flex justify-between items-center">
          <Link
            href="/"
            className="bg-palermo-pink text-white font-heading uppercase py-3 px-8 text-sm font-bold tracking-wider hover:bg-pink-600 transition shadow-md flex items-center gap-2"
          >
            ← Torna alla Home
          </Link>
          <div className="text-zinc-500 text-sm">
            Condividi su:
            <button className="ml-4 text-zinc-300 hover:text-palermo-pink">Twitter</button>
            <button className="ml-4 text-zinc-300 hover:text-palermo-pink">Facebook</button>
            <button className="ml-4 text-zinc-300 hover:text-palermo-pink">LinkedIn</button>
          </div>
        </div>
      </div>

      {/* Footer note */}
      <div className="container mx-auto px-8 pb-16 max-w-4xl text-center text-zinc-500 text-sm">
        <p>© 2025 xPalermoStat – Tutti i dati sono stati raccolti da fonti pubbliche e calcolati con metodologia open‑source.</p>
      </div>
    </div>
  );
}