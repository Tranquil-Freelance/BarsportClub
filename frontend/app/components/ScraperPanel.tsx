"use client";

import { useState } from "react";

const API_ROOT = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ScraperPanel() {
  const [matchId, setMatchId] = useState<string>("27362");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleScrape = async () => {
    const id = parseInt(matchId, 10);
    if (isNaN(id) || id <= 0) {
      setError("Please enter a valid positive match ID.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`${API_ROOT}/api/admin/scrape-match/${id}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      const contentType = response.headers.get("content-type");
      let data: any;
      if (contentType && contentType.includes("application/json")) {
        data = await response.json();
      } else {
        const text = await response.text();
        throw new Error(`Expected JSON but got ${contentType || "no content-type"}: ${text.slice(0, 200)}`);
      }

      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}: ${JSON.stringify(data)}`);
      }

      setSuccess(`✅ ${data.message || "Match scraped and stored successfully."}
        Home team: ${data.home_team}
        Away team: ${data.away_team}
        Shots (home/away/total): ${data.shots_home}/${data.shots_away}/${data.shots_total}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(`❌ ${message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 shadow-lg">
      <h3 className="mb-4 text-lg font-semibold text-slate-200">
        Match Data Scraper
      </h3>
      <p className="mb-6 text-sm text-slate-400">
        Insert the match ID to scrape shot data and store it in the database.
        The frontend will then be able to read the cached data instead of performing live scraping.
      </p>

      <div className="space-y-4">
        <div>
          <label htmlFor="match-id" className="block text-sm font-medium text-slate-300 mb-1">
            Match ID
          </label>
          <input
            id="match-id"
            type="number"
            min="1"
            value={matchId}
            onChange={(e) => setMatchId(e.target.value)}
            className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-palermo-pink focus:border-transparent"
            placeholder="e.g., 27362"
            disabled={isLoading}
          />
        </div>

        <button
          onClick={handleScrape}
          disabled={isLoading}
          className="w-full bg-palermo-pink hover:bg-pink-600 text-white font-heading uppercase font-bold tracking-wider py-3 px-4 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Scraping in progress…</span>
            </>
          ) : (
            "Sincronizza Match (Scraping)"
          )}
        </button>

        {error && (
          <div className="p-4 border border-red-800 bg-red-900/30 rounded-lg">
            <p className="text-red-300 text-sm font-medium">{error}</p>
          </div>
        )}

        {success && (
          <div className="p-4 border border-emerald-800 bg-emerald-900/20 rounded-lg">
            <p className="text-emerald-300 text-sm whitespace-pre-line">{success}</p>
          </div>
        )}
      </div>

      <div className="mt-6 pt-4 border-t border-slate-800">
        <h4 className="text-sm font-semibold text-slate-300 mb-2">How it works</h4>
        <ul className="text-sm text-slate-400 space-y-1">
          <li>• The scraper fetches shot data from external sources for the given match ID.</li>
          <li>• Data is saved in PostgreSQL (Match & Shot tables).</li>
          <li>• After scraping, the frontend can retrieve the data via <code className="text-palermo-pink">GET /api/match-data/{matchId}</code>.</li>
          <li>• If the match is already stored, existing shots will be replaced.</li>
        </ul>
      </div>
    </div>
  );
}