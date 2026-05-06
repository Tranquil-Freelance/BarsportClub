import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Admin Portal - barsport.club",
  description: "Administrative dashboard for managing scrapers, data ingestion, and analytics",
};

export default function AdminLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="min-h-screen">
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {children}
      </main>
      <footer className="mt-12 border-t border-slate-800 bg-slate-900/50 py-6">
        <div className="mx-auto max-w-7xl px-4 text-center text-sm text-slate-500">
          <p>
            &copy; 2026 barsport.club Admin. Restricted access.
          </p>
          <p className="mt-1">
            Use this panel to trigger backend scrapers and monitor data ingestion.
          </p>
          <p className="mt-2 text-xs">
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-500"></span>{" "}
            Live scraper status updates every 30 seconds.
          </p>
        </div>
      </footer>
    </div>
  );
}