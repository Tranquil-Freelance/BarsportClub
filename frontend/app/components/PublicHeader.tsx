"use client";

import { useState } from "react";
import Link from "next/link";
import { Menu, X, Trophy } from "lucide-react";

export default function PublicHeader() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const navLinks = [
    { label: "Home", href: "/" },
    { label: "Serie A", href: "/serie-a" },
    { label: "Premier League", href: "/premier-league" },
    { label: "Top Players", href: "/top-players" },
    { label: "Matches", href: "/matches" },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-gray-200 bg-white shadow-sm">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo / Branding */}
          <div className="flex items-center gap-3">
            <Trophy className="h-8 w-8 text-emerald-600" />
            <Link
              href="/"
              className="text-2xl font-bold tracking-tight text-gray-900 hover:text-emerald-700"
            >
              xPalermoStat
            </Link>
            <span className="hidden rounded-full bg-emerald-100 px-3 py-1 text-sm font-medium text-emerald-800 md:inline">
              Advanced Football Analytics
            </span>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-sm font-medium text-gray-700 hover:text-emerald-600 hover:underline underline-offset-4 transition-colors"
              >
                {link.label}
              </Link>
            ))}
          </nav>

          {/* Mobile menu button */}
          <button
            type="button"
            className="rounded-md p-2 text-gray-700 hover:bg-gray-100 hover:text-gray-900 md:hidden"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-label="Toggle menu"
          >
            {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="border-t border-gray-200 py-4 md:hidden">
            <div className="flex flex-col space-y-3">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="rounded-lg px-4 py-2 text-base font-medium text-gray-700 hover:bg-gray-100 hover:text-emerald-600"
                  onClick={() => setIsMenuOpen(false)}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </header>
  );
}