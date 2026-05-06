import type { Metadata } from "next";
import { Oswald, Inter } from "next/font/google";
import "./globals.css";
import UniversalHeader from "./components/UniversalHeader";
import Footer from "./components/Footer";
import I18nWrapper from "./components/I18nWrapper";

const oswald = Oswald({
  weight: ['400', '700'],
  subsets: ["latin"],
  variable: '--font-oswald',
});

const inter = Inter({
  subsets: ["latin"],
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: "barsport.club - Advanced Football Analytics",
  description:
    "Real-time football statistics, match insights, and player performance analytics for Serie A, Premier League, and top European leagues.",
  keywords: [
    "football analytics",
    "Serie A stats",
    "Premier League stats",
    "player performance",
    "match data",
    "barsport.club",
  ],
  authors: [{ name: "barsport.club Team" }],
  openGraph: {
    type: "website",
    title: "barsport.club - Advanced Football Analytics",
    description:
      "Real-time football statistics, match insights, and player performance analytics.",
    siteName: "barsport.club",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${oswald.variable} ${inter.variable}`}>
      <body className="bg-[#F8FAFC] text-[#0F172A] font-body antialiased selection:bg-palermo-pink selection:text-white" suppressHydrationWarning>
        <I18nWrapper>
          <UniversalHeader />
          <main className="min-h-screen">{children}</main>
          {/* Footer removed for premium magazine style */}
          <Footer />
        </I18nWrapper>
      </body>
    </html>
  );
}