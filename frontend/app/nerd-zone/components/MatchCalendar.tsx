"use client";

interface Match {
  match_id: number;
  date: string;
  home_team: string;
  away_team: string;
  home_team_id: number;
  away_team_id: number;
  home_goals: number | null;
  away_goals: number | null;
  home_xg: number | null;
  away_xg: number | null;
  is_completed: boolean;
  matchday: number | null;
  is_home: boolean;
}

interface Props {
  matches: Match[];
  teamId: number;
}

function matchResult(m: Match, teamId: number): "W" | "D" | "L" | null {
  if (!m.is_completed || m.home_goals == null || m.away_goals == null) return null;
  const isHome = m.home_team_id === teamId;
  const gf = isHome ? m.home_goals : m.away_goals;
  const ga = isHome ? m.away_goals : m.home_goals;
  if (gf > ga) return "W";
  if (gf < ga) return "L";
  return "D";
}

const RESULT_BG: Record<string, string> = {
  W: "#10B981",
  D: "#f59e0b",
  L: "#EF4444",
};

export default function MatchCalendar({ matches, teamId }: Props) {
  // Sort ascending by date for calendar display
  const sorted = [...matches].sort((a, b) => a.date.localeCompare(b.date));

  return (
    <div className="overflow-x-auto pb-2" style={{ scrollbarWidth: "thin" }}>
      <div className="flex gap-2 min-w-max">
        {sorted.map(m => {
          const isHome   = m.home_team_id === teamId;
          const opponent = isHome ? m.away_team : m.home_team;
          const result   = matchResult(m, teamId);
          const gf       = m.is_completed ? (isHome ? m.home_goals : m.away_goals) : null;
          const ga       = m.is_completed ? (isHome ? m.away_goals : m.home_goals) : null;
          const xgf      = isHome ? m.home_xg : m.away_xg;
          const xga      = isHome ? m.away_xg : m.home_xg;

          const dateStr  = m.date
            ? new Date(m.date).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "2-digit" })
            : "—";

          const badgeColor = result ? RESULT_BG[result] : "#475569";
          const badgeBg    = result ? badgeColor + "22" : "#1e293b";

          return (
            <div
              key={m.match_id}
              className="flex-shrink-0 w-[130px] border border-slate-800/60 rounded-xl bg-[#0a0c14] hover:bg-[#0d1220] transition-colors p-3 flex flex-col gap-1.5"
            >
              {/* Date + H/A badge */}
              <div className="flex items-center justify-between gap-1">
                <span
                  className="text-[10px] font-black"
                  style={{ color: result ? badgeColor : "#94a3b8" }}
                >
                  {dateStr}
                </span>
                <span
                  className="text-[9px] font-black px-1.5 py-0.5 rounded"
                  style={{ background: badgeBg, color: badgeColor, border: `1px solid ${badgeColor}40` }}
                >
                  {isHome ? "H" : "A"}
                </span>
              </div>

              {/* Score or time */}
              {m.is_completed && gf != null && ga != null ? (
                <div className="flex flex-col items-center">
                  <div className="flex items-center gap-2 font-black text-xl tabular-nums">
                    <span style={{ color: gf > ga ? "#10B981" : gf < ga ? "#EF4444" : "#94a3b8" }}>{gf}</span>
                    <span className="text-slate-700 text-sm">—</span>
                    <span style={{ color: ga > gf ? "#10B981" : ga < gf ? "#EF4444" : "#94a3b8" }}>{ga}</span>
                  </div>
                  {/* xG row */}
                  {xgf != null && xga != null && (
                    <div className="flex items-center gap-2 font-mono text-[9px] text-slate-600 mt-0.5">
                      <span>{xgf.toFixed(2)}</span>
                      <span>·</span>
                      <span>{xga.toFixed(2)}</span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center text-slate-600 font-mono text-sm">
                  {m.date
                    ? new Date(m.date).toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" })
                    : "TBD"}
                </div>
              )}

              {/* Opponent */}
              <div className="text-center text-[11px] text-slate-400 font-medium truncate">
                {opponent}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
