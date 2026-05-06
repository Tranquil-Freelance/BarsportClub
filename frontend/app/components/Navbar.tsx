"use client";

import React, { useState, useEffect } from 'react';
import { useTranslation } from "react-i18next";
import "../i18n/config";
import { mockMatches, mockLeagues, mockTeams } from '../lib/mockData';

interface Match {
  id: number;
  home_team: string;
  away_team: string;
}

interface NavbarProps {
  selectedMatchId: number | null;
  setSelectedMatchId: (id: number | null) => void;
  selectedLeague: string | null;
  setSelectedLeague: (league: string | null) => void;
  selectedTeam: string | null;
  setSelectedTeam: (team: string | null) => void;
}

const Navbar: React.FC<NavbarProps> = ({ selectedMatchId, setSelectedMatchId, selectedLeague, setSelectedLeague, selectedTeam, setSelectedTeam }) => {
  const { t } = useTranslation();
  const [availableMatches, setAvailableMatches] = useState<Match[]>([]);

  useEffect(() => {
    // Temporarily use mock data while backend is unavailable
    setAvailableMatches(mockMatches);
  }, []);

  const [leagues, setLeagues] = useState<{ id: number; name: string; understat_slug: string }[]>([]);
  const [teams, setTeams] = useState<{ id: number; name: string; league_id: number }[]>([]);

  useEffect(() => {
    // Temporarily use mock data while backend is unavailable
    setLeagues(mockLeagues);
  }, []);

  useEffect(() => {
    if (selectedLeague) {
      const league = mockLeagues.find(l => l.name === selectedLeague);
      if (league) {
        const filteredTeams = mockTeams.filter(t => t.league_id === league.id);
        setTeams(filteredTeams);
      }
    } else {
      setTeams([]);
    }
  }, [selectedLeague]);

  const handleMatchChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    const matchId = value === '' ? null : parseInt(value, 10);
    setSelectedMatchId(matchId);
  };

  const handleLeagueChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const league = event.target.value;
    setSelectedLeague(league || null);
    setSelectedTeam(null);
  };

  const handleTeamChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const team = event.target.value;
    setSelectedTeam(team || null);
  };

  return (
    <nav className="bg-palermo-dark text-white border-b border-zinc-800" suppressHydrationWarning>
      <div className="px-14 h-20 flex justify-between items-center">

        <div className="flex items-center gap-4">
          <div className="w-10 h-10 bg-palermo-pink flex items-center justify-center rotate-45">
            <div className="w-5 h-5 bg-palermo-dark -rotate-45"></div>
          </div>
          <span className="font-heading text-3xl tracking-wide uppercase font-bold">Palermo</span>
        </div>

        <div className="flex gap-7 text-[13px] uppercase font-heading tracking-wider h-full items-center">
          <span className="h-full flex items-center border-b-2 border-palermo-pink text-white pt-1 cursor-pointer">{t('nav.home')}</span>
          <span className="h-full flex items-center text-zinc-400 hover:text-white transition pt-1 cursor-pointer">{t('nav.analysis')}</span>
          <span className="h-full flex items-center text-zinc-400 hover:text-white transition pt-1 cursor-pointer">{t('nav.stats')}</span>
          <span className="h-full flex items-center text-zinc-400 hover:text-white transition pt-1 cursor-pointer">{t('nav.tactics')}</span>
          <select
            value={selectedLeague ?? ''}
            onChange={handleLeagueChange}
            className="h-full bg-transparent border-none text-zinc-400 hover:text-palermo-pink transition pt-1 cursor-pointer focus:outline-none"
          >
            <option value="">{t('navbar.select_league')}</option>
            {leagues.map(league => (
              <option key={league.id} value={league.name}>
                {league.name}
              </option>
            ))}
          </select>
          <select
            value={selectedTeam ?? ''}
            onChange={handleTeamChange}
            disabled={!selectedLeague}
            className="h-full bg-transparent border-none text-zinc-400 hover:text-palermo-pink transition pt-1 cursor-pointer focus:outline-none disabled:opacity-50"
          >
            <option value="">{t('navbar.select_team')}</option>
            {teams.map(team => (
              <option key={team.id} value={team.name}>
                {team.name}
              </option>
            ))}
          </select>
          <span className="h-full flex items-center text-zinc-400 hover:text-white transition pt-1 cursor-pointer">{t('nav.news')}</span>
        </div>

        <div className="flex items-center gap-4">
          <select
            value={selectedMatchId ?? ''}
            onChange={handleMatchChange}
            className="bg-palermo-dark border border-zinc-700 text-white text-sm px-3 py-2 rounded focus:outline-none focus:ring-1 focus:ring-palermo-pink"
          >
            <option value="">{t('navbar.select_match')}</option>
            {availableMatches.map(match => (
              <option key={match.id} value={match.id}>
                {match.home_team} vs {match.away_team}
              </option>
            ))}
          </select>
          <button className="bg-palermo-pink text-white font-heading uppercase px-5 py-2.5 text-xs font-bold tracking-wider hover:bg-pink-600 transition shadow-lg">
            {t('navbar.match_report')}
          </button>
        </div>

      </div>
    </nav>
  );
};

export default Navbar;
