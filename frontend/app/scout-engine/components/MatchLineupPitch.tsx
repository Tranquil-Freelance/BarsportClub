"use client";
import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import "../../i18n/config";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─── Types ────────────────────────────────────────────────────────────────────
interface SubInfo { name: string; minute: number }

interface StarterPlayer {
  name: string;
  position: string;
  time: number;
  goals: number;
  assists: number;
  yellow_card: boolean;
  red_card: boolean;
  xg: number;
  xa: number;
  sub_in: SubInfo | null;
}

interface TeamLineup { team: string; starters: StarterPlayer[]; subs: StarterPlayer[] }

interface MatchInfo {
  id: number;
  datetime: string;
  home_goals: number | null;
  away_goals: number | null;
  home_xg: number;
  away_xg: number;
  home_team: string;
  away_team: string;
}

interface LineupData { match: MatchInfo; home: TeamLineup; away: TeamLineup }
type Plotted = StarterPlayer & { px: number; py: number };

// ─── Spatial position map ─────────────────────────────────────────────────────
const POS_MAP: Record<string, { bx: number; zone: number }> = {
  GK:  { bx: 50, zone: 0 },
  DL:  { bx: 10, zone: 1 }, DC: { bx: 50, zone: 1 }, DR: { bx: 90, zone: 1 },
  DML: { bx: 20, zone: 1 }, DMR: { bx: 80, zone: 1 },
  DMC: { bx: 50, zone: 2 }, ML: { bx: 13, zone: 2 }, MC: { bx: 50, zone: 2 }, MR: { bx: 87, zone: 2 },
  AML: { bx: 20, zone: 3 }, AMC: { bx: 50, zone: 3 }, AMR: { bx: 80, zone: 3 },
  FWL: { bx: 27, zone: 4 }, FW: { bx: 50, zone: 4 }, FWR: { bx: 73, zone: 4 },
};

const HOME_ZONE_Y: number[] = [88, 74, 59, 45, 31];
const AWAY_ZONE_Y: number[] = [12, 26, 41, 55, 69];

function computeLayout(starters: StarterPlayer[], isHome: boolean): Plotted[] {
  const zones: Record<number, Array<StarterPlayer & { bx: number }>> = {};
  for (const p of starters) {
    const d = POS_MAP[(p.position ?? "").toUpperCase()] ?? { bx: 50, zone: 2 };
    (zones[d.zone] ||= []).push({ ...p, bx: d.bx });
  }
  const yArr = isHome ? HOME_ZONE_Y : AWAY_ZONE_Y;
  const result: Plotted[] = [];
  for (const [zStr, players] of Object.entries(zones)) {
    const zone = +zStr;
    const py = yArr[zone] ?? 50;
    const n = players.length;
    players.sort((a, b) => a.bx - b.bx);
    players.forEach((p, i) => {
      const px = n === 1 ? p.bx : 10 + (80 / (n - 1)) * i;
      result.push({ ...p, px, py });
    });
  }
  return result;
}

function abbrevName(full: string): string {
  const parts = full.trim().split(/\s+/);
  if (parts.length < 2) return full;
  return `${parts[0][0].toUpperCase()}. ${parts.slice(1).join(" ")}`;
}

const HOME_CIRCLE = "#7ab4dc";
const AWAY_CIRCLE = "#1c1c1c";

function PlayerNode({ p, isHome }: { p: Plotted; isHome: boolean }) {
  const bg   = isHome ? HOME_CIRCLE : AWAY_CIRCLE;
  const abbr = (p.position ?? "").toUpperCase().replace(/[0-9]/g, "").slice(0, 3);

  return (
    <div
      style={{
        position:  "absolute",
        left:      `${p.px}%`,
        top:       `${p.py}%`,
        transform: "translate(-50%, -50%)",
        zIndex:    10,
        width:     76,
        display:   "flex",
        flexDirection: "column",
        alignItems:    "center",
      }}
    >
      <div style={{ position: "relative", marginBottom: 3 }}>
        <div style={{
          width:        44,
          height:       44,
          borderRadius: "50%",
          background:   bg,
          boxShadow:    "0 2px 8px rgba(0,0,0,0.35)",
          display:      "flex",
          alignItems:   "center",
          justifyContent: "center",
        }}>
          <span style={{
            color:      "#fff",
            fontSize:   10,
            fontWeight: 700,
            letterSpacing: 0.3,
            fontFamily: "monospace",
            lineHeight: 1,
          }}>
            {abbr}
          </span>
        </div>

        {p.goals > 0 && (
          <span style={{
            position:  "absolute",
            top:       -6,
            left:      -8,
            fontSize:  16,
            lineHeight: 1,
            filter:    "drop-shadow(0 1px 2px rgba(0,0,0,0.5))",
          }}>
            ⚽
          </span>
        )}

        {p.yellow_card && !p.red_card && (
          <span style={{
            position:     "absolute",
            top:          -5,
            right:        -5,
            display:      "block",
            width:        9,
            height:       13,
            borderRadius: 2,
            background:   "#FFD700",
            border:       "1px solid rgba(0,0,0,0.25)",
            boxShadow:    "0 1px 3px rgba(0,0,0,0.35)",
          }} />
        )}

        {p.red_card && (
          <span style={{
            position:     "absolute",
            top:          -5,
            right:        -5,
            display:      "block",
            width:        9,
            height:       13,
            borderRadius: 2,
            background:   "#e53935",
            boxShadow:    "0 1px 3px rgba(0,0,0,0.4)",
          }} />
        )}

        {p.sub_in && (
          <span style={{
            position:     "absolute",
            bottom:       -4,
            right:        -4,
            width:        14,
            height:       14,
            borderRadius: "50%",
            background:   "#fff",
            border:       "1px solid rgba(0,0,0,0.15)",
            boxShadow:    "0 1px 3px rgba(0,0,0,0.3)",
            display:      "flex",
            alignItems:   "center",
            justifyContent: "center",
          }}>
            <svg width="7" height="7" viewBox="0 0 7 7" fill="none">
              <path d="M3.5 0v5M1 3l2.5 3 2.5-3" stroke="#e53935" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </span>
        )}
      </div>

      <span style={{
        fontSize:      11,
        fontWeight:    600,
        color:         "#111",
        lineHeight:    1.2,
        textAlign:     "center",
        whiteSpace:    "nowrap",
        overflow:      "hidden",
        textOverflow:  "ellipsis",
        maxWidth:      76,
        textShadow:    "0 1px 0 rgba(255,255,255,0.55)",
      }}>
        {abbrevName(p.name)}
      </span>
    </div>
  );
}

function PitchSVG() {
  const line  = "rgba(255,255,255,0.78)";
  const faint = "rgba(255,255,255,0.48)";
  return (
    <svg
      style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none" }}
      viewBox="0 0 100 155"
      preserveAspectRatio="none"
    >
      <rect x="3" y="2.5" width="94" height="150" fill="none" stroke={line} strokeWidth="0.7" />
      <line x1="3" y1="77.5" x2="97" y2="77.5" stroke={line} strokeWidth="0.6" />
      <circle cx="50" cy="77.5" r="12.5" fill="none" stroke={faint} strokeWidth="0.55" />
      <circle cx="50" cy="77.5" r="1.2" fill={line} />
      <rect x="22" y="2.5" width="56" height="20" fill="none" stroke={faint} strokeWidth="0.55" />
      <rect x="35" y="2.5" width="30" height="8.5" fill="none" stroke={faint} strokeWidth="0.45" />
      <rect x="43.5" y="2.5" width="13" height="2.8"  fill="none" stroke={line} strokeWidth="0.65" />
      <circle cx="50" cy="15" r="0.9" fill={faint} />
      <path d="M 31 22.5 A 14 13 0 0 0 69 22.5" fill="none" stroke={faint} strokeWidth="0.48" />
      <rect x="22" y="132.5" width="56" height="20" fill="none" stroke={faint} strokeWidth="0.55" />
      <rect x="35" y="144" width="30" height="8.5" fill="none" stroke={faint} strokeWidth="0.45" />
      <rect x="43.5" y="149.7" width="13" height="2.8" fill="none" stroke={line} strokeWidth="0.65" />
      <circle cx="50" cy="140" r="0.9" fill={faint} />
      <path d="M 31 132.5 A 14 13 0 0 1 69 132.5" fill="none" stroke={faint} strokeWidth="0.48" />
    </svg>
  );
}

function EmptyState({ msg }: { msg: string }) {
  return (
    <div style={{
      height: 520,
      borderRadius: 8,
      background: "linear-gradient(180deg,#4caf6e,#3d9a5e,#4caf6e)",
      display: "flex", alignItems: "center", justifyContent: "center",
    }}>
      <span style={{ fontFamily: "monospace", fontSize: 11, color: "rgba(255,255,255,0.45)", letterSpacing: 3 }}>
        {msg.toUpperCase()}
      </span>
    </div>
  );
}

export default function MatchLineupPitch({ matchId }: { matchId: number | string }) {
  const { t } = useTranslation();
  const [data, setData]       = useState<LineupData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(false);

  useEffect(() => {
    if (!matchId) return;
    setLoading(true);
    setError(false);
    fetch(`${API}/api/scout/match/${matchId}/lineup`)
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(d  => { setData(d); setLoading(false); })
      .catch(() => { setError(true); setLoading(false); });
  }, [matchId]);

  if (loading)        return <EmptyState msg={t("scout.lineup_loading")} />;
  if (error || !data) return <EmptyState msg={t("scout.lineup_unavailable")} />;

  const homePlotted = computeLayout(data.home.starters, true);
  const awayPlotted = computeLayout(data.away.starters, false);
  const m = data.match;

  return (
    <div suppressHydrationWarning style={{ borderRadius: 8, overflow: "hidden", background: "#fff", fontFamily: "sans-serif" }}>
      <div style={{
        display: "grid",
        gridTemplateColumns: "1fr auto 1fr",
        alignItems: "center",
        gap: 12,
        padding: "14px 18px 12px",
        background: "#fff",
        borderBottom: "1px solid #e5e7eb",
      }}>
        <div>
          <p style={{ fontWeight: 800, fontSize: 13, color: "#111", margin: 0, lineHeight: 1.3 }}>
            {m.home_team}
          </p>
          <p style={{ fontSize: 10, color: "#9ca3af", fontFamily: "monospace", margin: "2px 0 0" }}>
            xG {m.home_xg.toFixed(2)}
          </p>
        </div>

        <div style={{ textAlign: "center" }}>
          <p style={{
            fontSize: 30, fontWeight: 900, fontFamily: "monospace",
            color: "#111", margin: 0, lineHeight: 1, letterSpacing: -1,
          }}>
            {m.home_goals ?? "–"}&thinsp;–&thinsp;{m.away_goals ?? "–"}
          </p>
        </div>

        <div style={{ textAlign: "right" }}>
          <p style={{ fontWeight: 800, fontSize: 13, color: "#111", margin: 0, lineHeight: 1.3 }}>
            {m.away_team}
          </p>
          <p style={{ fontSize: 10, color: "#9ca3af", fontFamily: "monospace", margin: "2px 0 0" }}>
            xG {m.away_xg.toFixed(2)}
          </p>
        </div>
      </div>

      <div style={{
        position:     "relative",
        width:        "100%",
        paddingBottom:"155%",
        background:   "linear-gradient(180deg, #4caf6e 0%, #3d9a5e 50%, #4caf6e 100%)",
      }}>
        <PitchSVG />
        <div style={{ position: "absolute", inset: 0 }}>
          {homePlotted.map((p, i) => <PlayerNode key={`h${i}`} p={p} isHome />)}
          {awayPlotted.map((p, i) => <PlayerNode key={`a${i}`} p={p} isHome={false} />)}
        </div>
      </div>

      <div style={{
        display:    "flex",
        flexWrap:   "wrap",
        alignItems: "center",
        gap:        "12px 20px",
        padding:    "10px 16px",
        borderTop:  "1px solid #f3f4f6",
        background: "#fff",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ width: 14, height: 14, borderRadius: "50%", background: HOME_CIRCLE }} />
          <span style={{ fontSize: 10, color: "#6b7280" }}>{m.home_team}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ width: 14, height: 14, borderRadius: "50%", background: AWAY_CIRCLE }} />
          <span style={{ fontSize: 10, color: "#6b7280" }}>{m.away_team}</span>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", gap: 16, alignItems: "center" }}>
          {[
            { el: <span style={{ display:"inline-block", width:8, height:11, borderRadius:2, background:"#FFD700" }} />, label: "Yellow" },
            { el: <span style={{ display:"inline-block", width:8, height:11, borderRadius:2, background:"#e53935" }} />, label: "Red" },
            { el: <span style={{ fontSize: 13 }}>⚽</span>, label: "Goal" },
            { el: <span style={{ color:"#e53935", fontWeight:700, fontSize:11 }}>↓</span>, label: "Sub" },
          ].map(({ el, label }) => (
            <div key={label} style={{ display:"flex", alignItems:"center", gap: 5 }}>
              {el}
              <span style={{ fontSize: 10, color: "#9ca3af" }}>{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}