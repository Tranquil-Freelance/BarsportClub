"use client";

import { useTranslation } from "react-i18next";
import "../i18n/config";
import ArticleCard from "@/app/components/blog/ArticleCard";
import { WpPost } from "@/app/types/blog";
import { blogArticles, toWpPost, BlogArticleLocale } from "@/app/lib/blogContent";

function getLocale(code: string): BlogArticleLocale {
  if (code === "it" || code === "en" || code === "es" || code === "fr" || code === "de") return code;
  return "en";
}

export default function BlogIndexPage() {
  const { t, i18n } = useTranslation();
  const locale = getLocale(i18n.language);

  // Legacy posts — content now served from translation JSON
  const legacyPosts: WpPost[] = [
    {
      id: 1,
      slug: "analisi-tattica-il-nuovo-modulo",
      title: { rendered: t("blog.legacy.post_1_title") },
      excerpt: { rendered: t("blog.legacy.post_1_excerpt") },
      content: { rendered: t("blog.legacy.post_1_content") },
      date: "2025-01-15T10:30:00",
      _embedded: {
        "wp:featuredmedia": [
          {
            source_url: t("blog.legacy.post_1_img"),
            alt_text: t("blog.legacy.post_1_img_alt"),
            media_details: {
              sizes: {
                medium: {
                  source_url: t("blog.legacy.post_1_img"),
                },
              },
            },
          },
        ],
      },
    },
    {
      id: 2,
      slug: "xg-report-serie-a-winter-break",
      title: { rendered: t("blog.legacy.post_2_title") },
      excerpt: { rendered: t("blog.legacy.post_2_excerpt") },
      content: { rendered: t("blog.legacy.post_2_content") },
      date: "2025-01-10T14:45:00",
      _embedded: {
        "wp:featuredmedia": [
          {
            source_url: t("blog.legacy.post_2_img"),
            alt_text: t("blog.legacy.post_2_img_alt"),
            media_details: {
              sizes: {
                medium: {
                  source_url: t("blog.legacy.post_2_img"),
                },
              },
            },
          },
        ],
      },
    },
    {
      id: 3,
      slug: "palermo-retrospettiva-stagione",
      title: { rendered: t("blog.legacy.post_3_title") },
      excerpt: { rendered: t("blog.legacy.post_3_excerpt") },
      content: { rendered: t("blog.legacy.post_3_content") },
      date: "2025-01-05T09:15:00",
      _embedded: {
        "wp:featuredmedia": [
          {
            source_url: t("blog.legacy.post_3_img"),
            alt_text: t("blog.legacy.post_3_img_alt"),
            media_details: {
              sizes: {
                medium: {
                  source_url: t("blog.legacy.post_3_img"),
                },
              },
            },
          },
        ],
      },
    },
  ];

  // 5 fundamental articles in the current locale
  const fundamentalPosts: WpPost[] = blogArticles.map((a) => toWpPost(a, locale));

  const posts = [...legacyPosts, ...fundamentalPosts];

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="relative overflow-hidden border-b border-gray-200 bg-gray-50 py-20">
        <div className="container relative mx-auto max-w-7xl px-4 text-center">
          <h1 className="mb-4 text-5xl font-bold tracking-tight text-gray-900 md:text-6xl font-heading">
            {t("blog.title")}
          </h1>
          <p className="mx-auto max-w-3xl text-xl text-gray-600 font-body">
            {t("blog.subtitle")}
          </p>
          <p className="mt-4 text-gray-500 max-w-2xl mx-auto">
            {t("blog.description")}
          </p>
        </div>
      </header>

      {/* Main content */}
      <main className="container mx-auto max-w-7xl px-4 py-16">
        <div className="mb-12 flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">
              {t("blog.latest_articles")}
            </h2>
            <p className="mt-2 text-gray-500">
              {t("blog.articles_subtitle")}
            </p>
          </div>
          <div className="hidden rounded-full bg-palermo-pink/10 px-4 py-2 text-sm font-medium text-palermo-pink md:block">
            {t("blog.articles_count", { count: posts.length })}
          </div>
        </div>

        {/* Articles grid */}
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
          {posts.map((post) => (
            <ArticleCard
              key={post.id}
              title={post.title.rendered}
              excerpt={post.excerpt.rendered}
              date={post.date}
              slug={post.slug}
              imageUrl={
                post._embedded?.["wp:featuredmedia"]?.[0]?.source_url || null
              }
            />
          ))}
        </div>

        {/* Empty state (if no posts) */}
        {posts.length === 0 && (
          <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-12 text-center">
            <h3 className="text-2xl font-semibold text-gray-400">
              {t("blog.no_articles")}
            </h3>
            <p className="mt-2 text-gray-400">
              {t("blog.no_articles_desc")}
            </p>
          </div>
        )}

        {/* Call to action */}
        <div className="mt-20 rounded-2xl bg-gray-50 border border-gray-200 p-8 text-center">
          <h3 className="text-2xl font-bold text-gray-900">
            {t("blog.stay_updated")}
          </h3>
          <p className="mt-2 text-gray-600">
            {t("blog.newsletter_desc")}
          </p>
          <div className="mt-6 flex max-w-md mx-auto gap-4">
            <input
              type="email"
              placeholder={t("blog.email_placeholder")}
              className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder-gray-400 focus:border-palermo-pink focus:outline-none focus:ring-1 focus:ring-palermo-pink"
            />
            <button className="rounded-lg bg-palermo-pink px-6 py-3 font-semibold text-white hover:bg-pink-600 transition-colors">
              {t("blog.subscribe")}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
