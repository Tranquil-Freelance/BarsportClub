import { getAllArticlesMetaAllLocales } from "@/app/lib/articles";
import HomePageContent from "@/app/components/home/HomePageContent";

export default async function HomePage() {
  const articlesByLocale = getAllArticlesMetaAllLocales();

  return <HomePageContent articlesByLocale={articlesByLocale} />;
}
