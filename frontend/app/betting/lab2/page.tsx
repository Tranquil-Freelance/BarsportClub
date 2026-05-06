"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import Link from "next/link";
import { get } from "../../lib/apiClient";
import { usePathname } from "next/navigation";

// ═══════════════════════════════════════════════════════════════
//  TYPES
// ═══════════════════════════════════════════════════════════════

interface AvailableMatch {
  match_id: number;
  label: string;
}

interface LeagueMatches {
  league_name: string;
  matches: AvailableMatch[];
}

interface AhComponent {
  line: number;
  P_win: number;
  P_push: number;
  P_loss: number;
}

interface AsianHandicapBreakdown {
  line: number;
  full_win_component: AhComponent;
  half_component: AhComponent;
  combined_ev: number;
}

interface Lab2MatrixResponse {
  home_team: string;
  away_team: string;
  lambda_home: number;
  lambda_away: number;
  score_matrix: number[][];
  asian_handicap_breakdown: AsianHandicapBreakdown;
}

// ═══════════════════════════════════════════════════════════════
//  THEME CONSTANTS (same dark palette as Lab 1)
// ═══════════════════════════════════════════════════════════════

const C = {
  bg: "#0d1117",
  surface: "#161b22",
  surface2: "#1c2333",
  border: "#30363d",
  borderLight: "#21262d",
  text: "#e6edf3",
  textMuted: "#8b949e",
  accent: "#58a6ff",
  green: "#3fb950",
  red: "#f85149",
  gold: "#d29922",
};

// ═══════════════════════════════════════════════════════════════
//  NAVIGATION BAR
// ═══════════════════════════════════════════════════════════════

function LabNavBar() {
  const pathname = usePathname();

  const btn = (href: string, label: string, isActive: boolean) => (
    <Link
      href={href}
      className={`border px-4 py-2 text-xs font-mono transition-all ${
        isActive
          ? "border-gray-500 bg-gray-800 text-white"
          : "border-gray-700 bg-black text-gray-300 hover:bg-gray-800 hover:text-white"
      }`}
      style={{ textDecoration: "none", letterSpacing: "0.5px" }}
    >
      {label}
    </Link>
  );

  return (
    <div
      style={{
        display: "flex",
        gap: 8,
        alignItems: "center",
        padding: "8px 0",
        marginBottom: 16,
        borderBottom: `1px solid ${C.border}`,
        flexWrap: "wrap",
      }}
    >
      {btn("/betting", "← BACK TO BETTING HOME", pathname === "/betting")}
      {btn("/betting/lab1", "GO TO LAB 1: ANALYTICS", pathname === "/betting/lab1")}
      {btn("/betting/lab2", "GO TO LAB 2: THE MATRIX", pathname === "/betting/lab2")}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
//  HELPERS
// ═══════════════════════════════════════════════════════════════

function pct(val: number): string {
  return (val * 100).toFixed(2) + "%";
}

/** Heatmap colour: blend from #0d1117 (0 %) → #3fb950 (peak) */
function heatColor(prob: number, maxProb: number): string {
  if (maxProb <= 0) return C.bg;
  const intensity = prob / maxProb;
  const r = Math.round(13 + intensity * (63 - 13));
  const g = Math.round(17 + intensity * (185 - 17));
  const b = Math.round(23 + intensity * (80 - 23));
  return `rgb(${r},${g},${b})`;
}

function labelForLine(line: number): string {
  if (line === -0.5) return "Full Win (-0.5)";
  if (line === -1.0) return "Half / Push (-1.0)";
  return `${line > 0 ? "+" : ""}${line}`;
}

function labelForOutcome(key: string): string {
  switch (key) {
    case "P_win":  return "Win";
    case "P_push": return "Push";
    case "P_loss": return "Loss";
    default:       return key;
  }
}

function outcomeColor(key: string): string {
  switch (key) {
    case "P_win":  return C.green;
    case "P_push": return C.gold;
    case "P_loss": return C.red;
    default:       return C.text;
  }
}

// ═══════════════════════════════════════════════════════════════
//  COMPONENT
// ═══════════════════════════════════════════════════════════════

export default function Lab2MatrixPage() {
  const [matchId, setMatchId] = useState<number | null>(null);
  const [data, setData] = useState<Lab2MatrixResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ── Dropdown state ──────────────────────────────────────────
  const [leagues, setLeagues] = useState<LeagueMatches[]>([]);
  const [dropdownLoading, setDropdownLoading] = useState(true);
  const [dropdownError, setDropdownError] = useState<string | null>(null);
  const [selectedLeague, setSelectedLeague] = useState<string>("");
  const [selectedMatchId, setSelectedMatchId] = useState<number | "">("");

  // Derived: matches for the currently selected league
  const currentMatches = useMemo(() => {
    const league = leagues.find((l) => l.league_name === selectedLeague);
    return league ? league.matches : [];
  }, [leagues, selectedLeague]);

  // ── Fetch available matches on mount ──────────────────────
  useEffect(() => {
    (async () => {
      try {
        setDropdownLoading(true);
        setDropdownError(null);
        const res = await get<LeagueMatches[]>("/betting/available-matches");
        setLeagues(res);
        if (res.length > 0) {
          setSelectedLeague(res[0].league_name);
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Failed to fetch matches";
        setDropdownError(msg);
      } finally {
        setDropdownLoading(false);
      }
    })();
  }, []);

  // Reset match selection when league changes
  useEffect(() => {
    setSelectedMatchId("");
  }, [selectedLeague]);

  // ── Fetch matrix ────────────────────────────────────────────
  const fetchMatrix = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await get<Lab2MatrixResponse>(
        `/betting/lab2-matrix?match_id=${encodeURIComponent(id)}`
      );
      setData(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load matrix");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedMatchId === "") return;
    const id = selectedMatchId as number;
    setMatchId(id);
    fetchMatrix(id);
  };

  // ── URL query param auto-load (preserved from original) ─────
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const q = params.get("match_id");
    if (q) {
      const parsed = parseInt(q, 10);
      if (!isNaN(parsed)) {
        setMatchId(parsed);
        fetchMatrix(parsed);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Heatmap max for colour scaling ──────────────────────────
  const maxProb: number = data
    ? Math.max(...data.score_matrix.flat())
    : 0;

  // ── Shared dropdown style ───────────────────────────────────
  const dropdownStyle: React.CSSProperties = {
    background: C.surface,
    border: `1px solid ${C.border}`,
    borderRadius: 6,
    padding: "8px 12px",
    color: C.text,
    fontSize: 13,
    outline: "none",
    fontFamily: "'Courier New', monospace",
  };

  return (
    <main
      style={{
        maxWidth: 1200,
        margin: "0 auto",
        padding: "24px 16px",
        background: C.bg,
        minHeight: "100vh",
        color: C.text,
        fontFamily: "'Inter','Segoe UI',system-ui,sans-serif",
      }}
    >
      {/* ── LAB NAV ──────────────────────────────────────────── */}
      <LabNavBar />

      {/* ── Header ──────────────────────────────────────────── */}
      <h1
        style={{
          fontSize: 22,
          fontWeight: 700,
          letterSpacing: "0.02em",
          marginBottom: 4,
          color: C.text,
        }}
      >
        ⚡ LAB 2: POISSON MATRIX
      </h1>
      <p style={{ fontSize: 13, color: C.textMuted, marginBottom: 20 }}>
        Single-match Poisson λ → Score Matrix → Asian Handicap breakdown
      </p>

      {/* ── Two‑tier dropdown selector ───────────────────────── */}
      <form
        onSubmit={handleSubmit}
        style={{
          display: "flex",
          gap: 10,
          marginBottom: 24,
          alignItems: "center",
          flexWrap: "wrap",
        }}
      >
        {/* League selector */}
        <label style={{ fontSize: 12, color: C.textMuted, fontWeight: 600 }}>
          League:
        </label>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <select
            value={selectedLeague}
            onChange={(e) => setSelectedLeague(e.target.value)}
            disabled={dropdownLoading}
            style={{ ...dropdownStyle, minWidth: 120 }}
          >
            {dropdownLoading && <option value="">loading…</option>}
            {!dropdownLoading && leagues.length === 0 && !dropdownError && (
              <option value="">No leagues available</option>
            )}
            {leagues.map((l) => (
              <option key={l.league_name} value={l.league_name}>
                {l.league_name}
              </option>
            ))}
          </select>
          {dropdownLoading && (
            <span style={{ fontSize: 11, color: C.textMuted }}>Loading matches...</span>
          )}
          {dropdownError && (
            <span style={{ fontSize: 11, color: C.red }}>
              Error loading matches. Is the backend running?
            </span>
          )}
        </div>

        {/* Match selector */}
        <label style={{ fontSize: 12, color: C.textMuted, fontWeight: 600 }}>
          Match:
        </label>
        <select
          value={selectedMatchId}
          onChange={(e) =>
            setSelectedMatchId(
              e.target.value === "" ? "" : parseInt(e.target.value, 10)
            )
          }
          disabled={currentMatches.length === 0}
          style={{ ...dropdownStyle, minWidth: 220 }}
        >
          <option value="">— Select a match —</option>
          {currentMatches.length === 0 && (
            <option value="" disabled>No matches available</option>
          )}
          {currentMatches.map((m) => (
            <option key={m.match_id} value={m.match_id}>
              {m.label}
            </option>
          ))}
        </select>

        <button
          type="submit"
          disabled={selectedMatchId === ""}
          style={{
            background: selectedMatchId !== "" ? C.accent : C.border,
            color: selectedMatchId !== "" ? "#fff" : C.textMuted,
            border: "none",
            borderRadius: 6,
            padding: "8px 16px",
            fontSize: 13,
            fontWeight: 600,
            cursor: selectedMatchId !== "" ? "pointer" : "default",
          }}
        >
          {selectedMatchId !== "" ? "Load" : "Load"}
        </button>

        {/* Show selected match_id in muted text */}
        {matchId && data && (
          <span style={{ fontSize: 11, color: C.textMuted }}>
            (match_id: {matchId})
          </span>
        )}
      </form>

      {/* ── Loading / Error ─────────────────────────────────── */}
      {loading && (
        <p style={{ color: C.textMuted, fontSize: 14 }}>
          Loading matrix…
        </p>
      )}
      {error && (
        <p style={{ color: C.red, fontSize: 14 }}>
          {error}
        </p>
      )}

      {/* ── Data ────────────────────────────────────────────── */}
      {data && (
        <>
          {/* ════════════════════════════════════════════════════
              SECTION A — λ Display
              ════════════════════════════════════════════════════ */}
          <section
            style={{
              background: C.surface,
              border: `1px solid ${C.border}`,
              borderRadius: 10,
              padding: "20px 24px",
              marginBottom: 20,
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: 16,
              }}
            >
              {/* Home */}
              <div style={{ textAlign: "center", flex: 1 }}>
                <div
                  style={{
                    fontSize: 13,
                    fontWeight: 600,
                    color: C.textMuted,
                    textTransform: "uppercase",
                    letterSpacing: "0.06em",
                    marginBottom: 4,
                  }}
                >
                  HOME
                </div>
                <div
                  style={{
                    fontSize: 28,
                    fontWeight: 800,
                    color: C.text,
                    lineHeight: 1.2,
                  }}
                >
                  {data.home_team}
                </div>
                <div
                  style={{
                    marginTop: 8,
                    background: C.surface2,
                    borderRadius: 8,
                    padding: "8px 16px",
                    display: "inline-block",
                  }}
                >
                  <span style={{ fontSize: 11, color: C.textMuted }}>
                    λ =
                  </span>{" "}
                  <span
                    style={{
                      fontSize: 26,
                      fontWeight: 700,
                      color: C.accent,
                    }}
                  >
                    {data.lambda_home.toFixed(3)}
                  </span>
                </div>
              </div>

              {/* VS */}
              <div
                style={{
                  fontSize: 18,
                  fontWeight: 700,
                  color: C.textMuted,
                }}
              >
                VS
              </div>

              {/* Away */}
              <div style={{ textAlign: "center", flex: 1 }}>
                <div
                  style={{
                    fontSize: 13,
                    fontWeight: 600,
                    color: C.textMuted,
                    textTransform: "uppercase",
                    letterSpacing: "0.06em",
                    marginBottom: 4,
                  }}
                >
                  AWAY
                </div>
                <div
                  style={{
                    fontSize: 28,
                    fontWeight: 800,
                    color: C.text,
                    lineHeight: 1.2,
                  }}
                >
                  {data.away_team}
                </div>
                <div
                  style={{
                    marginTop: 8,
                    background: C.surface2,
                    borderRadius: 8,
                    padding: "8px 16px",
                    display: "inline-block",
                  }}
                >
                  <span style={{ fontSize: 11, color: C.textMuted }}>
                    λ =
                  </span>{" "}
                  <span
                    style={{
                      fontSize: 26,
                      fontWeight: 700,
                      color: C.accent,
                    }}
                  >
                    {data.lambda_away.toFixed(3)}
                  </span>
                </div>
              </div>
            </div>
          </section>

          {/* ════════════════════════════════════════════════════
              SECTION B — 6×6 Score Matrix Heatmap
              ════════════════════════════════════════════════════ */}
          <section
            style={{
              background: C.surface,
              border: `1px solid ${C.border}`,
              borderRadius: 10,
              padding: "20px 24px",
              marginBottom: 20,
              overflowX: "auto",
            }}
          >
            <h2
              style={{
                fontSize: 15,
                fontWeight: 700,
                color: C.text,
                marginBottom: 12,
                letterSpacing: "0.02em",
              }}
            >
              📊 Score Matrix — Joint Probability (Poisson)
            </h2>

            <table
              style={{
                borderCollapse: "collapse",
                fontSize: 12,
                width: "100%",
                minWidth: 400,
              }}
            >
              <thead>
                <tr>
                  <th
                    style={{
                      padding: "6px 8px",
                      textAlign: "center",
                      color: C.textMuted,
                      fontWeight: 600,
                      fontSize: 11,
                      borderBottom: `2px solid ${C.border}`,
                    }}
                  >
                    H \ A
                  </th>
                  {Array.from({ length: 6 }, (_, i) => (
                    <th
                      key={i}
                      style={{
                        padding: "6px 8px",
                        textAlign: "center",
                        color: C.accent,
                        fontWeight: 700,
                        fontSize: 13,
                        borderBottom: `2px solid ${C.border}`,
                      }}
                    >
                      {i}
                    </th>
                  ))}
                  <th
                    style={{
                      padding: "6px 8px",
                      textAlign: "center",
                      color: C.textMuted,
                      fontWeight: 600,
                      fontSize: 11,
                      borderBottom: `2px solid ${C.border}`,
                    }}
                  >
                    Row Σ
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.score_matrix.map((row, h) => {
                  const rowSum = row.reduce((a: number, b: number) => a + b, 0);
                  return (
                    <tr key={h}>
                      <td
                        style={{
                          padding: "4px 8px",
                          textAlign: "center",
                          fontWeight: 700,
                          color: C.accent,
                          fontSize: 13,
                          borderBottom: `1px solid ${C.borderLight}`,
                        }}
                      >
                        {h}
                      </td>
                      {row.map((prob: number, a: number) => {
                        const pctStr = pct(prob);
                        return (
                          <td
                            key={a}
                            style={{
                              padding: "8px 6px",
                              textAlign: "center",
                              background: heatColor(prob, maxProb),
                              border: `1px solid ${C.borderLight}`,
                              color: prob > maxProb * 0.4 ? "#fff" : C.text,
                              fontWeight: prob > maxProb * 0.3 ? 700 : 400,
                              fontSize: 12,
                              fontVariantNumeric: "tabular-nums",
                              transition: "background 0.15s",
                              cursor: "default",
                            }}
                            title={`${data.home_team} ${h} – ${data.away_team} ${a}: ${pctStr}`}
                          >
                            {prob > 0.0001 ? pctStr : "—"}
                          </td>
                        );
                      })}
                      <td
                        style={{
                          padding: "4px 8px",
                          textAlign: "center",
                          color: C.textMuted,
                          fontSize: 11,
                          fontWeight: 600,
                          borderBottom: `1px solid ${C.borderLight}`,
                          borderLeft: `2px solid ${C.border}`,
                        }}
                      >
                        {pct(rowSum)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            <p
              style={{
                fontSize: 11,
                color: C.textMuted,
                marginTop: 10,
                textAlign: "center",
              }}
            >
              Rows = {data.home_team} goals, Columns = {data.away_team} goals.
              Colour intensity ∝ joint probability (max ={" "}
              {(maxProb * 100).toFixed(2)}%).
            </p>
          </section>

          {/* ════════════════════════════════════════════════════
              SECTION C — Asian Handicap Breakdown
              ════════════════════════════════════════════════════ */}
          <section
            style={{
              background: C.surface,
              border: `1px solid ${C.border}`,
              borderRadius: 10,
              padding: "20px 24px",
            }}
          >
            <h2
              style={{
                fontSize: 15,
                fontWeight: 700,
                color: C.text,
                marginBottom: 16,
                letterSpacing: "0.02em",
              }}
            >
              🧮 Asian Handicap Breakdown —{" "}
              <span style={{ color: C.accent }}>
                {data.home_team} -0.75
              </span>
            </h2>

            <p
              style={{
                fontSize: 12,
                color: C.textMuted,
                marginBottom: 16,
                lineHeight: 1.5,
              }}
            >
              A quarter line (−0.75) is mathematically split into two
              components: a{" "}
              <strong style={{ color: C.text }}>full win</strong> component
              (−0.5) and a <strong style={{ color: C.text }}>half/push</strong>{" "}
              component (−1.0). The combined expected value is the average of
              the two.
            </p>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 16,
                marginBottom: 20,
              }}
            >
              {/* Component cards */}
              {(["full_win_component", "half_component"] as const).map(
                (compKey) => {
                  const comp = data.asian_handicap_breakdown[compKey];
                  return (
                    <div
                      key={compKey}
                      style={{
                        background: C.surface2,
                        borderRadius: 8,
                        padding: "14px 16px",
                        border: `1px solid ${C.borderLight}`,
                      }}
                    >
                      <div
                        style={{
                          fontSize: 12,
                          fontWeight: 700,
                          color: C.text,
                          marginBottom: 10,
                          textTransform: "uppercase",
                          letterSpacing: "0.04em",
                        }}
                      >
                        {labelForLine(comp.line)}
                      </div>
                      <table
                        style={{
                          width: "100%",
                          borderCollapse: "collapse",
                          fontSize: 13,
                        }}
                      >
                        <tbody>
                          {(["P_win", "P_push", "P_loss"] as const).map(
                            (key) => (
                              <tr key={key}>
                                <td
                                  style={{
                                    padding: "4px 0",
                                    color: C.textMuted,
                                    fontWeight: 500,
                                  }}
                                >
                                  {labelForOutcome(key)}
                                </td>
                                <td
                                  style={{
                                    padding: "4px 0",
                                    textAlign: "right",
                                    fontWeight: 700,
                                    color: outcomeColor(key),
                                    fontVariantNumeric: "tabular-nums",
                                  }}
                                >
                                  {pct(comp[key])}
                                </td>
                              </tr>
                            )
                          )}
                        </tbody>
                      </table>
                    </div>
                  );
                }
              )}
            </div>

            {/* Combined EV */}
            <div
              style={{
                background: C.surface2,
                borderRadius: 8,
                padding: "14px 20px",
                border: `1px solid ${C.borderLight}`,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <span
                style={{
                  fontSize: 14,
                  fontWeight: 600,
                  color: C.text,
                }}
              >
                Combined Expected Value
              </span>
              <span
                style={{
                  fontSize: 22,
                  fontWeight: 800,
                  color:
                    data.asian_handicap_breakdown.combined_ev > 0.5
                      ? C.green
                      : C.text,
                  fontVariantNumeric: "tabular-nums",
                }}
              >
                {pct(data.asian_handicap_breakdown.combined_ev)}
              </span>
            </div>

            <p
              style={{
                fontSize: 11,
                color: C.textMuted,
                marginTop: 10,
                textAlign: "center",
              }}
            >
              Combined EV = 0.5 × P_win(−0.5) + 0.5 × P_win(−1.0). This
              represents the probability that backing{" "}
              <strong style={{ color: C.text }}>{data.home_team} -0.75</strong>{" "}
              yields a positive return.
            </p>
          </section>
        </>
      )}
    </main>
  );
}
