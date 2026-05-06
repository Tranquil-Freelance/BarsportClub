"use client";

import { useTranslation } from "react-i18next";
import "../../i18n/config";
import Link from "next/link";
import Image from "next/image";
import type { Article } from "@/app/lib/articles";

interface ArticleDetailClientProps {
  articles: Partial<Record<string, Article>>;
}

/**
 * Client component that renders the article detail page using i18n locale.
 * Receives all locale variants from the server component.
 */
export default function ArticleDetailClient({ articles }: ArticleDetailClientProps) {
  const { t, i18n } = useTranslation();

  // Pick the right locale variant — fallback to "de" → "it" → then any available
  const lang = i18n.language?.slice(0, 2);
  const article =
    articles[lang] || articles["de"] || articles["it"] || articles["en"] || Object.values(articles)[0] || null;

  if (!article) return null;

  function formatDate(dateStr: string): string {
    try {
      const locale = lang === "it" ? "it-IT" : lang === "es" ? "es-ES" : lang === "fr" ? "fr-FR" : lang === "de" ? "de-DE" : "en-US";
      return new Date(dateStr).toLocaleDateString(locale, {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
      });
    } catch {
      return dateStr;
    }
  }

  return (
    <div className="min-h-screen bg-white text-[#0f172a]">
      {/* ── COVER IMAGE — full bleed, cinematic ── */}
      <div className="relative w-full h-[380px] md:h-[520px] bg-[#0a192f] overflow-hidden">
        {article.coverImage && (
          <Image
            src={article.coverImage}
            alt={article.title}
            fill
            className="object-cover object-center"
            priority
          />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-[#050d1a]/90 via-[#050d1a]/30 to-[#050d1a]/10" />

        {/* Back nav over image */}
        <div className="absolute top-6 left-6 z-10">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-[8px] font-black uppercase tracking-[0.22em] text-white/60 hover:text-white transition-colors duration-200"
          >
            <span className="text-[#ff0055]">←</span>
            {t("blog.back_link")}
          </Link>
        </div>

        {/* Category + title over image */}
        <div className="absolute bottom-0 left-0 right-0 px-6 md:px-12 lg:px-16 pb-8 z-10 max-w-[860px]">
          <span className="inline-block bg-[#ff0055] text-white text-[7px] font-black uppercase tracking-[0.28em] px-3 py-1.5 mb-4">
            {article.category}
          </span>
          <h1 className="font-heading text-[1.8rem] md:text-[2.6rem] lg:text-[3.1rem] font-black uppercase leading-[1.05] tracking-tight text-white">
            {article.title}
          </h1>
        </div>
      </div>

      {/* ── ARTICLE HEADER ── */}
      <div className="max-w-[720px] mx-auto px-5 md:px-8 pt-9 pb-2">
        {/* Date */}
        <time className="block text-[9px] font-bold uppercase tracking-[0.24em] text-[#94a3b8] mb-5">
          {formatDate(article.date)}
        </time>

        {/* Excerpt / deck */}
        <div
          className="text-lg md:text-xl text-[#334155] leading-[1.65] font-medium border-l-[3px] border-[#ff0055] pl-5 mb-8"
          dangerouslySetInnerHTML={{ __html: article.excerpt }}
        />

        {/* Divider */}
        <div className="flex items-center gap-3 mb-10">
          <span className="block w-6 h-[2px] bg-[#ff0055]" />
          <span className="block flex-1 h-px bg-[#f1f5f9]" />
        </div>
      </div>

      {/* ── ARTICLE BODY ── */}
      <main className="max-w-[720px] mx-auto px-5 md:px-8 pb-20">
        <div
          className="
            prose-article
            text-[#1e293b] text-[1.05rem] leading-[1.82]
            [&_h2]:font-heading [&_h2]:text-[1.5rem] [&_h2]:md:text-[1.75rem] [&_h2]:font-black [&_h2]:uppercase [&_h2]:tracking-tight [&_h2]:text-[#0a192f] [&_h2]:mt-12 [&_h2]:mb-5 [&_h2]:leading-[1.1] [&_h2]:border-b [&_h2]:border-[#f1f5f9] [&_h2]:pb-3
            [&_h3]:font-heading [&_h3]:text-[1.1rem] [&_h3]:md:text-[1.2rem] [&_h3]:font-black [&_h3]:uppercase [&_h3]:tracking-tight [&_h3]:text-[#0a192f] [&_h3]:mt-9 [&_h3]:mb-4 [&_h3]:leading-[1.15]
            [&_p]:mb-6 [&_p]:text-[#334155] [&_p]:leading-[1.82]
            [&_strong]:text-[#0a192f] [&_strong]:font-black
            [&_em]:text-[#475569] [&_em]:not-italic [&_em]:font-semibold
            [&_a]:text-[#ff0055] [&_a]:font-bold [&_a]:no-underline [&_a]:hover:underline
            [&_ul]:mb-6 [&_ul]:pl-6 [&_ul]:space-y-2
            [&_ol]:mb-6 [&_ol]:pl-6 [&_ol]:space-y-2
            [&_li]:text-[#334155] [&_li]:leading-relaxed [&_li]:marker:text-[#ff0055]
            [&_blockquote]:border-l-[3px] [&_blockquote]:border-[#ff0055] [&_blockquote]:pl-5 [&_blockquote]:my-8 [&_blockquote]:text-[#475569] [&_blockquote]:text-lg [&_blockquote]:italic [&_blockquote]:leading-relaxed
            [&_table]:w-full [&_table]:mb-8 [&_table]:border-collapse [&_table]:text-sm
            [&_th]:text-left [&_th]:font-black [&_th]:uppercase [&_th]:tracking-wider [&_th]:text-[8px] [&_th]:text-[#94a3b8] [&_th]:pb-2 [&_th]:border-b-2 [&_th]:border-[#e2e8f0]
            [&_td]:py-2.5 [&_td]:text-[#334155] [&_td]:border-b [&_td]:border-[#f1f5f9]
            [&_hr]:my-10 [&_hr]:border-[#f1f5f9]
            [&_img]:rounded-sm [&_img]:shadow-sm [&_img]:my-8
            [&_code]:bg-[#f1f5f9] [&_code]:text-[#e11d48] [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-sm [&_code]:font-mono
          "
          dangerouslySetInnerHTML={{ __html: article.contentHtml }}
        />
      </main>

      {/* ── FOOTER NAV ── */}
      <div className="border-t border-[#f1f5f9] bg-[#F8F9FA]">
        <div className="max-w-[720px] mx-auto px-5 md:px-8 py-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-[9px] font-black uppercase tracking-[0.2em] text-[#0a192f] hover:text-[#ff0055] transition-colors duration-200"
          >
            <span className="text-[#ff0055]">←</span>
            {t("blog.back_to_magazine")}
          </Link>
          <Link
            href="/tools"
            className="inline-flex items-center gap-2 text-[9px] font-black uppercase tracking-[0.2em] text-[#0a192f] border border-[#0a192f] px-5 py-2.5 hover:bg-[#0a192f] hover:text-white transition-all duration-200"
          >
            {t("blog.explore_data")}
          </Link>
        </div>
      </div>
    </div>
  );
}
