import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { sassuoloArticles } from "@/app/sassuolo/data";

interface Props {
  params: Promise<{ id: string }>;
}

export async function generateStaticParams() {
  return sassuoloArticles.map((a) => ({ id: a.id }));
}

export default async function SassuoloArticlePage({ params }: Props) {
  const { id } = await params;
  const article = sassuoloArticles.find((a) => a.id === id);

  if (!article) notFound();

  return (
    <div className="min-h-screen bg-white">
      {/* ── Back navigation ── */}
      <div className="sticky top-0 z-50 bg-white/95 backdrop-blur-sm border-b border-[#e2e8f0]">
        <div className="max-w-[1120px] mx-auto px-5 py-4 flex items-center justify-between">
          <Link
            href="/sassuolo"
            className="inline-flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-[#64748b] hover:text-[#ff0055] transition-colors duration-200"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M19 12H5" />
              <path d="M12 19l-7-7 7-7" />
            </svg>
            Torna allo Speciale
          </Link>
          <span className="text-[9px] font-black uppercase tracking-[0.2em] text-[#94a3b8]">
            {article.category}
          </span>
        </div>
      </div>

      {/* ── Hero image ── */}
      <div className="relative w-full h-[360px] md:h-[520px] lg:h-[600px] bg-[#0a192f] overflow-hidden">
        <Image
          src={article.image}
          alt={article.title}
          fill
          className="object-cover object-top"
          priority
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />

        {/* Overlay title */}
        <div className="absolute bottom-0 left-0 right-0 px-5 md:px-8 pb-10 max-w-[1120px] mx-auto">
          <span className="inline-block bg-[#ff0055] text-white text-[8px] font-black uppercase tracking-[0.26em] px-3 py-1.5 mb-4">
            {article.category}
          </span>
          <h1 className="font-heading text-[1.8rem] md:text-[3rem] lg:text-[3.8rem] font-black uppercase leading-[1.04] tracking-tight text-white max-w-[960px]">
            {article.title}
          </h1>
          {article.subtitle && (
            <p className="text-white/60 text-sm md:text-base italic mt-3 max-w-[640px]">
              {article.subtitle}
            </p>
          )}
        </div>
      </div>

      {/* ── Body content ── */}
      <div className="max-w-3xl mx-auto px-5 py-12 md:py-16">
        <div className="space-y-6 text-[#1e293b] text-base md:text-[1.1rem] leading-[1.85]">
          {article.content.map((paragraph, i) => (
            <p
              key={i}
              dangerouslySetInnerHTML={{ __html: paragraph }}
              className="first:border-l-[3px] first:border-[#ff0055] first:pl-5 first:text-[#475569]"
            />
          ))}
        </div>

        {/* Footer */}
        <div className="mt-16 pt-8 border-t border-[#e2e8f0]">
          <Link
            href="/sassuolo"
            className="inline-flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-[#ff0055] hover:text-[#0a192f] transition-colors duration-200"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M19 12H5" />
              <path d="M12 19l-7-7 7-7" />
            </svg>
            Torna allo Speciale Sassuolo
          </Link>
        </div>
      </div>
    </div>
  );
}
