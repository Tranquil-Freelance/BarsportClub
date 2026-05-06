"use client";

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { mockArticles } from '../lib/mockData';

export interface NewsArticle {
  id: number;
  title: string;
  description: string;
  imageSrc: string;
  alt: string;
  slug: string;
}

export interface NewsSectionProps {
  newsArticles?: NewsArticle[]; // optional: if provided, use static data
}

interface ApiArticle {
  id: number;
  slug: string;
  title: string;
  author: string;
  content: string;
  hero_image: string | null;
  created_at: string;
}

const NewsSection: React.FC<NewsSectionProps> = ({ newsArticles: staticArticles }) => {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // If static articles are provided, use them and skip fetching
    if (staticArticles !== undefined) {
      setArticles(staticArticles);
      setLoading(false);
      return;
    }

    // Temporarily use mock data while backend is unavailable
    const transformed: NewsArticle[] = mockArticles.slice(0, 6).map((article) => ({
      id: article.id,
      title: article.title,
      description: article.content.substring(0, 150) + '...',
      imageSrc: article.hero_image || '/default-news.jpg',
      alt: article.title,
      slug: article.slug,
    }));
    setArticles(transformed);
    setLoading(false);
  }, [staticArticles]);

  if (loading && articles.length === 0) {
    return (
      <div className="mt-14">
        <div className="bg-zinc-800 text-white font-heading uppercase text-2xl font-bold px-6 py-2 w-fit pr-24 shadow-md border-l-8 border-palermo-pink mb-6" style={{ clipPath: 'polygon(0 0, 96% 0, 100% 100%, 0% 100%)' }}>
          NEWS E APPROFONDIMENTI
        </div>
        <div className="grid grid-cols-2 gap-8">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="bg-white shadow-lg flex flex-col border-b-[5px] border-palermo-dark rounded-sm overflow-hidden animate-pulse">
              <div className="h-56 w-full bg-slate-300" />
              <div className="p-7 flex flex-col flex-grow relative">
                <div className="h-7 bg-slate-300 rounded mb-3" />
                <div className="h-4 bg-slate-200 rounded w-3/4" />
                <div className="absolute bottom-6 right-6 bg-slate-300 h-8 w-24 rounded" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error && articles.length === 0) {
    return (
      <div className="mt-14">
        <div className="bg-zinc-800 text-white font-heading uppercase text-2xl font-bold px-6 py-2 w-fit pr-24 shadow-md border-l-8 border-palermo-pink mb-6" style={{ clipPath: 'polygon(0 0, 96% 0, 100% 100%, 0% 100%)' }}>
          NEWS E APPROFONDIMENTI
        </div>
        <div className="text-center py-12 text-red-600">
          Failed to load articles: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="mt-14">
      <div className="bg-zinc-800 text-white font-heading uppercase text-2xl font-bold px-6 py-2 w-fit pr-24 shadow-md border-l-8 border-palermo-pink mb-6" style={{ clipPath: 'polygon(0 0, 96% 0, 100% 100%, 0% 100%)' }}>
        NEWS E APPROFONDIMENTI
      </div>
      <div className="grid grid-cols-2 gap-8">
        {articles.map((article) => (
          <Link key={article.id} href={`/article/${article.slug}`} className="block">
            <article className="bg-white shadow-lg flex flex-col border-b-[5px] border-palermo-dark rounded-sm overflow-hidden cursor-pointer hover:shadow-xl transition-shadow duration-300">
              <div className="h-56 w-full overflow-hidden">
                <img src={article.imageSrc} alt={article.alt} className="w-full h-full object-cover" />
              </div>
              <div className="p-7 flex flex-col flex-grow relative">
                <h3 className="font-heading uppercase text-2xl text-black leading-tight font-bold pr-20">{article.title}</h3>
                <p className="text-zinc-600 text-sm mt-3">{article.description}</p>
                <div className="absolute bottom-6 right-6 bg-palermo-dark text-white font-heading text-xs px-6 py-2 uppercase tracking-widest hover:bg-palermo-pink transition shadow-md cursor-pointer">
                  Leggi Tutto
                </div>
              </div>
            </article>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default NewsSection;