"use client";

import Image from "next/image";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import "../../i18n/config";
import { ArticleMeta, Locale } from "@/app/lib/articles";

/** Normalise an i18n language code to one of our supported Locale values. */
function resolveLocale(code: string): Locale {
  if (code === "it" || code === "en" || code === "es" || code === "fr") return code;
  // Fallback chain: exact match → en → it
  return "en";
}

function formatDate(dateStr: string, locale: string): string {
  try {
    const lang = locale.startsWith("it") ? "it-IT" : locale.startsWith("es") ? "es-ES" : locale.startsWith("fr") ? "fr-FR" : "en-US";
    return new Date(dateStr).toLocaleDateString(lang, {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}

function HeroArticle({ article, t, i18n }: { article: ArticleMeta; t: (key: string) => string; i18n: { language: string } }) {
  return (
    <article className="mb-14">
      <Link href={`/blog/${article.slug}`} className="group block">
        {/* Cinematic cover image */}
        <div className="relative w-full h-[440px] md:h-[560px] bg-[#0a192f] overflow-hidden mb-7">
          {article.coverImage && (
            <Image
              src={article.coverImage}
              alt={article.title}
              fill
              className="object-cover object-center group-hover:scale-[1.02] transition-transform duration-700 ease-out"
              priority
            />
          )}
          {/* Gradient */}
          <div className="absolute inset-0 bg-gradient-to-t from-[#050d1a]/95 via-[#050d1a]/25 to-transparent" />

          {/* Category chip */}
          <div className="absolute top-5 left-5 z-10">
            <span className="inline-block bg-[#ff0055] text-white text-[8px] font-black uppercase tracking-[0.26em] px-3 py-1.5">
              {article.category}
            </span>
          </div>

          {/* Title over image */}
          <div className="absolute bottom-0 left-0 right-0 px-6 md:px-8 pb-7 z-10">
            <h1 className="font-heading text-[1.7rem] md:text-[2.6rem] lg:text-[3rem] font-black uppercase leading-[1.04] tracking-tight text-white mb-4 group-hover:text-[#ff0055] transition-colors duration-300">
              {article.title}
            </h1>
            <div className="flex items-center gap-5 flex-wrap">
              <time className="text-[9px] font-bold uppercase tracking-wider text-white/45">
                {formatDate(article.date, i18n.language)}
              </time>
              <span className="text-[9px] font-black uppercase tracking-[0.16em] text-white/60 border border-white/20 px-3 py-1 group-hover:border-[#ff0055] group-hover:text-[#ff0055] transition-all duration-200">
                {t("home.read_article")}
              </span>
            </div>
          </div>
        </div>

        {/* Excerpt */}
        <div
          className="text-[#475569] text-base md:text-[1.05rem] leading-relaxed border-l-[3px] border-[#ff0055] pl-5 max-w-[800px]"
          dangerouslySetInnerHTML={{ __html: article.excerpt }}
        />
      </Link>
    </article>
  );
}

function GridArticle({ article, t, i18n }: { article: ArticleMeta; t: (key: string) => string; i18n: { language: string } }) {
  return (
    <article>
      <Link href={`/blog/${article.slug}`} className="group block h-full">
        {/* Card image */}
        <div className="relative w-full aspect-[16/9] bg-[#1e293b] overflow-hidden mb-4">
          {article.coverImage && (
            <Image
              src={article.coverImage}
              alt={article.title}
              fill
              className="object-cover object-center group-hover:scale-[1.03] transition-transform duration-500 ease-out"
            />
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
          <div className="absolute top-3 left-3 z-10">
            <span className="inline-block bg-[#0a192f]/80 backdrop-blur-sm text-white text-[7px] font-black uppercase tracking-[0.2em] px-2.5 py-1">
              {article.category}
            </span>
          </div>
        </div>

        {/* Text */}
        <time className="block text-[8px] font-bold uppercase tracking-wider text-[#94a3b8] mb-2.5">
          {formatDate(article.date, i18n.language)}
        </time>
        <h3 className="font-heading text-[1.1rem] md:text-[1.25rem] font-black uppercase leading-[1.1] tracking-tight text-[#0a192f] group-hover:text-[#ff0055] transition-colors duration-200 mb-3">
          {article.title}
        </h3>
        <div
          className="text-[#64748b] text-sm leading-relaxed line-clamp-3 mb-4"
          dangerouslySetInnerHTML={{ __html: article.excerpt }}
        />
        <span className="text-[8px] font-black uppercase tracking-[0.16em] text-[#ff0055]">
          {t("home.read_analysis")}
        </span>
      </Link>
    </article>
  );
}

// Squadre nella Strip
const STRIP_TEAMS = [
  { name: "Sassuolo",    slug: "sassuolo",    logo: "/logos/Sassuolo.png" },
  { name: "Como",        slug: "como",        logo: "/logos/Como.png" },
  { name: "Atalanta",    slug: "atalanta",    logo: "/logos/Atalanta.png" },
  { name: "Palermo",     slug: "palermo",     logo: "/logos/Palermo.png" },
  { name: "Fiorentina",  slug: "fiorentina",  logo: "/logos/Fiorentina.png" },
  { name: "Lecce",       slug: "lecce",       logo: "/logos/Lecce.png" },
  { name: "Parma",       slug: "parma",       logo: "/logos/Parma.png" },
  { name: "Torino",      slug: "torino",      logo: "/logos/Torino.png" },
];

interface HomePageContentProps {
  /** Metadata for ALL locales keyed by locale code. */
  articlesByLocale: Record<Locale, ArticleMeta[]>;
}

export default function HomePageContent({ articlesByLocale }: HomePageContentProps) {
  const { t, i18n } = useTranslation();

  // Pick the right articles for the currently active UI language
  const locale = resolveLocale(i18n.language);
  const articles = articlesByLocale[locale] ?? articlesByLocale["en"] ?? articlesByLocale["it"] ?? [];
  const [hero, ...grid] = articles;

  return (
    <div className="min-h-screen bg-[#F8F9FA] text-[#0f172a] font-body">

      {/* ── MASTHEAD ── */}
      <div className="border-b border-[#e2e8f0] bg-white">
        <div className="max-w-[1120px] mx-auto px-5 py-5 flex items-end justify-between gap-4">
          <div>
            <p className="text-[7px] font-black uppercase tracking-[0.35em] text-[#94a3b8] mb-1">
              {t("home.magazine_title")}
            </p>
            <p className="font-heading text-[12px] font-black uppercase tracking-[0.1em] text-[#0a192f]">
              {t("home.magazine_subtitle")}
            </p>
          </div>
          <p className="hidden sm:block text-[8px] font-bold text-[#94a3b8] tabular-nums text-right">
            {new Date().toLocaleDateString(
              i18n.language?.startsWith("it") ? "it-IT" :
              i18n.language?.startsWith("es") ? "es-ES" :
              i18n.language?.startsWith("fr") ? "fr-FR" : "en-US",
              {
                weekday: "long",
                year: "numeric",
                month: "long",
                day: "numeric",
              }
            )}
          </p>
        </div>
      </div>

      {/* ── STRIP SCUDETTI ── */}
      <div className="bg-white border-b border-[#e2e8f0]">
        <div className="max-w-[1120px] mx-auto px-5">
          <div className="flex items-center gap-1 overflow-x-auto scrollbar-hide py-3">
            <span className="text-[7px] font-black uppercase tracking-[0.28em] text-[#94a3b8] whitespace-nowrap mr-4 flex-shrink-0">
              {t("home.teams_strip_label")}
            </span>
            {STRIP_TEAMS.map((team) => (
              <Link
                key={team.slug}
                href={`/${team.slug}`}
                className="flex-shrink-0 group flex flex-col items-center gap-1 px-3 py-1 rounded-sm hover:bg-[#f8f9fa] transition-colors duration-150"
                title={team.name}
              >
                <div className="relative w-9 h-9 flex items-center justify-center">
                  {team.logo ? (
                    <Image
                      src={team.logo}
                      alt={team.name}
                      width={36}
                      height={36}
                      className="object-contain group-hover:scale-110 transition-transform duration-200"
                      unoptimized
                    />
                  ) : (
                    <span className="text-[8px] font-black uppercase text-[#0a192f] text-center leading-none">
                      {team.name.slice(0, 3)}
                    </span>
                  )}
                </div>
                <span className="text-[6px] font-black uppercase tracking-wide text-[#94a3b8] group-hover:text-[#ff0055] transition-colors duration-150 whitespace-nowrap">
                  {team.name}
                </span>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* ── CONTENT ── */}
      <div className="max-w-[1120px] mx-auto px-5 py-10">

        {/* Section label */}
        <div className="flex items-center gap-3 mb-9">
          <span className="block w-8 h-[2px] bg-[#ff0055]" />
          <span className="text-[8px] font-black uppercase tracking-[0.3em] text-[#ff0055]">
            {t("home.analysis_section_label")}
          </span>
          <span className="block flex-1 h-px bg-[#e2e8f0]" />
        </div>

        {/* Hero */}
        {hero && <HeroArticle article={hero} t={t} i18n={i18n} />}

        {/* Divider */}
        {grid.length > 0 && (
          <div className="flex items-center gap-3 mb-10">
            <span className="block flex-1 h-px bg-[#e2e8f0]" />
            <span className="text-[7px] font-black uppercase tracking-[0.3em] text-[#cbd5e1]">
              {t("home.other_articles")}
            </span>
            <span className="block flex-1 h-px bg-[#e2e8f0]" />
          </div>
        )}

        {/* 2×2 Grid */}
        {grid.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-9 lg:gap-12 mb-16">
            {grid.map((article) => (
              <GridArticle key={article.slug} article={article} t={t} i18n={i18n} />
            ))}
          </div>
        )}

      </div>
    </div>
  );
}
