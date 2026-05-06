import type { Metadata } from "next";
import Link from "next/link";
import { Crown, Trophy, Users, BarChart3 } from "lucide-react";

export const metadata: Metadata = {
  title: "barsport.club - Focus Rosanero",
  description: "Deep‑dive analytics and metrics for Palermo Football Club",
};

export default function PalermoLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="min-h-screen">

      {/* Theme wrapper – ensures all child components are aware of the Palermo context */}
      <div
        className="palermo-theme-wrapper"
        data-theme="palermo"
        // This wrapper can be targeted by CSS or JS to enforce pink/black styling
      >
        <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </div>

      {/* Palermo‑specific footer */}
      <footer className="mt-16 border-t border-pink-900/30 bg-black/50 py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-between gap-6 md:flex-row">
            <div className="text-center md:text-left">
              <div className="flex items-center justify-center md:justify-start gap-3">
                <div className="h-8 w-8 rounded-full bg-gradient-to-br from-pink-600 to-black" />
                <span className="text-xl font-bold text-white">
                  xPalermoStat
                </span>
              </div>
              <p className="mt-2 max-w-md text-sm text-zinc-400">
                Independent analytics platform dedicated to Palermo FC. Data sourced from Opta,
                Advanced Analytics Engine, and Serie B official feeds.
              </p>
            </div>
            <div className="flex items-center gap-6">
              <a
                href="https://palermocalcio.it"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-pink-400 hover:text-pink-300 underline"
              >
                Official Club Site
              </a>
              <a
                href="#"
                className="text-sm text-zinc-400 hover:text-white"
              >
                Data Methodology
              </a>
              <a
                href="#"
                className="text-sm text-zinc-400 hover:text-white"
              >
                Privacy
              </a>
            </div>
          </div>
          <div className="mt-8 text-center text-xs text-zinc-500">
            © 2026 xPalermoStat. This is a fan project, not affiliated with
            Palermo FC.
          </div>
        </div>
      </footer>
    </div>
  );
}