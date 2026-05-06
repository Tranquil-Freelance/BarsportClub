import React from "react";
import Link from "next/link";
import { ChevronLeft, ExternalLink } from "lucide-react";
import TeamLogo from "../../../components/TeamLogo";
import MatchRosterList from "../../../components/MatchRosterList";
import { API_BASE } from "@/app/lib/apiClient";

export const revalidate = 0;

/* ─── Helpers ──────────────────────────────────────────────────────── */

function sanitize(v: unknown, fallback = 0): number {
  if (typeof v === "number" && !Number.isNaN(v)) return v;
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

function formatDate(iso: string | null): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString("it-IT", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  } catch {
    return "";
  }
}

/* ─── Types ────────────────────────────────────────────────────────── */

interface MatchHeader {
  id: number;
  date: string | null;
  league: string;
  home_id: number;
  home_team: string;
  away_id: number;
  away_team: string;
  round: number | null;
  goals: { home: number | null; away: number | null };
  xg: { home: number; away: number };
  is_completed: boolean;
  ai_verdict: string | null;
}

interface TeamComparison {
  team: string;
  avg_xG: number;
  avg_xG_conceded: number;
  avg_goals_scored: number;
  avg_goals_conceded: number;
  ppda: number;
  deep_completions: number;
}

interface PreviewResponse {
  match: MatchHeader;
  comparison: {
    home: TeamComparison;
    away: TeamComparison;
  };
}

/* ─── Article-style stat card ──────────────────────────────────────── */

function StatCard({ label, home, away }: { label: string; home: string; away: string }) {
  return (
    <div className="flex items-center justify-between py-3 px-4 even:bg-slate-50 rounded-lg">
      <span className="text-sm font-bold text-right w-[30%] text-[#FF2A6D]">{home}</span>
      <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400 w-[40%] text-center">{label}</span>
      <span className="text-sm font-bold text-left w-[30%] text-slate-800">{away}</span>
    </div>
  );
}

/* ─── Page ──────────────────────────────────────────────────────────── */

export default async function MatchPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  // Extract numeric ID (support both "slug-12345" and "12345" formats)
  const numericId = /^\d+$/.test(id) ? id : id.match(/-(\d+)$/)?.[1] || null;

  let matchData: Record<string, unknown> | null = null;
  let previewData: PreviewResponse | null = null;
  let error: string | null = null;

  if (!numericId) {
    error = "ID partita non valido.";
  }

  if (!error) {
    try {
      const [matchRes, previewRes] = await Promise.all([
        fetch(`${API_BASE}/api/match/${numericId}`, {
          next: { revalidate: 30 },
        }),
        fetch(`${API_BASE}/api/v1/matches/${numericId}/preview`, {
          next: { revalidate: 30 },
        }),
      ]);

      if (!matchRes.ok) {
        if (matchRes.status === 404) error = "Match non trovato nel database.";
        else throw new Error(`Match API HTTP ${matchRes.status}`);
      } else {
        matchData = await matchRes.json();
      }

      if (previewRes.ok) {
        previewData = await previewRes.json();
      }
    } catch (err) {
      console.error("Fetch error:", err);
      error = "Errore di connessione al backend.";
    }
  }

  const raw = matchData || {};
  const match = {
    home: (raw as any).home ?? (raw as any).home_team ?? (raw as any).homeTeam ?? previewData?.match?.home_team ?? "",
    away: (raw as any).away ?? (raw as any).away_team ?? (raw as any).awayTeam ?? previewData?.match?.away_team ?? "",
    scoreH: sanitize((raw as any).home_score ?? (raw as any).goals?.h ?? (raw as any).goals_h ?? (raw as any).homeScore),
    scoreA: sanitize((raw as any).away_score ?? (raw as any).goals?.a ?? (raw as any).goals_a ?? (raw as any).awayScore),
    xgH: sanitize((raw as any).home_xg ?? (raw as any).xg?.h ?? (raw as any).home_xG),
    xgA: sanitize((raw as any).away_xg ?? (raw as any).xg?.a ?? (raw as any).away_xG),
    league: (raw as any).league ?? "",
    date: formatDate((raw as any).start_time ?? (raw as any).date ?? (raw as any).match_datetime),
    status: (raw as any).status,
    round: (raw as any).round ?? null,
  };

  const pHome = previewData?.comparison?.home;
  const pAway = previewData?.comparison?.away;
  const aiVerdict = previewData?.match?.ai_verdict ?? null;

  const isFuture = match.status && !["FT", "PEN"].includes(match.status);
  const isCompleted = previewData?.match?.is_completed ?? false;

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#1E293B] font-sans">

      {/* ── Minimal top bar ── */}
      <div className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center gap-3 text-sm">
          <Link href="/" className="text-slate-400 hover:text-[#FF2A6D] transition-colors font-medium">
            Home
          </Link>
          <span className="text-slate-200">/</span>
          <Link href="/prossimo-turno" className="text-slate-400 hover:text-[#FF2A6D] transition-colors font-medium">
            Prossimo Turno
          </Link>
          <span className="text-slate-200">/</span>
          <span className="text-slate-800 font-bold truncate">
            {match.home}{match.home && match.away ? " – " : ""}{match.away}
          </span>
        </div>
      </div>

      {/* ── Article header ── */}
      <header className="max-w-5xl mx-auto px-6 pt-12 pb-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6 mb-8">
          <div>
            {/* Category tag */}
            <div className="flex items-center gap-3 mb-4">
              <span className="bg-[#FF2A6D]/10 text-[#FF2A6D] text-[10px] font-black uppercase tracking-widest px-3 py-1.5 rounded-full">
                {match.league}
              </span>
              {match.round && (
                <span className="bg-slate-100 text-slate-500 text-[10px] font-black uppercase tracking-widest px-3 py-1.5 rounded-full">
                  Giornata {match.round}
                </span>
              )}
            </div>

            <h1 className="text-4xl md:text-5xl lg:text-6xl font-black italic tracking-tighter text-[#0a192f] leading-tight">
              {match.home}
              <span className="text-slate-300 mx-3 font-normal not-italic">–</span>
              {match.away}
            </h1>
          </div>
        </div>

        {/* Scoreboard — teams + logos + clean VS center */}
        <div className="bg-white rounded-3xl border border-slate-200 shadow-lg overflow-hidden">
          <div className="p-8 md:p-10 flex items-center justify-between">
            <div className="flex flex-col items-center text-center w-[30%]">
              {match.home && (
                <>
                  <TeamLogo teamName={match.home} size={64} />
                  <span className="text-lg md:text-xl font-black uppercase text-[#0a192f] tracking-tighter mt-3">
                    {match.home}
                  </span>
                </>
              )}
              {(match.scoreH > 0 || match.scoreA > 0) && (
                <span className="text-5xl md:text-6xl font-black text-[#FF2A6D] mt-2">{match.scoreH}</span>
              )}
            </div>

            <div className="flex flex-col items-center w-[40%]">
              {/* Clean bold VS */}
              <span className="text-3xl md:text-4xl font-black italic text-slate-300 tracking-tighter">VS</span>
              {(match.scoreH > 0 || match.scoreA > 0) ? (
                <span className="text-[10px] font-black uppercase tracking-widest text-slate-400 mt-3">
                  Risultato Finale
                </span>
              ) : (
                <span className="text-[10px] font-black uppercase tracking-widest text-slate-400 mt-3">
                  In programma
                </span>
              )}
              {isCompleted && (
                <div className="flex items-center gap-2 mt-3">
                  <span className="text-xs font-bold text-slate-400">xG</span>
                  <span className="text-lg font-black text-[#FF2A6D]">{match.xgH.toFixed(2)}</span>
                  <span className="text-slate-200">–</span>
                  <span className="text-lg font-black text-slate-700">{match.xgA.toFixed(2)}</span>
                </div>
              )}
            </div>

            <div className="flex flex-col items-center text-center w-[30%]">
              {match.away && (
                <>
                  <TeamLogo teamName={match.away} size={64} />
                  <span className="text-lg md:text-xl font-black uppercase text-[#0a192f] tracking-tighter mt-3">
                    {match.away}
                  </span>
                </>
              )}
              {(match.scoreH > 0 || match.scoreA > 0) && (
                <span className="text-5xl md:text-6xl font-black text-slate-700 mt-2">{match.scoreA}</span>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* ── Main article body ── */}
      <main className="max-w-5xl mx-auto px-6 pb-20">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">

          {/* ── LEFT / CENTER: Editorial content ── */}
          <article className="lg:col-span-2 space-y-10">

            {error && (
              <div className="bg-rose-50 border border-rose-200 rounded-2xl p-6 text-rose-700">
                <p className="font-bold mb-1">Attenzione</p>
                <p className="text-sm">{error}</p>
              </div>
            )}

            {isFuture && !aiVerdict && (
              <div className="bg-amber-50 border border-amber-200 rounded-2xl p-8 text-center">
                <h3 className="text-xl font-black text-amber-700 mb-2">Partita in programma</h3>
                <p className="text-amber-600 text-sm">
                  Questa partita è in programma per il {match.date}. L&rsquo;analisi tattica verrà pubblicata dopo il fischio finale.
                </p>
              </div>
            )}

            {/* ── Stats comparison — editorial style ── */}
            {pHome && pAway && (
              <section className="bg-white rounded-3xl border border-slate-200 shadow-lg overflow-hidden">
                <div className="border-b border-slate-100 p-8 pb-6">
                  <h3 className="text-xl font-black italic tracking-tighter text-[#0a192f]">
                    Confronto Statistico
                  </h3>
                  <p className="text-sm text-slate-400 mt-2 font-medium">
                    Media delle ultime 5 partite
                  </p>
                </div>
                <div className="p-6">
                  <div className="flex items-center justify-between px-4 pb-3 border-b border-slate-100 mb-2">
                    <span className="text-xs font-black uppercase tracking-widest text-[#FF2A6D] w-[30%] text-right">{pHome.team}</span>
                    <span className="text-[9px] font-black uppercase tracking-widest text-slate-300 w-[40%] text-center">Stat</span>
                    <span className="text-xs font-black uppercase tracking-widest text-slate-600 w-[30%]">{pAway.team}</span>
                  </div>
                  <StatCard label="xG Medi" home={pHome.avg_xG.toFixed(3)} away={pAway.avg_xG.toFixed(3)} />
                  <StatCard label="xG Subiti" home={pHome.avg_xG_conceded.toFixed(3)} away={pAway.avg_xG_conceded.toFixed(3)} />
                  <StatCard label="Gol Fatti" home={pHome.avg_goals_scored.toFixed(1)} away={pAway.avg_goals_scored.toFixed(1)} />
                  <StatCard label="Gol Subiti" home={pHome.avg_goals_conceded.toFixed(1)} away={pAway.avg_goals_conceded.toFixed(1)} />
                  <StatCard label="PPDA" home={pHome.ppda.toFixed(1)} away={pAway.ppda.toFixed(1)} />
                  <StatCard label="Deep Comp." home={String(pHome.deep_completions)} away={String(pAway.deep_completions)} />
                </div>
              </section>
            )}

            {/* ── AI VERDICT — Editorial article (BELOW Confronto Statistico) ── */}
            <section className="bg-white rounded-3xl border border-slate-200 shadow-lg overflow-hidden">
              {/* Article header */}
              <div className="border-b border-slate-100 p-8 pb-6">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-2 h-2 rounded-full bg-[#FF2A6D]"></div>
                  <span className="text-[10px] font-black uppercase tracking-widest text-[#FF2A6D]">
                    Preview
                  </span>
                </div>
                <h2 className="text-2xl md:text-3xl font-black italic tracking-tighter text-[#0a192f]">
                  Analisi Tattica Pre-Match
                </h2>
                <p className="text-sm text-slate-400 mt-3 font-medium">
                  Un&rsquo;analisi basata sui dati raccolti dal nostro algoritmo, che confronta le statistiche
                  delle ultime uscite per delineare scenari e tendenze.
                </p>
              </div>

              {/* Article body — editorial blog styling */}
              <div className="p-8 md:p-10">
                <div className="prose prose-lg max-w-none
                  prose-headings:text-[#0a192f] prose-headings:font-black prose-headings:italic prose-headings:tracking-tighter
                  prose-p:text-slate-700 prose-p:leading-[1.8] prose-p:text-base md:prose-p:text-lg
                  prose-strong:text-[#0a192f] prose-strong:font-black
                  prose-em:text-[#FF2A6D] prose-em:not-italic prose-em:font-bold
                  prose-li:text-slate-700
                  prose-blockquote:border-[#FF2A6D] prose-blockquote:bg-slate-50 prose-blockquote:py-4 prose-blockquote:px-6 prose-blockquote:rounded-xl prose-blockquote:not-italic prose-blockquote:text-slate-600
                  prose-hr:border-slate-200
                ">
                  <p className="lead text-xl md:text-2xl font-bold text-slate-600 leading-relaxed mb-8">
                    {match.home} vs {match.away} — {match.league}
                  </p>
                  {aiVerdict ? (
                    <div className="whitespace-pre-line text-slate-700 leading-[1.8] text-base md:text-lg">
                      {aiVerdict}
                    </div>
                  ) : (
                    <div className="text-slate-400 italic text-base md:text-lg leading-relaxed bg-slate-50 rounded-2xl p-8 text-center border border-slate-100">
                      Analisi AI non ancora generata o in attesa di calcolo.
                    </div>
                  )}
                </div>
              </div>

              {/* Article footer */}
              <div className="border-t border-slate-100 p-8 bg-slate-50/50">
                <div className="flex items-center gap-3 text-xs text-slate-400">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#FF2A6D]"></div>
                  <span className="font-bold uppercase tracking-wider">Analisi generata da barsport.club Algorithm</span>
                </div>
              </div>
            </section>

            {/* ── FORMAZIONI — Data-driven roster list (replaces visual pitch) ── */}
            {!isFuture && (
              <section>
                <MatchRosterList matchId={numericId!} />
              </section>
            )}

          </article>

          {/* ── RIGHT: Sidebar widget ── */}
          <aside className="space-y-6">
            {/* Match info card — only Competizione + Probabili Formazioni */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="bg-[#0a192f] p-5">
                <h4 className="text-xs font-black uppercase tracking-widest text-white">Dettagli Partita</h4>
              </div>
              <div className="p-5 space-y-5 text-sm">
                {/* Only Competizione (League) */}
                <div>
                  <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">Competizione</span>
                  <p className="font-bold text-slate-800 mt-1">{match.league}</p>
                </div>
                {match.round && (
                  <div>
                    <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">Giornata</span>
                    <p className="font-bold text-slate-800 mt-1">{match.round}</p>
                  </div>
                )}

                {/* 🔍 Probabili Formazioni smart link — blue button style */}
                {match.home && match.away && (
                  <a
                    href={`https://www.google.com/search?q=probabili+formazioni+${encodeURIComponent(match.home)}+${encodeURIComponent(match.away)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center gap-2 w-full border border-slate-300 text-slate-700 text-sm font-semibold py-2 rounded-lg hover:bg-slate-50 hover:border-slate-400 transition-all"
                  >
                    <ExternalLink size={14} />
                    Probabili Formazioni
                  </a>
                )}
              </div>
            </div>

            {/* Navigation */}
            <Link
              href="/prossimo-turno"
              className="flex items-center justify-center gap-2 w-full bg-white border border-slate-200 rounded-2xl px-5 py-4 text-sm font-bold text-slate-600 hover:text-[#FF2A6D] hover:border-[#FF2A6D]/30 transition-all shadow-sm hover:shadow-md"
            >
              <ChevronLeft size={16} />
              Torna al Prossimo Turno
            </Link>
          </aside>
        </div>
      </main>
    </div>
  );
}
