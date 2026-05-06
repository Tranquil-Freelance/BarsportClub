"use client";

import React, { useEffect, useState, useMemo, useCallback, useRef } from "react";
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

interface MarketEntry {
  match_name: string;
  match_id: number;
  market_key: string;
  market_label: string;
  odds: number | null;
  p_book: number | null;
  p_model: number;
  diff: number | null;
  ev_base: number | null;
}

interface Lab1Response {
  markets: MarketEntry[];
}

// ═══════════════════════════════════════════════════════════════
//  COLOR PALETTE — Bloomberg Terminal inspired
// ═══════════════════════════════════════════════════════════════

const C = {
  bg: "#0a0d14",
  surface: "#10141e",
  surfaceAlt: "#161b26",
  border: "#1e2533",
  borderLight: "#2a3344",
  text: "#c8d0d8",
  textDim: "#6b7688",
  accent: "#58a6ff",
  green: "#00ff41",
  greenDim: "#00cc33",
  red: "#ff3333",
  redDim: "#cc2222",
  amber: "#ffaa33",
  gold: "#ffd700",
};

// ═══════════════════════════════════════════════════════════════
//  NAVIGATION BAR — shared between Lab 1 & Lab 2
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
        marginBottom: 12,
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
//  COMPONENT
// ═══════════════════════════════════════════════════════════════

export default function Lab1MarketAnalyticsPage() {
  const [data, setData] = useState<Lab1Response | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<string>("diff");
  const [sortAsc, setSortAsc] = useState(false);
  const [marketFilter, setMarketFilter] = useState<string>("all");

  // ── Dropdown state ──────────────────────────────────────────
  const [leagues, setLeagues] = useState<LeagueMatches[]>([]);
  const [dropdownLoading, setDropdownLoading] = useState(true);
  const [dropdownError, setDropdownError] = useState<string | null>(null);
  const [selectedLeague, setSelectedLeague] = useState<string>("");
  const [selectedMatchIds, setSelectedMatchIds] = useState<number[]>([]);
  const [multiSelectOpen, setMultiSelectOpen] = useState(false);

  // Ref for outside-click detection (fixes the native event bubbling bug)
  const dropdownWrapperRef = useRef<HTMLDivElement>(null);

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

  // ── Fetch lab1 analytics ────────────────────────────────────
  const fetchLab1 = useCallback(async (ids: number[]) => {
    if (ids.length === 0) return;
    try {
      setLoading(true);
      setError(null);
      const idsStr = ids.join(",");
      const res = await get<Lab1Response>(
        `/betting/lab1-analytics?match_ids=${encodeURIComponent(idsStr)}`
      );
      setData(res);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Unknown error fetching lab1 analytics"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  // ── Handle Load click ─────────────────────────────────────
  const handleLoad = () => {
    if (selectedMatchIds.length === 0) return;
    fetchLab1(selectedMatchIds);
  };

  // ── Toggle a match in the multi-select ──────────────────────
  const toggleMatch = (matchId: number) => {
    setSelectedMatchIds((prev) =>
      prev.includes(matchId)
        ? prev.filter((id) => id !== matchId)
        : [...prev, matchId]
    );
  };

  // ── Select all / deselect all for current league ────────────
  const toggleSelectAll = () => {
    if (selectedMatchIds.length === currentMatches.length) {
      setSelectedMatchIds([]);
    } else {
      setSelectedMatchIds(currentMatches.map((m) => m.match_id));
    }
  };

  // ── Close multi-select on outside click ─────────────────────
  // Uses a ref-based approach to check if the click is outside,
  // which properly handles native DOM event propagation.
  useEffect(() => {
    if (!multiSelectOpen) return;
    const handler = (e: MouseEvent) => {
      if (
        dropdownWrapperRef.current &&
        !dropdownWrapperRef.current.contains(e.target as Node)
      ) {
        setMultiSelectOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [multiSelectOpen]);

  // ── Filtered & sorted markets ─────────────────────────────
  const filteredMarkets = useMemo(() => {
    if (!data) return [];
    let list = [...data.markets];

    // market type filter
    if (marketFilter !== "all") {
      list = list.filter((m) => m.market_key.startsWith(marketFilter));
    }

    // sort
    list.sort((a, b) => {
      let cmp = 0;
      switch (sortKey) {
        case "match_name":
          cmp = a.match_name.localeCompare(b.match_name);
          break;
        case "market_label":
          cmp = a.market_label.localeCompare(b.market_label);
          break;
        case "odds":
          cmp = (a.odds ?? 0) - (b.odds ?? 0);
          break;
        case "p_book":
          cmp = (a.p_book ?? 0) - (b.p_book ?? 0);
          break;
        case "p_model":
          cmp = a.p_model - b.p_model;
          break;
        case "diff":
          cmp = (a.diff ?? 0) - (b.diff ?? 0);
          break;
        case "ev_base":
          cmp = (a.ev_base ?? 0) - (b.ev_base ?? 0);
          break;
        default:
          cmp = (a.diff ?? 0) - (b.diff ?? 0);
      }
      return sortAsc ? cmp : -cmp;
    });

    return list;
  }, [data, sortKey, sortAsc, marketFilter]);

  // ── Sort helpers ─────────────────────────────────────────
  function handleSort(key: string) {
    if (sortKey === key) {
      setSortAsc((prev) => !prev);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  }

  function SortArrow({ colKey }: { colKey: string }) {
    if (sortKey !== colKey) return null;
    return <span style={{ marginLeft: 2 }}>{sortAsc ? "▲" : "▼"}</span>;
  }

  // ── Stats ─────────────────────────────────────────────────
  const stats = useMemo(() => {
    if (!data) return null;
    const m = data.markets;
    return {
      total: m.length,
      positiveEv: m.filter((x) => x.ev_base !== null && x.ev_base > 0).length,
      negativeEv: m.filter((x) => x.ev_base !== null && x.ev_base <= 0).length,
      positiveDelta: m.filter((x) => x.diff !== null && x.diff > 0).length,
      negativeDelta: m.filter((x) => x.diff !== null && x.diff <= 0).length,
      uniqueMatches: new Set(m.map((x) => x.match_name)).size,
      uniqueMarkets: new Set(m.map((x) => x.market_key)).size,
    };
  }, [data]);

  // ── Market type options ───────────────────────────────────
  const marketOptions = useMemo(() => {
    if (!data) return ["all"];
    const types = new Set<string>();
    data.markets.forEach((m) => {
      const prefix = m.market_key.split("_")[0];
      types.add(prefix);
    });
    return ["all", ...Array.from(types).sort()];
  }, [data]);

  // ── Format helpers ────────────────────────────────────────
  const fmtPct = (v: number | null) =>
    v === null || v === undefined ? "-" : (v * 100).toFixed(1) + "%";
  const fmtOdds = (v: number | null) =>
    v === null || v === undefined ? "-" : v.toFixed(2);
  const fmtDelta = (v: number | null) =>
    v === null || v === undefined
      ? "-"
      : (v > 0 ? "+" : "") + (v * 100).toFixed(2) + "%";

  const dropdownBase: React.CSSProperties = {
    background: C.surface,
    border: `1px solid ${C.borderLight}`,
    color: C.text,
    fontFamily: "'Courier New', monospace",
    fontSize: 11,
    padding: "3px 6px",
    outline: "none",
    cursor: "pointer",
  };

  // ══════════════════════════════════════════════════════════
  //  RENDER
  // ══════════════════════════════════════════════════════════

  return (
    <div
      style={{
        padding: "12px 20px 40px",
        fontFamily: "'Courier New', Courier, monospace",
        background: C.bg,
        color: C.text,
        minHeight: "100vh",
        fontSize: 12,
        lineHeight: 1.5,
      }}
    >
      {/* ═══ LAB NAV ═══ */}
      <LabNavBar />

      {/* ═══ HEADER ═══ */}
      <div style={{ marginBottom: 16, borderBottom: `1px solid ${C.border}`, paddingBottom: 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
          <pre style={{ fontSize: 14, fontWeight: "bold", color: C.accent, margin: 0 }}>
╔══ LAB 1: MARKET ANALYTICS ══╗
          </pre>
          {stats && (
            <span style={{ color: C.textDim, fontSize: 11 }}>
              {stats.total} markets | {stats.uniqueMatches} matches | {stats.uniqueMarkets} types
            </span>
          )}
        </div>

        {/* Control bar */}
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          {/* League dropdown */}
          <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
            <span style={{ color: C.textDim, fontSize: 11 }}>league:</span>
            <select
              value={selectedLeague}
              onChange={(e) => {
                setSelectedLeague(e.target.value);
                setSelectedMatchIds([]);
              }}
              disabled={dropdownLoading}
              style={{ ...dropdownBase, minWidth: 100 }}
            >
              {dropdownLoading && <option value="">Loading matches...</option>}
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
              <span style={{ color: C.textDim, fontSize: 10 }}>Loading matches...</span>
            )}
            {dropdownError && (
              <span style={{ color: C.red, fontSize: 10 }}>
                Error loading matches. Is the backend running?
              </span>
            )}
          </div>

          {/* Match multi-select dropdown */}
          <div
            ref={dropdownWrapperRef}
            style={{ display: "flex", gap: 4, alignItems: "center", position: "relative" }}
          >
            <span style={{ color: C.textDim, fontSize: 11 }}>matches:</span>
            <div
              onClick={() => setMultiSelectOpen((prev) => !prev)}
              style={{
                ...dropdownBase,
                minWidth: 180,
                userSelect: "none",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 4,
              }}
            >
              <span style={{ color: selectedMatchIds.length > 0 ? C.text : C.textDim }}>
                {selectedMatchIds.length > 0
                  ? `${selectedMatchIds.length} selected`
                  : "Select matches"}
              </span>
              <span style={{ color: C.textDim, fontSize: 9 }}>{multiSelectOpen ? "▲" : "▼"}</span>
            </div>

            {multiSelectOpen && (
              <div
                style={{
                  position: "absolute",
                  top: "100%",
                  left: 0,
                  marginTop: 2,
                  background: C.surface,
                  border: `1px solid ${C.borderLight}`,
                  maxHeight: 220,
                  overflowY: "auto",
                  minWidth: 260,
                  zIndex: 100,
                  boxShadow: "0 4px 12px rgba(0,0,0,0.5)",
                }}
              >
                {/* Select all / deselect all */}
                <div
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleSelectAll();
                  }}
                  style={{
                    padding: "5px 8px",
                    borderBottom: `1px solid ${C.border}`,
                    color: C.accent,
                    cursor: "pointer",
                    fontSize: 10,
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                  }}
                >
                  {selectedMatchIds.length === currentMatches.length
                    ? "— Deselect All"
                    : "✓ Select All"}
                </div>

                {currentMatches.length === 0 && (
                  <div style={{ padding: "8px", color: C.textDim, fontSize: 10 }}>
                    No matches available
                  </div>
                )}

                {currentMatches.map((m) => {
                  const checked = selectedMatchIds.includes(m.match_id);
                  return (
                    <div
                      key={m.match_id}
                      onClick={() => toggleMatch(m.match_id)}
                      style={{
                        padding: "4px 8px",
                        cursor: "pointer",
                        background: checked ? C.surfaceAlt : "transparent",
                        color: checked ? C.accent : C.text,
                        display: "flex",
                        alignItems: "center",
                        gap: 6,
                        fontSize: 11,
                        borderBottom: `1px solid ${C.border}`,
                        transition: "background 0.1s",
                      }}
                      onMouseOver={(e) => {
                        (e.currentTarget as HTMLElement).style.background = checked
                          ? C.surfaceAlt
                          : C.surface;
                      }}
                      onMouseOut={(e) => {
                        (e.currentTarget as HTMLElement).style.background = checked
                          ? C.surfaceAlt
                          : "transparent";
                      }}
                    >
                      <span
                        style={{
                          fontSize: 10,
                          color: checked ? C.accent : C.textDim,
                          fontWeight: checked ? "bold" : "normal",
                        }}
                      >
                        {checked ? "✓" : "○"}
                      </span>
                      {m.label}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Load button */}
          <button
            onClick={handleLoad}
            disabled={selectedMatchIds.length === 0}
            style={{
              background: selectedMatchIds.length > 0 ? C.accent : C.border,
              color: selectedMatchIds.length > 0 ? "#fff" : C.textDim,
              border: "none",
              fontFamily: "'Courier New', monospace",
              fontSize: 10,
              fontWeight: "bold",
              padding: "3px 8px",
              cursor: selectedMatchIds.length > 0 ? "pointer" : "default",
              textTransform: "uppercase",
            }}
          >
            {selectedMatchIds.length > 0
              ? `Load (${selectedMatchIds.length})`
              : "Load"}
          </button>

          {/* Market type filter */}
          <div style={{ display: "flex", gap: 4, alignItems: "center", marginLeft: 8 }}>
            <span style={{ color: C.textDim, fontSize: 11 }}>market:</span>
            <select
              value={marketFilter}
              onChange={(e) => setMarketFilter(e.target.value)}
              style={dropdownBase}
            >
              {marketOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt === "all" ? "ALL" : opt}
                </option>
              ))}
            </select>
          </div>

          {/* Stats summary */}
          {stats && (
            <div style={{ display: "flex", gap: 12, marginLeft: "auto", fontSize: 11 }}>
              <span style={{ color: C.textDim }}>
                Δ+: <span style={{ color: C.green }}>{stats.positiveDelta}</span>
                {" | "}Δ−: <span style={{ color: C.red }}>{stats.negativeDelta}</span>
              </span>
              <span style={{ color: C.textDim }}>
                EV⁺: <span style={{ color: C.green }}>{stats.positiveEv}</span>
                {" | "}EV⁻: <span style={{ color: C.red }}>{stats.negativeEv}</span>
              </span>
            </div>
          )}
        </div>
      </div>

      {/* ═══ DATA TABLE ═══ */}
      <div style={{ overflowX: "auto", border: `1px solid ${C.border}` }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
          <thead>
            {/* Column headers */}
            <tr style={{ background: C.surface }}>
              <TH style={{ cursor: "pointer", userSelect: "none" }} onClick={() => handleSort("match_name")}>
                Match <SortArrow colKey="match_name" />
              </TH>
              <TH style={{ cursor: "pointer", userSelect: "none" }} onClick={() => handleSort("market_label")}>
                Market <SortArrow colKey="market_label" />
              </TH>
              <TH style={{ cursor: "pointer", userSelect: "none", textAlign: "right" }} onClick={() => handleSort("odds")}>
                Odds <SortArrow colKey="odds" />
              </TH>
              <TH style={{ cursor: "pointer", userSelect: "none", textAlign: "right" }} onClick={() => handleSort("p_book")}>
                P_Book <SortArrow colKey="p_book" />
              </TH>
              <TH style={{ cursor: "pointer", userSelect: "none", textAlign: "right" }} onClick={() => handleSort("p_model")}>
                P_Model <SortArrow colKey="p_model" />
              </TH>
              <TH style={{ cursor: "pointer", userSelect: "none", textAlign: "right" }} onClick={() => handleSort("diff")}>
                Delta <SortArrow colKey="diff" />
              </TH>
              <TH style={{ cursor: "pointer", userSelect: "none", textAlign: "right" }} onClick={() => handleSort("ev_base")}>
                EV Base <SortArrow colKey="ev_base" />
              </TH>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={7} style={{ padding: 24, textAlign: "center", color: C.textDim }}>
                  Loading analytics data...
                </td>
              </tr>
            )}
            {error && !loading && (
              <tr>
                <td colSpan={7} style={{ padding: 24, textAlign: "center", color: C.red }}>
                  {error}
                </td>
              </tr>
            )}
            {!loading && !error && filteredMarkets.length === 0 && (
              <tr>
                <td
                  colSpan={7}
                  style={{ padding: 24, textAlign: "center", color: C.textDim }}
                >
                  No markets returned. Select matches and click Load.
                </td>
              </tr>
            )}
            {!loading && !error && filteredMarkets.map((m, i) => (
                <tr
                  key={`${m.match_id}-${m.market_key}-${i}`}
                  style={{
                    borderBottom: `1px solid ${C.border}`,
                    transition: "background 0.1s",
                  }}
                  onMouseOver={(e) => {
                    (e.currentTarget as HTMLElement).style.background = C.surfaceAlt;
                  }}
                  onMouseOut={(e) => {
                    (e.currentTarget as HTMLElement).style.background = "transparent";
                  }}
                >
                  <TD style={{ fontWeight: 600, color: C.accent }}>
                    {m.match_name}
                  </TD>
                  <TD style={{ color: C.textDim }}>
                    {m.market_label || m.market_key}
                  </TD>
                  <TD style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                    {fmtOdds(m.odds)}
                  </TD>
                  <TD style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                    {fmtPct(m.p_book)}
                  </TD>
                  <TD style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                    {fmtPct(m.p_model)}
                  </TD>
                  <TD
                    style={{
                      textAlign: "right",
                      fontVariantNumeric: "tabular-nums",
                      fontWeight: "bold",
                      color:
                        m.diff !== null && m.diff > 0
                          ? C.green
                          : m.diff !== null && m.diff < 0
                            ? C.red
                            : C.textDim,
                    }}
                  >
                    {fmtDelta(m.diff)}
                  </TD>
                  <TD
                    style={{
                      textAlign: "right",
                      fontVariantNumeric: "tabular-nums",
                      fontWeight: "bold",
                      color:
                        m.ev_base !== null && m.ev_base > 0
                          ? C.green
                          : m.ev_base !== null && m.ev_base < 0
                            ? C.red
                            : C.textDim,
                    }}
                  >
                    {fmtDelta(m.ev_base)}
                  </TD>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {/* ═══ FOOTER ═══ */}
      <div
        style={{
          marginTop: 16,
          padding: "6px 0",
          borderTop: `1px solid ${C.border}`,
          color: C.textDim,
          fontSize: 10,
          display: "flex",
          justifyContent: "space-between",
        }}
      >
        <span>
          Lab 1 v1.0 — Raw Market Analytics | No AI filter | No EV threshold
        </span>
        <span>
          {stats && `${stats.total} markets · ${stats.positiveEv} positive EV · ${stats.negativeEv} negative EV`}
        </span>
      </div>
    </div>
  );
}

// ─── Bloomberg-style table helpers ────────────────────────────

function TH({
  children,
  colSpan,
  style,
  onClick,
}: {
  children?: React.ReactNode;
  colSpan?: number;
  style?: React.CSSProperties;
  onClick?: () => void;
}) {
  return (
    <th
      colSpan={colSpan}
      onClick={onClick}
      style={{
        padding: "6px 8px",
        fontWeight: "bold",
        color: C.textDim,
        textTransform: "uppercase",
        fontSize: 10,
        letterSpacing: "0.8px",
        whiteSpace: "nowrap",
        borderBottom: `1px solid ${C.borderLight}`,
        ...style,
      }}
    >
      {children}
    </th>
  );
}

function TD({
  children,
  style,
  colSpan,
}: {
  children?: React.ReactNode;
  style?: React.CSSProperties;
  colSpan?: number;
}) {
  return (
    <td
      colSpan={colSpan}
      style={{
        padding: "4px 8px",
        whiteSpace: "nowrap",
        ...style,
      }}
    >
      {children}
    </td>
  );
}
