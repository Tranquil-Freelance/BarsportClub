"use client";

import { useState, useEffect, useRef } from "react";
import { Search, X } from "lucide-react";
import { useTranslation } from "react-i18next";
import "../../i18n/config";

// Mock search results
const mockResults = [
  { id: 1, type: "player", name: "Paulo Dybala", team: "Roma" },
  { id: 2, type: "team", name: "Palermo", league: "Serie B" },
  { id: 3, type: "player", name: "Lautaro Martínez", team: "Inter" },
  { id: 4, type: "team", name: "Juventus", league: "Serie A" },
  { id: 5, type: "player", name: "Khvicha Kvaratskhelia", team: "Napoli" },
  { id: 6, type: "team", name: "AC Milan", league: "Serie A" },
];

export default function GlobalSearch() {
  const { t } = useTranslation();
  const [query, setQuery] = useState("");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [filteredResults, setFilteredResults] = useState(mockResults);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Filter results based on query
  useEffect(() => {
    if (query.trim().length >= 2) {
      const lowerQuery = query.toLowerCase();
      const filtered = mockResults.filter(
        (item) =>
          item.name.toLowerCase().includes(lowerQuery) ||
          (item.type === "player" && item.team?.toLowerCase().includes(lowerQuery)) ||
          (item.type === "team" && item.league?.toLowerCase().includes(lowerQuery))
      );
      setFilteredResults(filtered);
      setIsDropdownOpen(true);
    } else {
      setIsDropdownOpen(false);
    }
  }, [query]);

  const handleClear = () => {
    setQuery("");
    setIsDropdownOpen(false);
  };

  const handleResultClick = (result: (typeof mockResults)[0]) => {
    alert(`Navigating to ${result.type}: ${result.name}`);
    setQuery(result.name);
    setIsDropdownOpen(false);
  };

  return (
    <div className="relative w-full max-w-md" ref={wrapperRef} suppressHydrationWarning>
      {/* Search input */}
      <div className="relative flex items-center">
        <Search className="absolute left-3 h-5 w-5 text-slate-400" aria-hidden="true" />
        <input
          type="text"
          placeholder={t('search.placeholder')}
          aria-label={t('search.placeholder')}
          className="w-full rounded-lg border border-slate-700 bg-slate-800/80 py-3 pl-10 pr-10 text-sm text-white placeholder-slate-400 shadow-inner focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query.length >= 2 && setIsDropdownOpen(true)}
        />
        {query && (
          <button
            onClick={handleClear}
            className="absolute right-3 rounded-full p-1 text-slate-400 hover:bg-slate-700 hover:text-white"
            aria-label={t('search.clear')}
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Dropdown results */}
      {isDropdownOpen && filteredResults.length > 0 && (
        <div className="absolute z-50 mt-2 w-full rounded-xl border border-slate-700 bg-slate-900 shadow-2xl">
          <div className="p-3">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                {t('search.quick_results')}
              </span>
              <span className="rounded-full bg-slate-800 px-2 py-1 text-xs text-slate-300">
                {t('search.results_count', { n: filteredResults.length })}
              </span>
            </div>
            <ul className="space-y-2">
              {filteredResults.map((result) => (
                <li
                  key={result.id}
                  className="group cursor-pointer rounded-lg border border-slate-800 bg-slate-800/50 p-3 transition-all hover:border-emerald-700 hover:bg-emerald-950/30"
                  onClick={() => handleResultClick(result)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <div
                          className={`h-2 w-2 rounded-full ${result.type === "player" ? "bg-emerald-500" : "bg-pink-500"}`}
                        />
                        <span className="font-medium text-white">{result.name}</span>
                      </div>
                      <div className="ml-4 mt-1 flex items-center gap-2 text-xs text-slate-400">
                        {result.type === "player" ? (
                          <>
                            <span className="capitalize">{result.type}</span>
                            <span className="text-slate-500">•</span>
                            <span>{result.team}</span>
                          </>
                        ) : (
                          <>
                            <span className="capitalize">{result.type}</span>
                            <span className="text-slate-500">•</span>
                            <span>{result.league}</span>
                          </>
                        )}
                      </div>
                    </div>
                    <div className="hidden group-hover:block">
                      <div className="rounded-full bg-emerald-900/50 px-3 py-1 text-xs font-medium text-emerald-300">
                        View
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
            <div className="mt-3 border-t border-slate-800 pt-3">
              <button className="w-full rounded-lg bg-slate-800 py-2 text-sm font-medium text-slate-300 hover:bg-slate-700">
                {t('search.advanced')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {isDropdownOpen && filteredResults.length === 0 && (
        <div className="absolute z-50 mt-2 w-full rounded-xl border border-slate-700 bg-slate-900 p-6 text-center shadow-2xl">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-slate-800">
            <Search className="h-6 w-6 text-slate-500" aria-hidden="true" />
          </div>
          <h4 className="mb-1 text-lg font-semibold text-white">{t('search.no_results')}</h4>
          <p className="text-sm text-slate-400">
            {t('search.no_results_desc')}
          </p>
          <button
            onClick={handleClear}
            className="mt-4 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-700"
          >
            {t('search.clear')}
          </button>
        </div>
      )}
    </div>
  );
}
