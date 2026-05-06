"use client";

import React from "react";
import MatchRosterList from "./MatchRosterList";

/* ─── Types (kept for backward compat) ─── */
export interface LineupPlayer {
  name: string;
  position: string;
  minutes: number;
  xG: number;
  xA: number;
  goals: number;
  assists: number;
  substitution?: { minute: number; player_in: string };
}

export interface TeamLineup {
  name: string;
  goals: number;
  starters: LineupPlayer[];
  bench: LineupPlayer[];
  substitutions: { player_out: string; player_in: string; minute: number }[];
}

export interface LineupData {
  match_id: number;
  teams: { home?: TeamLineup; away?: TeamLineup };
}

/* ─── Main Component ─── */
interface MatchLineupPitchProps {
  data?: LineupData;
  matchId?: number | string;
  teamType?: "home" | "away";
  showBothTeams?: boolean;
}

/**
 * DEPRECATED – visual pitch removed due to inaccurate positional data.
 * Now delegates to MatchRosterList for a clean dual-column roster display.
 */
export default function MatchLineupPitch(props: MatchLineupPitchProps) {
  const { matchId } = props;

  if (!matchId) {
    return (
      <div className="text-center py-8 text-sm text-white/30">
        Formazioni non disponibili.
      </div>
    );
  }

  return <MatchRosterList matchId={matchId} />;
}
