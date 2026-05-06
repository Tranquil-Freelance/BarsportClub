"use client";

import { useEffect, useState } from "react";

type Match = {
  id: number;
  home_team: string;
  away_team: string;
  home_score: number | null;
  away_score: number | null;
  status: string | null;
  start_time: string | null; // ISO string
  understat_id: number | null;
  last_scraped_at: string | null; // ISO string
  scraping_status: string | null; // "PENDING", "SUCCESS", "FAILED", "RETRYING", "PROCESSING"
  error_log: string | null;
  home_xg: number | null;
  away_xg: number | null;
  home_shots: number | null;
  away_shots: number | null;
  home_shots_on_target: number | null;
  away_shots_on_target: number | null;
};

export default function ScraperDashboard() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentDate] = useState(() => new Date().toISOString().split("T")[0]); // YYYY-MM-DD

  const fetchMatches = async () => {
    try {
      const res = await fetch("/api/matches");
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      const data = await res.json();
      setMatches(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const triggerManualScrape = async (matchId: number) => {
    if (!confirm(`Force scrape for match ${matchId}? This will call the external API and update the database.`)) return;
    try {
      const res = await fetch(`/api/admin/scrape-match/${matchId}`, { method: "POST" });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Scrape failed: ${text}`);
      }
      const result = await res.json();
      alert(`Success: ${result.message}`);
      // Refresh the list after a short delay
      setTimeout(fetchMatches, 2000);
    } catch (err) {
      alert(`Error: ${err instanceof Error ? err.message : "Unknown error"}`);
    }
  };

  useEffect(() => {
    fetchMatches();
    // Auto‑refresh every 30 seconds
    const interval = setInterval(fetchMatches, 30000);
    return () => clearInterval(interval);
  }, []);

  // Filter matches of the current day (based on start_time date part)
  const todayMatches = matches.filter(match => {
    if (!match.start_time) return false;
    const matchDate = new Date(match.start_time).toISOString().split("T")[0];
    return matchDate === currentDate;
  });

  // Sort by start_time ascending
  todayMatches.sort((a, b) => {
    if (!a.start_time || !b.start_time) return 0;
    return new Date(a.start_time).getTime() - new Date(b.start_time).getTime();
  });

  const getStatusIcon = (status: string | null) => {
    switch (status) {
      case "SUCCESS":
        return <span className="inline-block h-4 w-4 rounded-full bg-emerald-500" title="Dati estratti e Shot Map pronta" />;
      case "PROCESSING":
        return <span className="inline-block h-4 w-4 rounded-full bg-amber-500 animate-pulse" title="Scraping in corso" />;
      case "PENDING":
        return <span className="inline-block h-4 w-4 rounded-full bg-slate-500" title="In attesa di scraping" />;
      case "RETRYING":
        return <span className="inline-block h-4 w-4 rounded-full bg-orange-500 animate-pulse" title="Tentativo di scraping in corso" />;
      case "FAILED":
        return <span className="inline-block h-4 w-4 rounded-full bg-rose-500" title="Errore di scraping" />;
      default:
        return <span className="inline-block h-4 w-4 rounded-full bg-gray-500" title="Stato sconosciuto" />;
    }
  };

  const getMatchStatusColor = (match: Match) => {
    const now = new Date();
    const start = match.start_time ? new Date(match.start_time) : null;
    const end = start ? new Date(start.getTime() + 105 * 60 * 1000) : null; // match lasts 105 minutes

    if (match.scraping_status === "SUCCESS") return "bg-emerald-900/30 border-emerald-700";
    if (match.scraping_status === "FAILED") return "bg-rose-900/30 border-rose-700";
    if (match.scraping_status === "PROCESSING" || match.scraping_status === "RETRYING")
      return "bg-amber-900/30 border-amber-700";
    if (match.status === "FT") return "bg-slate-800/30 border-slate-600";
    if (start && now >= start && end && now <= end) return "bg-blue-900/30 border-blue-700"; // match in play
    if (start && now < start) return "bg-slate-900/30 border-slate-700"; // scheduled
    return "bg-slate-900/30 border-slate-800";
  };

  const formatTime = (isoString: string | null) => {
    if (!isoString) return "—";
    const d = new Date(isoString);
    return d.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });
  };

  const formatDate = (isoString: string | null) => {
    if (!isoString) return "—";
    const d = new Date(isoString);
    return d.toLocaleDateString("it-IT");
  };

  return (
    <div className="space-y-8">
      <header className="border-b border-slate-700 pb-6">
        <h1 className="text-3xl font-bold text-white">Scraping Dashboard</h1>
        <p className="mt-2 text-slate-400">
          Monitoraggio in tempo reale dello stato di scraping delle partite della giornata odierna (
          {new Date(currentDate).toLocaleDateString("it-IT", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
          ).
        </p>
        <div className="mt-4 flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 rounded-full bg-emerald-500" />
            <span>Dati estratti</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 rounded-full bg-amber-500" />
            <span>In corso / programmato</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 rounded-full bg-rose-500" />
            <span>Errore</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 rounded-full bg-slate-500" />
            <span>In attesa</span>
          </div>
        </div>
      </header>

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-[#2a75d3] border-t-transparent" />
        </div>
      ) : error ? (
        <div className="rounded-lg bg-rose-900/30 p-6 text-rose-300">
          <p className="font-semibold">Errore nel caricamento dei match:</p>
          <p className="mt-2 font-mono text-sm">{error}</p>
          <button
            onClick={fetchMatches}
            className="mt-4 rounded bg-rose-700 px-4 py-2 text-sm font-medium text-white hover:bg-rose-600"
          >
            Riprova
          </button>
        </div>
      ) : todayMatches.length === 0 ? (
        <div className="rounded-lg bg-slate-800/50 p-8 text-center">
          <p className="text-xl text-slate-300">Nessuna partita in programma oggi.</p>
          <p className="mt-2 text-slate-500">
            Le partite di altre giornate possono essere visualizzate nella{" "}
            <a href="/admin" className="text-[#2a75d3] underline">
              lista completa
            </a>
            .
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-[#0a192f] shadow-2xl">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/80 text-slate-400">
                <th className="whitespace-nowrap px-6 py-4 text-left font-semibold">Stato</th>
                <th className="whitespace-nowrap px-6 py-4 text-left font-semibold">Match</th>
                <th className="whitespace-nowrap px-6 py-4 text-left font-semibold">Ora</th>
                <th className="whitespace-nowrap px-6 py-4 text-left font-semibold">Scraping</th>
                <th className="whitespace-nowrap px-6 py-4 text-left font-semibold">Ultimo scrape</th>
                <th className="whitespace-nowrap px-6 py-4 text-left font-semibold">Statistiche</th>
                <th className="whitespace-nowrap px-6 py-4 text-left font-semibold">Azioni</th>
              </tr>
            </thead>
            <tbody>
              {todayMatches.map((match) => (
                <tr
                  key={match.id}
                  className={`border-b border-slate-800 transition-colors hover:bg-slate-900/50 ${getMatchStatusColor(match)}`}
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(match.scraping_status)}
                      <span className="text-xs font-medium">{match.scraping_status || "N/A"}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="font-medium text-white">
                      {match.home_team} – {match.away_team}
                    </div>
                    <div className="mt-1 text-xs text-slate-400">
                      ID {match.id} • API ID {match.understat_id || "—"}
                    </div>
                    <div className="mt-1 text-xs">
                      {match.home_score !== null && match.away_score !== null ? (
                        <span className="font-bold text-white">
                          {match.home_score}‑{match.away_score}
                        </span>
                      ) : (
                        <span className="text-slate-500">Non disputata</span>
                      )}
                      {match.status && <span className="ml-2 text-slate-500">({match.status})</span>}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-white">{formatTime(match.start_time)}</div>
                    <div className="text-xs text-slate-500">{formatDate(match.start_time)}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className={`inline-block h-2 w-2 rounded-full ${match.home_shots_on_target ? "bg-emerald-500" : "bg-slate-700"}`} />
                        <span className="text-xs">
                          Tiri: {match.home_shots ?? "—"} / {match.away_shots ?? "—"}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`inline-block h-2 w-2 rounded-full ${match.home_xg ? "bg-emerald-500" : "bg-slate-700"}`} />
                        <span className="text-xs">
                          xG: {match.home_xg?.toFixed(2) ?? "—"} – {match.away_xg?.toFixed(2) ?? "—"}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {match.last_scraped_at ? (
                      <>
                        <div className="text-white">{formatTime(match.last_scraped_at)}</div>
                        <div className="text-xs text-slate-500">{formatDate(match.last_scraped_at)}</div>
                      </>
                    ) : (
                      <span className="text-slate-500">Mai</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    {match.error_log ? (
                      <div className="max-w-xs truncate rounded bg-rose-900/40 px-2 py-1 font-mono text-xs text-rose-300" title={match.error_log}>
                        {match.error_log}
                      </div>
                    ) : (
                      <span className="text-slate-500">—</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => triggerManualScrape(match.understat_id ?? match.id)}
                        disabled={!match.understat_id}
                        className="rounded bg-[#2a75d3] px-3 py-1.5 text-xs font-medium text-white hover:bg-[#1e60b0] disabled:cursor-not-allowed disabled:opacity-50"
                        title={match.understat_id ? "Forza scraping manuale" : "ID API mancante"}
                      >
                        REDRIVE
                      </button>
                      <a
                        href={`/match/${match.understat_id ?? match.id}`}
                        className="rounded border border-slate-700 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-800"
                      >
                        View
                      </a>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="rounded-lg border border-slate-800 bg-slate-900/30 p-6">
        <h2 className="mb-4 text-xl font-semibold text-white">Note operative</h2>
        <ul className="list-inside list-disc space-y-2 text-sm text-slate-400">
          <li>Le partite vengono automaticamente scansionate 5 minuti dopo il termine (status → FT).</li>
          <li>Lo stato di scraping viene aggiornato in tempo reale dallo script <code className="rounded bg-slate-800 px-1">scraper_orchestrator.py</code>.</li>
          <li>Il pulsante <strong>REDRIVE</strong> forza uno scraping immediato chiamando <code className="rounded bg-slate-800 px-1">POST /api/admin/scrape-match/{"{id}"}</code>.</li>
          <li>Le coordinate dei tiri sono normalizzate nell'intervallo 0‑100 per adattarsi al campo SVG frontend.</li>
          <li>La tabella si aggiorna automaticamente ogni 30 secondi.</li>
        </ul>
      </div>
    </div>
  );
}