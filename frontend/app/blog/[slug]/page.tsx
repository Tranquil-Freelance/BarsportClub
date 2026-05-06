import { notFound } from "next/navigation";
import { getArticleAllLocales, getAllSlugs } from "@/app/lib/articles";
import ArticleDetailClient from "@/app/components/blog/ArticleDetailClient";
import type { Metadata } from "next";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateStaticParams() {
  // Generate params from Italian slugs (canonical source)
  return getAllSlugs("it").map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const result = await getArticleAllLocales(slug);
  if (!result) return { title: "Article not found · Barsport.club" };

  // Use German as default, then Italian, then any available
  const article = result.articles["de"] || result.articles["it"] || result.articles["en"] || Object.values(result.articles)[0];
  if (!article) return { title: "Article not found · Barsport.club" };

  return {
    title: `${article.title} · Barsport.club`,
    description: article.excerpt.replace(/<[^>]+>/g, "").slice(0, 155),
    openGraph: {
      title: article.title,
      description: article.excerpt.replace(/<[^>]+>/g, "").slice(0, 155),
      images: article.coverImage ? [{ url: article.coverImage }] : [],
    },
  };
}

export default async function ArticlePage({ params }: PageProps) {
  const { slug } = await params;
  const result = await getArticleAllLocales(slug);

  if (!result) {
    notFound();
  }

  // Pass all locale variants to the client component
  return <ArticleDetailClient articles={result.articles} />;
}
