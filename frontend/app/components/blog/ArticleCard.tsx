"use client";

import Link from "next/link";

// Utility to strip HTML tags
function stripHtml(html: string): string {
  return html.replace(/<[^>]*>?/gm, "").replace(/\s+/g, " ").trim();
}

// Utility to extract featured image URL from _embedded
function getFeaturedImageUrl(
  embedded?: { "wp:featuredmedia"?: Array<{ source_url: string }> }
): string | null {
  if (
    embedded &&
    embedded["wp:featuredmedia"] &&
    embedded["wp:featuredmedia"].length > 0
  ) {
    return embedded["wp:featuredmedia"][0].source_url;
  }
  return null;
}

interface ArticleCardProps {
  title: string;
  excerpt: string;
  date: string;
  slug: string;
  imageUrl?: string | null;
}

export default function ArticleCard({
  title,
  excerpt,
  date,
  slug,
  imageUrl,
}: ArticleCardProps) {
  const formattedDate = new Date(date).toLocaleDateString("it-IT", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
  const cleanExcerpt = stripHtml(excerpt);

  return (
    <article className="group relative overflow-hidden rounded-xl border border-slate-800 bg-slate-900/80 p-6 shadow-lg transition-all duration-300 hover:border-emerald-700 hover:bg-slate-900 hover:shadow-2xl hover:shadow-emerald-900/20">
      {/* Featured Image */}
      {imageUrl ? (
        <div className="mb-6 overflow-hidden rounded-lg">
          <img
            src={imageUrl}
            alt={title}
            className="aspect-video object-cover w-full transition-transform duration-500 group-hover:scale-105"
          />
        </div>
      ) : (
        <div className="mb-6 aspect-video w-full bg-gradient-to-br from-como-blue/20 to-como-dark/20 rounded-lg flex items-center justify-center">
          <span className="text-gray-500">No image</span>
        </div>
      )}

      {/* Date */}
      <div className="mb-3 text-sm font-medium text-emerald-400">
        {formattedDate}
      </div>

      {/* Title */}
      <h3 className="mb-4 text-2xl font-bold tracking-tight text-white transition-colors group-hover:text-emerald-300">
        <Link href={`/blog/${slug}`} className="after:absolute after:inset-0">
          {title}
        </Link>
      </h3>

      {/* Excerpt */}
      <p className="mb-6 line-clamp-3 text-slate-300">{cleanExcerpt}</p>

      {/* Read more link */}
      <div className="flex items-center justify-between">
        <Link
          href={`/blog/${slug}`}
          className="inline-flex items-center text-emerald-400 hover:text-emerald-300 font-semibold transition-colors"
        >
          Leggi l'articolo
          <svg
            className="ml-2 h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M14 5l7 7m0 0l-7 7m7-7H3"
            />
          </svg>
        </Link>

        {/* Category badge - optional */}
        <span className="rounded-full bg-emerald-950/40 px-3 py-1 text-xs font-medium text-emerald-300">
          Analisi
        </span>
      </div>
    </article>
  );
}