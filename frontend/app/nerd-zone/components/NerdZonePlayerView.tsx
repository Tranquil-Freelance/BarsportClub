"use client";

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import "../../i18n/config";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Types ────────────────────────────────────────────────────────────────────
interface MatchLogRow {
  date: string; venue: string; opponent: string;
  score: string; result: string;
  minutes: number; goals: number; assists: number;
  shots: number; key_passes: number; xg: number; xa: number;
}

interface ShotDot {
  x: number; y: number; xg: number;
  result: string; situation: string; minute: number;
}

interface PlayerData { match_log: MatchLogRow[]; shots: ShotDot[]; }

interface Props {
  player: string;
  team: string;
  league: string;
  backendSeason: string;
  onBackToTeam: () => void;
  onBackToLeague: () => void;
}

// ── Shared cell styles ───────────────────────────────────────────────────────
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

// ── Result color map ─────────────────────────────────────────────────────────
const RESULT_COLOR: Record<string, string> = {
  W: "#4ade80",
  D: "#fbbf24",
  L: "#f87171",
};

// ── Tooltip state ────────────────────────────────────────────────────────────
interface Tip { x: number; y: number; label: string; }

// ── Pitch half SVG ───────────────────────────────────────────────────────────
// Coordinate system: svgX = (1 - dbX) * 105  [goal at x=0, halfway at x=52.5]
//                   svgY = dbY * 68           [top=0, bottom=68]
// viewBox covers half pitch + goal depth: x from -5 to 57, y from -3 to 71
function PitchHalf({ shots }: { shots: ShotDot[] }) {
  const [tip, setTip] = useState<Tip | null>(null);

  return (
    <div style={{ position: "relative", display: "block", width: "100%" }}>
      <svg
        viewBox="-5 -3 62 74"
        style={{ display: "block", width: "100%", height: "500px", background: "#060e08" }}
        preserveAspectRatio="xMidYMid meet"
        onMouseLeave={() => setTip(null)}
      >
        {/* ── Pitch fill ── */}
        <rect x="0" y="0" width="52.5" height="68" fill="#0c1a0f" />

        {/* ── Penalty area: 40.32m wide, 16.5m deep ── */}
        <rect x="0" y="13.84" width="16.5" height="40.32"
          fill="none" stroke="#1a3320" strokeWidth="0.5" />

        {/* ── Six-yard box: 18.32m wide, 5.5m deep ── */}
        <rect x="0" y="24.84" width="5.5" height="18.32"
          fill="none" stroke="#1a3320" strokeWidth="0.4" />

        {/* ── Goal: 7.32m wide, 2.44m deep ── */}
        <rect x="-2.44" y="30.34" width="2.44" height="7.32"
          fill="#0a1510" stroke="#2d5a3d" strokeWidth="0.5" />

        {/* ── Pitch boundary (half) ── */}
        <rect x="0" y="0" width="52.5" height="68"
          fill="none" stroke="#1a3320" strokeWidth="0.5" />

        {/* ── Penalty spot ── */}
        <circle cx="11" cy="34" r="0.5" fill="#1a3320" />

        {/* ── Penalty arc D ── */}
        <path d="M 16.5 26.7 A 9.15 9.15 0 0 1 16.5 41.3"
          fill="none" stroke="#1a3320" strokeWidth="0.4" />

        {/* ── Halfway line ── */}
        <line x1="52.5" y1="0" x2="52.5" y2="68"
          stroke="#1a3320" strokeWidth="0.4" strokeDasharray="1.5 1.5" />

        {/* ── Shots ── */}
        {shots.map((s, i) => {
          const cx = (1 - s.x) * 105;
          const cy = s.y * 68;
          const r = Math.max(1.2, Math.min(5.5, s.xg * 26));
          const isGoal = s.result === "Goal";
          const fill = isGoal ? "#10B981" : "#374151";
          const stroke = isGoal ? "#065f46" : "#4b5563";
          const opacity = isGoal ? 0.92 : 0.70;
          return (
            <circle
              key={i}
              cx={cx} cy={cy} r={r}
              fill={fill} fillOpacity={opacity}
              stroke={stroke} strokeWidth="0.3"
              style={{ cursor: "default" }}
              onMouseEnter={() =>
                setTip({
                  x: cx, y: cy,
                  label: `${s.result} · xG ${s.xg.toFixed(3)} · ${s.minute}'`
                })
              }
            />
          );
        })}

        {/* ── Tooltip ── */}
        {tip && (
          <g>
            <rect
              x={tip.x + 1} y={tip.y - 6}
              width={tip.label.length * 2.4 + 2} height="6.5"
              rx="0.6" fill="#111827" fillOpacity="0.94"
            />
            <text
              x={tip.x + 2} y={tip.y - 1.2}
              fontSize="4" fill="#e2e8f0"
            >
              {tip.label}
            </text>
          </g>
        )}
      </svg>

      {/* ── Legend ── */}
      <div style={{ display: "flex", gap: "12px", fontSize: "10px", color: "#4b5563", marginTop: "4px" }}>
        <span><span style={{ color: "#10B981" }}>●</span> Goal</span>
        <span><span style={{ color: "#374151" }}>●</span> No goal</span>
        <span>Size = xG</span>
      </div>
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────────────
export default function NerdZonePlayerView({
  player, team, league, backendSeason, onBackToTeam, onBackToLeague
}: Props) {
  const { t } = useTranslation();
  const [data,    setData]    = useState<PlayerData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setData(null);
    fetch(
      `${API_BASE}/api/nerd-zone/player` +
      `?player_name=${encodeURIComponent(player)}` +
      `&team_name=${encodeURIComponent(team)}` +
      `&season=${encodeURIComponent(backendSeason)}`
    )
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [player, team, backendSeason]);

  // ── Breadcrumb ─────────────────────────────────────────────────────────────
  const breadcrumb = (
    <div style={{ marginBottom: "10px", fontSize: "11px", color: "#4b5563" }}>
      <span
        onClick={onBackToLeague}
        style={{ color: "#3b82f6", cursor: "pointer", textDecoration: "underline" }}
      >
        ← {league}
      </span>
      {" / "}
      <span
        onClick={onBackToTeam}
        style={{ color: "#3b82f6", cursor: "pointer", textDecoration: "underline" }}
      >
        {team}
      </span>
      {" / "}
      <span style={{ color: "#e2e8f0", fontWeight: 700 }}>{player}</span>
    </div>
  );

  if (loading) return (
    <div style={ROOT} suppressHydrationWarning>{breadcrumb}<div style={{ color: "#4b5563", padding: "20px 0" }}>{t("common.loading")}</div></div>
  );
  if (error || !data) return (
    <div style={ROOT} suppressHydrationWarning>{breadcrumb}<div style={{ color: "#ef4444", padding: "12px 0" }}>{t("nerd.error", { msg: error ?? "no data" })}</div></div>
  );

  // ── Totals ─────────────────────────────────────────────────────────────────
  const totals = data.match_log.reduce(
    (acc, r) => ({
      minutes:    acc.minutes    + r.minutes,
      goals:      acc.goals      + r.goals,
      assists:    acc.assists    + r.assists,
      shots:      acc.shots      + r.shots,
      key_passes: acc.key_passes + r.key_passes,
      xg:         acc.xg         + r.xg,
      xa:         acc.xa         + r.xa,
    }),
    { minutes: 0, goals: 0, assists: 0, shots: 0, key_passes: 0, xg: 0, xa: 0 }
  );

  return (
    <div style={ROOT} suppressHydrationWarning>
      {breadcrumb}

      {/* ── Two-column: shot map left, match log right ─────────────────────── */}
      <div style={{ display: "flex", gap: "24px", alignItems: "flex-start", flexWrap: "wrap" }}>

        {/* ── Shot map column ─────────────────────────────────────────────── */}
        <div style={{ flex: "0 0 480px", minWidth: "320px" }}>
          <div style={{
            fontSize: "10px", color: "#4b5563",
            textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "5px"
          }}>
            {t("nerd.shot_map_summary", {
              n: data.shots.length,
              m: data.shots.filter(s => s.result === "Goal").length,
              xg: data.shots.reduce((a, s) => a + s.xg, 0).toFixed(2),
            })}
          </div>
          {data.shots.length === 0
            ? <div style={{ color: "#4b5563", fontSize: "11px" }}>{t("nerd.no_shot_data")}</div>
            : <PitchHalf shots={data.shots} />
          }
        </div>

        {/* ── Match log column ────────────────────────────────────────────── */}
        <div style={{ flex: "1 1 480px", minWidth: "400px", overflowX: "auto" }}>
          <div style={{
            fontSize: "10px", color: "#4b5563",
            textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "4px"
          }}>
            {t("nerd.match_log_title", { n: data.match_log.length })}
          </div>
          <table style={{ borderCollapse: "collapse", fontSize: "12px", width: "100%" }}>
            <thead>
              <tr>
                {["Date","H/A","Opponent","Score","Res","Min","G","A","Sh","KP","xG","xA"].map(h => (
                  <th key={h} style={{ ...TH, textAlign: h === "Opponent" ? "left" : "center" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.match_log.map((row, i) => (
                <tr
                  key={i}
                  onMouseEnter={e => (e.currentTarget.style.background = "#161b27")}
                  onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
                >
                  <td style={{ ...TD, color: "#6b7280", whiteSpace: "nowrap" }}>{row.date}</td>
                  <td style={{ ...TD, color: "#9ca3af" }}>{row.venue}</td>
                  <td style={{ ...TD, textAlign: "left", color: "#93c5fd", whiteSpace: "nowrap" }}>
                    {row.opponent}
                  </td>
                  <td style={{ ...TD, color: "#9ca3af", whiteSpace: "nowrap" }}>{row.score}</td>
                  <td style={{
                    ...TD, fontWeight: 700, fontSize: "11px",
                    color: RESULT_COLOR[row.result] ?? "#cbd5e0"
                  }}>
                    {row.result}
                  </td>
                  <td style={TD}>{row.minutes}</td>
                  <td style={{ ...TD, color: row.goals > 0 ? "#4ade80" : TD.color }}>{row.goals}</td>
                  <td style={{ ...TD, color: row.assists > 0 ? "#a78bfa" : TD.color }}>{row.assists}</td>
                  <td style={TD}>{row.shots}</td>
                  <td style={TD}>{row.key_passes}</td>
                  <td style={{ ...TD, color: "#34d399" }}>{row.xg.toFixed(2)}</td>
                  <td style={{ ...TD, color: "#818cf8" }}>{row.xa.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
            {/* Totals footer */}
            <tfoot>
              <tr style={{ borderTop: "2px solid #374151" }}>
                <td colSpan={5} style={{
                  ...TD, textAlign: "right", color: "#4b5563",
                  fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.08em"
                }}>
                  {t("nerd.total")}
                </td>
                <td style={{ ...TD, fontWeight: 700, color: "#e2e8f0" }}>{totals.minutes}</td>
                <td style={{ ...TD, fontWeight: 700, color: totals.goals > 0 ? "#4ade80" : "#e2e8f0" }}>
                  {totals.goals}
                </td>
                <td style={{ ...TD, fontWeight: 700, color: totals.assists > 0 ? "#a78bfa" : "#e2e8f0" }}>
                  {totals.assists}
                </td>
                <td style={{ ...TD, fontWeight: 700, color: "#e2e8f0" }}>{totals.shots}</td>
                <td style={{ ...TD, fontWeight: 700, color: "#e2e8f0" }}>{totals.key_passes}</td>
                <td style={{ ...TD, fontWeight: 700, color: "#34d399" }}>{totals.xg.toFixed(2)}</td>
                <td style={{ ...TD, fontWeight: 700, color: "#818cf8" }}>{totals.xa.toFixed(2)}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  );
}
