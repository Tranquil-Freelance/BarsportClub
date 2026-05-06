"use client";

import { useState, useEffect } from "react";
import { Activity, RefreshCw, CalendarSync, PlayCircle, AlertCircle, Terminal } from "lucide-react";
import { triggerCalendarSync, triggerLiveScraper } from "../../services/adminService";

export default function ScraperPanel() {
  // Sync calendars state
  const [syncLoading, setSyncLoading] = useState(false);
  const [league, setLeague] = useState("Serie A");
  const [season, setSeason] = useState("2025");
  const [lastSync, setLastSync] = useState<string | null>("2025-02-19 11:45");

  // Live scraper state
  const [scraperLoading, setScraperLoading] = useState(false);
  const [matchId, setMatchId] = useState<string>("");
  const [scraperStatus, setScraperStatus] = useState<"idle" | "running" | "error">("idle");
  const [lastScrape, setLastScrape] = useState<string | null>("2025-02-19 12:15");

  // System logs
  const [logs, setLogs] = useState<{ message: string; timestamp: string }[]>([
    { message: "[INFO] Calendar sync completed for Serie A 2025", timestamp: "12:00" },
    { message: "[INFO] Live scraper started – fetching match events", timestamp: "12:01" },
    { message: "[WARN] External API rate limit near threshold", timestamp: "12:02" },
    { message: "[INFO] Upserting 15 matches for Serie A...", timestamp: "12:03" },
    { message: "[INFO] Fetching Serie A data for season 2025", timestamp: "12:04" },
  ]);

  // Simulate real-time status updates
  useEffect(() => {
    if (scraperLoading) {
      const interval = setInterval(() => {
        setLogs(prev => [
          {
            message: `[INFO] Scraping in progress... ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
          },
          ...prev.slice(0, 9),
        ]);
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [scraperLoading]);

  const handleSyncCalendars = async () => {
    setSyncLoading(true);
    setLogs(prev => [
      {
        message: `[INFO] Syncing calendars for ${league} ${season}...`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      },
      ...prev
    ]);

    try {
      const response = await triggerCalendarSync(league, season);
      const now = new Date().toISOString().slice(0, 16).replace("T", " ");
      setLastSync(now);
      setLogs(prev => [
        {
          message: `[SUCCESS] ${response.message}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        },
        ...prev.slice(0, 9),
      ]);
    } catch (err) {
      console.error("Calendar sync failed:", err);
      setLogs(prev => [
        {
          message: `[ERROR] Calendar sync failed: ${err instanceof Error ? err.message : 'Unknown error'}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        },
        ...prev.slice(0, 9),
      ]);
    } finally {
      setSyncLoading(false);
    }
  };

  const handleTriggerScraper = async (matchId: number) => {
    setScraperLoading(true);
    setScraperStatus("running");
    setLogs(prev => [
      {
        message: `[INFO] Live scraper triggered for match ${matchId}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      },
      ...prev
    ]);

    try {
      // Inseriamo l'URL assoluto maniacale che punta dritto al tuo backend funzionante
      const response = await fetch(`http://localhost:8000/api/admin/scrape-match/${matchId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Errore API ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      console.log("Dati scaricati:", data);
      
      const now = new Date().toISOString().slice(0, 16).replace("T", " ");
      setLastScrape(now);
      setLogs(prev => [
        {
          message: `[SUCCESS] Scraping completato con successo! Tiri estratti: ${data.shots_total}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        },
        ...prev.slice(0, 9),
      ]);
      setScraperStatus("idle");
      
      alert(`Scraping completato con successo! Tiri estratti: ${data.shots_total}`);
      // Ricarica la pagina per mostrare i nuovi dati
      window.location.reload();
      
    } catch (error: any) {
      console.error("Errore durante lo scraping:", error);
      setScraperStatus("error");
      setLogs(prev => [
        {
          message: `[ERROR] Live scraper failed: ${error.message}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        },
        ...prev.slice(0, 9),
      ]);
      alert(`Errore nello scraping: ${error.message}`);
    } finally {
      setScraperLoading(false);
    }
  };

  const handleScrapeLatestRound = async () => {
    setScraperLoading(true);
    setScraperStatus("running");
    setLogs(prev => [
      {
        message: `[INFO] Scraping latest round for ${league} ${season}...`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      },
      ...prev
    ]);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 seconds

      const response = await fetch(`http://localhost:8000/api/v1/scraper/scrape-latest-round`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ league, season }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API error ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      console.log("Latest round scraping started:", data);
      
      const now = new Date().toISOString().slice(0, 16).replace("T", " ");
      setLastScrape(now);
      setLogs(prev => [
        {
          message: `[SUCCESS] ${data.message}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        },
        ...prev.slice(0, 9),
      ]);
      setScraperStatus("idle");
      
      alert(`Scraping latest round started: ${data.message}`);
      
    } catch (error: any) {
      console.error("Error during latest round scraping:", error);
      setScraperStatus("error");
      setLogs(prev => [
        {
          message: `[ERROR] Latest round scraping failed: ${error.message}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        },
        ...prev.slice(0, 9),
      ]);
      alert(`Error: ${error.message}`);
    } finally {
      setScraperLoading(false);
    }
  };

  const clearLogs = () => setLogs([]);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
          <Activity className="h-6 w-6 text-cyan-400" />
          Scraper Control Center
        </h2>
        <p className="mt-2 text-slate-400">
          Manually trigger data extraction pipelines and monitor real‑time status.
        </p>
      </div>

      {/* Two‑column layout for actions */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        {/* Sync Calendars Card */}
        <div className="rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 to-slate-950 p-8 shadow-2xl">
          <div className="flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-cyan-500 shadow-lg">
              <CalendarSync className="h-8 w-8 text-white" />
            </div>
            <div>
              <h3 className="text-2xl font-bold text-white">Sync Calendars</h3>
              <p className="mt-1 text-slate-400">
                Pull match schedules from external source for selected league and season.
              </p>
            </div>
          </div>

          {/* League/Season inputs */}
          <div className="mt-8 grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">
                League
              </label>
              <select
                value={league}
                onChange={(e) => setLeague(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-white focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
                suppressHydrationWarning
              >
                <option value="Serie A">Serie A</option>
                <option value="Premier League">Premier League</option>
                <option value="La Liga">La Liga</option>
                <option value="Bundesliga">Bundesliga</option>
                <option value="Ligue 1">Ligue 1</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">
                Season
              </label>
              <select
                value={season}
                onChange={(e) => setSeason(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-white focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
                suppressHydrationWarning
              >
                <option value="2025">2025</option>
                <option value="2024">2024</option>
                <option value="2023">2023</option>
                <option value="2022">2022</option>
              </select>
            </div>
          </div>

          <button
            onClick={handleSyncCalendars}
            disabled={syncLoading}
            className="mt-8 w-full rounded-lg bg-gradient-to-r from-blue-600 to-cyan-600 py-3.5 text-lg font-semibold text-white shadow-lg hover:from-blue-500 hover:to-cyan-500 disabled:opacity-70 disabled:cursor-not-allowed transition-all duration-300"
          >
            {syncLoading ? (
              <span className="flex items-center justify-center gap-2">
                <RefreshCw className="h-5 w-5 animate-spin" />
                Syncing...
              </span>
            ) : (
              <span className="flex items-center justify-center gap-2">
                <CalendarSync className="h-5 w-5" />
                Sync Calendars Now
              </span>
            )}
          </button>

          <div className="mt-6 flex items-center justify-between text-sm">
            <span className="text-slate-500">Last sync:</span>
            <span className="font-mono text-slate-300">{lastSync || "Never"}</span>
          </div>
        </div>

        {/* Trigger Live Scraper Card */}
        <div className="rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 to-slate-950 p-8 shadow-2xl">
          <div className="flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-600 to-green-500 shadow-lg">
              <PlayCircle className="h-8 w-8 text-white" />
            </div>
            <div>
              <h3 className="text-2xl font-bold text-white">Trigger Live Scraper</h3>
              <p className="mt-1 text-slate-400">
                Start a real‑time scraping session for ongoing matches and player stats.
              </p>
            </div>
          </div>

          {/* Real‑time status indicator */}
          <div className="mt-8 flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/50 px-5 py-4">
            <div className="flex items-center gap-3">
              <div
                className={`h-3 w-3 rounded-full ${scraperStatus === "running" ? "animate-pulse bg-emerald-500" : scraperStatus === "error" ? "bg-rose-500" : "bg-slate-500"}`}
              />
              <span className="font-medium text-slate-300">
                {scraperStatus === "running" ? "Live scraper is running" : scraperStatus === "error" ? "Error encountered" : "Scraper is idle"}
              </span>
            </div>
            <div className="text-sm text-slate-500">
              {scraperStatus === "running" ? "Real‑time updates active" : "Ready to start"}
            </div>
          </div>


          <button
            onClick={handleScrapeLatestRound}
            disabled={scraperLoading}
            className="mt-8 w-full rounded-lg bg-gradient-to-r from-emerald-600 to-green-600 py-3.5 text-lg font-semibold text-white shadow-lg hover:from-emerald-500 hover:to-green-500 disabled:opacity-70 disabled:cursor-not-allowed transition-all duration-300"
          >
            {scraperLoading ? (
              <span className="flex items-center justify-center gap-2">
                <RefreshCw className="h-5 w-5 animate-spin" />
                Scraping...
              </span>
            ) : (
              <span className="flex items-center justify-center gap-2">
                <PlayCircle className="h-5 w-5" />
                Scrape Ultima Giornata (Auto)
              </span>
            )}
          </button>

          <div className="mt-6 flex items-center justify-between text-sm">
            <span className="text-slate-500">Last scrape:</span>
            <span className="font-mono text-slate-300">{lastScrape || "Never"}</span>
          </div>
        </div>
      </div>

      {/* System Logs */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-8">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold text-white flex items-center gap-3">
              <Terminal className="h-5 w-5 text-amber-400" />
              System Logs
            </h3>
            <p className="mt-1 text-slate-400">Live terminal output from scraping pipelines.</p>
          </div>
          <button
            onClick={clearLogs}
            className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
          >
            Clear logs
          </button>
        </div>

        {/* Scrollable logs window */}
        <div className="mt-6 max-h-80 overflow-y-auto rounded-xl border border-slate-800 bg-slate-950 p-4 font-mono text-sm">
          {logs.length === 0 ? (
            <div className="py-8 text-center text-slate-500">No logs yet. Trigger an action to see output.</div>
          ) : (
            logs.map((log, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 border-b border-slate-800 py-3 last:border-b-0"
              >
                <div className="mt-1.5 h-2 w-2 flex-shrink-0 rounded-full bg-emerald-500" />
                <span className="text-slate-300 whitespace-pre-wrap">{log.message}</span>
                <span className="ml-auto flex-shrink-0 text-xs text-slate-500">
                  {log.timestamp}
                </span>
              </div>
            ))
          )}
        </div>
        <div className="mt-4 text-xs text-slate-500 flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-emerald-500" />
          <span>Live updates every 3 seconds when scraper is active.</span>
        </div>
      </div>

      {/* Warning */}
      <div className="rounded-xl border border-amber-800/50 bg-amber-900/20 p-6">
        <div className="flex items-start gap-4">
          <AlertCircle className="h-6 w-6 text-amber-400 mt-0.5" />
          <div>
            <h4 className="font-bold text-amber-300">Heads up</h4>
            <p className="mt-1 text-sm text-amber-200/80">
              Triggering the live scraper while a previous session is still running may cause duplicate entries. Ensure the queue is empty before proceeding.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}