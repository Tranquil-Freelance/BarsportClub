"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { STORAGE_KEY } from "../i18n/config";

const LANGUAGES = [
  { code: "it", label: "ITA", name: "Italiano" },
  { code: "en", label: "ENG", name: "English" },
  { code: "es", label: "ESP", name: "Español" },
  { code: "fr", label: "FRA", name: "Français" },
  { code: "de", label: "DEU", name: "Deutsch" },
];

function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const [isMounted, setIsMounted] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isOpen) return;

    const handleMouseDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsOpen(false);
    };

    document.addEventListener("mousedown", handleMouseDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("mousedown", handleMouseDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  const handleSelect = (code: string) => {
    i18n.changeLanguage(code);
    try { localStorage.setItem(STORAGE_KEY, code); } catch { /* storage unavailable */ }
    setIsOpen(false);
  };

  if (!isMounted) return <div className="w-16 h-8 flex-shrink-0" />;

  const currentLang = i18n.language?.slice(0, 2) ?? "en";
  const current = LANGUAGES.find((l) => l.code === currentLang) ?? LANGUAGES[1];

  return (
    <div ref={ref} className="relative flex-shrink-0">
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        className={`flex items-center gap-1.5 py-7 text-sm font-bold tracking-widest uppercase transition-all duration-300 transform hover:-translate-y-0.5
          ${isOpen ? "text-white" : "text-slate-400 hover:text-white"}
        `}
      >
        <span>{current.label}</span>
        <svg
          className={`w-3 h-3 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2.5}
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <ul
          role="listbox"
          aria-label="Select language"
          className="absolute right-0 top-full mt-1 bg-[#0d2137] border border-slate-700 rounded shadow-xl z-50 min-w-[140px] py-1"
        >
          {LANGUAGES.map((lang) => (
            <li
              key={lang.code}
              role="option"
              aria-selected={lang.code === currentLang}
              onClick={() => handleSelect(lang.code)}
              className={`flex items-center gap-3 px-4 py-2.5 text-sm font-bold tracking-wider cursor-pointer transition-colors hover:bg-slate-800
                ${lang.code === currentLang ? "text-[#FF2A6D]" : "text-slate-300"}
              `}
            >
              <span className="w-8 flex-shrink-0">{lang.label}</span>
              <span className="text-xs font-normal text-slate-500">{lang.name}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function UniversalHeader() {
  const pathname = usePathname();

  const navItems = [
    { label: "PROSSIMO TURNO", href: "/prossimo-turno" },
    { label: "CAMPIONATI", href: "/campionati" },
    { label: "BETTING", href: "/betting" },
    { label: "MERITOMETRO", href: "/meritometro" },
    { label: "SCOUT ENGINE", href: "/scout-engine" },
    { label: "NERD ZONE", href: "/nerd-zone" },
    { label: "FANTA DRAFT", href: "/fanta-draft" },
  ];

  return (
    <header className="bg-[#0a192f] text-white border-b border-slate-800 sticky top-0 z-[100] shadow-lg">
      <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">

          {/* Logo & Brand */}
          <div className="flex-shrink-0 flex items-center gap-4">
            <div className="w-10 h-10 relative flex items-center justify-center bg-[#FF2A6D] rounded-sm transform rotate-45 shadow-[0_0_10px_rgba(255,42,109,0.5)]">
              <div className="w-5 h-5 bg-[#0a192f] border border-white"></div>
            </div>
            <Link href="/" className="font-black text-3xl tracking-tighter italic text-white drop-shadow-sm">
              barsport<span className="text-slate-400">.club</span>
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-10">
            {navItems.map((item) => {
              const isActive = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`relative py-7 text-sm font-bold tracking-widest uppercase transition-all duration-300 transform hover:-translate-y-0.5
                    ${isActive ? "text-white" : "text-slate-400 hover:text-white"}
                  `}
                >
                  {item.label}
                  {isActive && (
                    <span className="absolute bottom-0 left-0 w-full h-1 bg-[#FF2A6D] rounded-t-md shadow-[0_0_10px_#FF2A6D]"></span>
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Language Switcher — always visible, incl. mobile */}
          <LanguageSwitcher />
        </div>
      </div>
    </header>
  );
}
