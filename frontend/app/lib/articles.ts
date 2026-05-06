import fs from "fs";
import path from "path";
import matter from "gray-matter";
import { remark } from "remark";
import remarkHtml from "remark-html";

const LOCALE_DIRS = ["it", "en", "es", "fr", "de"] as const;
export type Locale = (typeof LOCALE_DIRS)[number];

// Fixed display order for the 5 canonical articles
const CANONICAL_ORDER = [
  "timeline",
  "meritometro",
  "scout-engine",
  "fanta-draft",
  "nerd-zone",
];

export interface ArticleMeta {
  slug: string;
  title: string;
  excerpt: string;
  coverImage: string;
  date: string;
  category: string;
}

export interface Article extends ArticleMeta {
  contentHtml: string;
}

export interface ArticleByLocale {
  slug: string;
  articles: Partial<Record<Locale, Article>>;
}

function articlesDir(locale: string): string {
  return path.join(process.cwd(), "content/articles", locale);
}

function readMetaForLocale(filename: string, locale: string): ArticleMeta | null {
  const slug = filename.replace(/\.md$/, "");
  const dir = articlesDir(locale);
  const filePath = path.join(dir, filename);
  if (!fs.existsSync(filePath)) return null;
  const raw = fs.readFileSync(filePath, "utf8");
  const { data } = matter(raw);
  return {
    slug,
    title: (data.title as string) ?? slug,
    excerpt: (data.excerpt as string) ?? "",
    coverImage: (data.coverImage as string) ?? "",
    date: (data.date as string) ?? "",
    category: (data.category as string) ?? "",
  };
}

export function getAllArticlesMeta(locale: string = "it"): ArticleMeta[] {
  const dir = articlesDir(locale);
  if (!fs.existsSync(dir)) return [];
  const files = fs.readdirSync(dir).filter((f) => f.endsWith(".md"));
  const articles = files
    .map((f) => readMetaForLocale(f, locale))
    .filter((a): a is ArticleMeta => a !== null);

  // Sort: canonical order first, then remaining by date desc
  articles.sort((a, b) => {
    const ai = CANONICAL_ORDER.indexOf(a.slug);
    const bi = CANONICAL_ORDER.indexOf(b.slug);
    if (ai !== -1 && bi !== -1) return ai - bi;
    if (ai !== -1) return -1;
    if (bi !== -1) return 1;
    return new Date(b.date).getTime() - new Date(a.date).getTime();
  });

  return articles;
}

export async function getArticle(slug: string, locale: string = "it"): Promise<Article | null> {
  const dir = articlesDir(locale);
  const filePath = path.join(dir, `${slug}.md`);
  if (!fs.existsSync(filePath)) return null;

  const raw = fs.readFileSync(filePath, "utf8");
  const { data, content } = matter(raw);

  const processed = await remark()
    .use(remarkHtml, { sanitize: false })
    .process(content);

  return {
    slug,
    title: (data.title as string) ?? slug,
    excerpt: (data.excerpt as string) ?? "",
    coverImage: (data.coverImage as string) ?? "",
    date: (data.date as string) ?? "",
    category: (data.category as string) ?? "",
    contentHtml: processed.toString(),
  };
}

/**
 * Load an article in ALL available locales at once.
 * Used to pass all variants to a client component that picks based on i18n.language.
 */
export async function getArticleAllLocales(slug: string): Promise<ArticleByLocale | null> {
  const results: ArticleByLocale = { slug, articles: {} };
  let found = false;

  for (const locale of LOCALE_DIRS) {
    const article = await getArticle(slug, locale);
    if (article) {
      results.articles[locale] = article;
      found = true;
    }
  }

  return found ? results : null;
}

/**
 * Fetch ArticleMeta for ALL locales at once.
 * Returns a Record keyed by locale code, so a client component
 * can pick the right language based on i18n.language.
 */
export function getAllArticlesMetaAllLocales(): Record<Locale, ArticleMeta[]> {
  const result: Partial<Record<Locale, ArticleMeta[]>> = {};
  for (const locale of LOCALE_DIRS) {
    result[locale] = getAllArticlesMeta(locale);
  }
  return result as Record<Locale, ArticleMeta[]>;
}

export function getAllSlugs(locale: string = "it"): string[] {
  const dir = articlesDir(locale);
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((f) => f.endsWith(".md"))
    .map((f) => f.replace(/\.md$/, ""));
}
