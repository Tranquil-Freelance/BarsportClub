"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const PalermoNavbar = () => {
  const pathname = usePathname();

  const navLinks = [
    { label: "Home", href: "/" },
    { label: "Analisi", href: "/analisi" },
    { label: "Statistiche", href: "/statistiche" },
    { label: "Tattiche", href: "/tattiche" },
    { label: "News", href: "/news" },
  ];

  return (
    <nav className="bg-palermo-dark border-b border-zinc-800 flex justify-between items-center py-4 px-8">
      {/* Logo */}
      <div className="flex items-center space-x-3">
        <div className="h-10 w-10 rounded-full bg-gradient-to-br from-palermo-pink to-pink-600 flex items-center justify-center">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-6 w-6 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M16 8l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M5 3a2 2 0 00-2 2v1c0 8.284 6.716 15 15 15h1a2 2 0 002-2v-3.28a1 1 0 00-.684-.948l-4.493-1.498a1 1 0 00-1.21.502l-1.13 2.257a11.042 11.042 0 01-5.516-5.517l2.257-1.128a1 1 0 00.502-1.21L9.228 3.684A1 1 0 008.279 3H5z"
            />
          </svg>
        </div>
        <span className="font-heading text-2xl text-white tracking-tight">
          Palermo
        </span>
      </div>

      {/* Center Links */}
      <div className="hidden md:flex items-center space-x-10">
        {navLinks.map((link) => (
          <Link
            key={link.label}
            href={link.href}
            className={`font-heading text-sm uppercase tracking-wider transition-colors ${
              pathname === link.href
                ? "text-white border-b-4 border-palermo-pink pb-1"
                : "text-zinc-400 hover:text-white"
            }`}
          >
            {link.label}
          </Link>
        ))}
      </div>

      {/* Right Button */}
      <button className="bg-palermo-pink text-white font-heading px-4 py-1 hover:bg-pink-600 transition-colors">
        Report Partita
      </button>
    </nav>
  );
};

export default PalermoNavbar;