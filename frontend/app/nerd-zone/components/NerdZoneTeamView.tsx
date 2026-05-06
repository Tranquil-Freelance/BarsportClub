"use client";

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import "../../i18n/config";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface RosterRow {
  player: string; position: string; apps: number; minutes: number;
  goals: number; assists: number; sh90: number; kp90: number;
  xg: number; xa: number; xg90: number; xa90: number;
  xgchain: number; xgbuildup: number;
}

interface SituationRow {
  situation: string; shots: number; goals: number; xg: number;
}

interface TeamData { roster: RosterRow[]; situations: SituationRow[]; }

interface Props {
  team: string;
  league: string;
  backendSeason: string;
  onBack: () => void;
  onSelectPlayer: (player: string) => void;
}

// ── Shared micro-styles ──────────────────────────────────────────────────────
const TH: React.CSSProperties = {
  padding: "3px 6px",
  border: "1px solid #2d3748",
  fontWeight: 600,
  letterSpacing: "0.04em",
  textAlign: "center",
  whiteSpace: "nowrap",
  color: "#718096",
  fontSize: "10px",
  textTransform: "uppercase",
  background: "#111827",
};

const TD: React.CSSProperties = {
  padding: "2px 6px",
  border: "1px solid #1f2937",
  textAlign: "center",
  fontSize: "12px",
  fontVariantNumeric: "tabular-nums",
  color: "#cbd5e0",
};

const ROOT: React.CSSProperties = {
  fontFamily: "'Courier New', Courier, monospace",
  fontSize: "12px",
  color: "#cbd5e0",
  background: "#0d1117",
  minHeight: "100vh",
  padding: "10px 32px",
  maxWidth: "1600px",
  margin: "0 auto",
  boxSizing: "border-box",
};

// ── Delta superscript ────────────────────────────────────────────────────────
function Delta({ base, actual }: { base: number; actual: number }) {
  const delta = actual - base;
  if (Math.abs(delta) < 0.005) return null;
  const color = delta > 0 ? "#10B981" : "#EF4444";
  const sign  = delta > 0 ? "+" : "";
  return (
    <sup style={{ fontSize: "9px", color, marginLeft: "2px", fontWeight: 700 }}>
      {sign}{delta.toFixed(2)}
    </sup>
  );
}

// ── Breadcrumb ───────────────────────────────────────────────────────────────
function Breadcrumb({ league, team, onBack }: { league: string; team: string; onBack: () => void }) {
  return (
    <div style={{ marginBottom: "10px", fontSize: "11px", color: "#4b5563" }}>
      <span
        onClick={onBack}
        style={{ color: "#3b82f6", cursor: "pointer", textDecoration: "underline" }}
      >
        ← {league}
      </span>
      {" / "}
      <span style={{ color: "#e2e8f0", fontWeight: 700 }}>{team}</span>
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────────────
export default function NerdZoneTeamView({ team, league, backendSeason, onBack, onSelectPlayer }: Props) {
  const { t } = useTranslation();
  const [data,    setData]    = useState<TeamData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);
  const [sortCol, setSortCol] = useState<keyof RosterRow>("xg");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  useEffect(() => {
    setLoading(true);
    setError(null);
    setData(null);
    fetch(
      `${API_BASE}/api/nerd-zone/team` +
      `?team_name=${encodeURIComponent(team)}` +
      `&season=${encodeURIComponent(backendSeason)}`
    )
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [team, backendSeason]);

  function toggleSort(col: keyof RosterRow) {
    if (col === sortCol) setSortDir(d => d === "desc" ? "asc" : "desc");
    else { setSortCol(col); setSortDir("desc"); }
  }

  if (loading) {
    return (
      <div style={ROOT} suppressHydrationWarning>
        <Breadcrumb league={league} team={team} onBack={onBack} />
        <div style={{ color: "#4b5563", padding: "20px 0" }}>{t("common.loading")}</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={ROOT} suppressHydrationWarning>
        <Breadcrumb league={league} team={team} onBack={onBack} />
        <div style={{ color: "#ef4444", padding: "12px 0" }}>{t("nerd.error", { msg: error ?? "no data" })}</div>
      </div>
    );
  }

  const sorted = [...data.roster].sort((a, b) => {
    const av = a[sortCol];
    const bv = b[sortCol];
    if (typeof av === "string" && typeof bv === "string") {
      return sortDir === "desc" ? bv.localeCompare(av) : av.localeCompare(bv);
    }
    return sortDir === "desc"
      ? (bv as number) - (av as number)
      : (av as number) - (bv as number);
  });

  type RosterColDef = { key: keyof RosterRow; label: string; title?: string };
  const rosterCols: RosterColDef[] = [
    { key: "position",  label: "Pos" },
    { key: "apps",      label: "Apps",  title: "Appearances" },
    { key: "minutes",   label: "Min" },
    { key: "goals",     label: "G",     title: "Goals" },
    { key: "assists",   label: "A",     title: "Assists" },
    { key: "sh90",      label: "Sh90",  title: "Shots per 90" },
    { key: "kp90",      label: "KP90",  title: "Key Passes per 90" },
    { key: "xg",        label: "xG",    title: "Expected Goals" },
    { key: "xa",        label: "xA",    title: "Expected Assists" },
    { key: "xg90",      label: "xG90" },
    { key: "xa90",      label: "xA90" },
    { key: "xgchain",   label: "xGCh",  title: "xG Chain" },
    { key: "xgbuildup", label: "xGBu",  title: "xG Buildup" },
  ];

  return (
    <div style={ROOT} suppressHydrationWarning>
      <Breadcrumb league={league} team={team} onBack={onBack} />

      {/* ── Situational block ─────────────────────────────────────────────── */}
      <div style={{ marginBottom: "18px" }}>
        <div style={{ fontSize: "10px", color: "#4b5563", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "4px" }}>
          {t("nerd.shots_by_situation")}
        </div>
        <table style={{ borderCollapse: "collapse", fontSize: "12px", width: "100%", maxWidth: "600px" }}>
          <thead>
            <tr>
              <th style={{ ...TH, textAlign: "left" }}>Situation</th>
              <th style={TH}>Sh</th>
              <th style={TH}>G</th>
              <th style={TH}>xG</th>
            </tr>
          </thead>
          <tbody>
            {data.situations.map(row => (
              <tr key={row.situation}>
                <td style={{ ...TD, textAlign: "left", color: "#e2e8f0", paddingRight: "20px" }}>{row.situation}</td>
                <td style={TD}>{row.shots}</td>
                <td style={TD}>{row.goals}</td>
                <td style={{ ...TD, color: "#34d399" }}>{row.xg.toFixed(2)}</td>
              </tr>
            ))}
            {data.situations.length === 0 && (
              <tr>
                <td colSpan={4} style={{ ...TD, color: "#4b5563", textAlign: "left" }}>{t("nerd.no_shot_data")}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* ── Roster block ──────────────────────────────────────────────────── */}
      <div>
        <div style={{ fontSize: "10px", color: "#4b5563", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "4px" }}>
          {t("nerd.roster_hint", { n: data.roster.length })}
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ borderCollapse: "collapse", fontSize: "12px", width: "100%", tableLayout: "auto" }}>
            <thead>
              <tr>
                <th style={{ ...TH, width: "22px" }}>#</th>
                <th style={{ ...TH, textAlign: "left", minWidth: "150px" }}>Player</th>
                {rosterCols.map(c => (
                  <th
                    key={c.key}
                    title={c.title}
                    onClick={() => toggleSort(c.key)}
                    style={{
                      ...TH,
                      cursor: "pointer",
                      color: sortCol === c.key ? "#e2e8f0" : "#718096",
                      background: sortCol === c.key ? "#1a2035" : "#111827",
                      userSelect: "none",
                    }}
                  >
                    {c.label}{sortCol === c.key ? (sortDir === "desc" ? " ↓" : " ↑") : ""}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((row, i) => (
                <tr
                  key={row.player}
                  onClick={() => onSelectPlayer(row.player)}
                  style={{ cursor: "pointer" }}
                  onMouseEnter={e => (e.currentTarget.style.background = "#161b27")}
                  onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
                >
                  <td style={{ ...TD, color: "#4b5563", fontSize: "10px" }}>{i + 1}</td>
                  <td style={{ ...TD, textAlign: "left", color: "#60a5fa", whiteSpace: "nowrap" }}>
                    {row.player}
                  </td>
                  <td style={{ ...TD, color: "#9ca3af" }}>{row.position || "—"}</td>
                  <td style={TD}>{row.apps}</td>
                  <td style={TD}>{row.minutes}</td>
                  <td style={{ ...TD, color: "#4ade80" }}>{row.goals}</td>
                  <td style={{ ...TD, color: "#a78bfa" }}>{row.assists}</td>
                  <td style={TD}>{row.sh90.toFixed(2)}</td>
                  <td style={TD}>{row.kp90.toFixed(2)}</td>
                  {/* xG + delta vs actual goals */}
                  <td style={TD}>
                    {row.xg.toFixed(2)}
                    <Delta base={row.xg} actual={row.goals} />
                  </td>
                  {/* xA + delta vs actual assists */}
                  <td style={TD}>
                    {row.xa.toFixed(2)}
                    <Delta base={row.xa} actual={row.assists} />
                  </td>
                  <td style={TD}>{row.xg90.toFixed(3)}</td>
                  <td style={TD}>{row.xa90.toFixed(3)}</td>
                  <td style={TD}>{row.xgchain.toFixed(2)}</td>
                  <td style={TD}>{row.xgbuildup.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
