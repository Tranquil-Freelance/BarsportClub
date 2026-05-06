"use client";

import { useState, useMemo } from "react";
import { Search, ChevronUp, ChevronDown } from "lucide-react";

export interface PlayerData {
  id: number;
  rank: number;
  name: string;
  team: string;
  goals: number;
  xG: number;
  assists: number;
  xA: number;
  // total is xG + xA
}

interface PlayerTableProps {
  players: PlayerData[];
}

type SortColumn = keyof Omit<PlayerData, "id"> | "total";
type SortDirection = "asc" | "desc";

export default function PlayerTable({ players }: PlayerTableProps) {
  const [search, setSearch] = useState("");
  const [sortColumn, setSortColumn] = useState<SortColumn>("rank");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  // Compute total for each player
  const playersWithTotal = useMemo(
    () =>
      players.map((p) => ({
        ...p,
        total: p.xG + p.xA,
      })),
    [players]
  );

  // Filter by player name or team
  const filteredPlayers = useMemo(() => {
    if (!search.trim()) return playersWithTotal;
    const term = search.toLowerCase();
    return playersWithTotal.filter(
      (p) =>
        p.name.toLowerCase().includes(term) ||
        p.team.toLowerCase().includes(term)
    );
  }, [playersWithTotal, search]);

  // Sorting
  const sortedPlayers = useMemo(() => {
    return [...filteredPlayers].sort((a, b) => {
      let aVal = a[sortColumn as keyof typeof a];
      let bVal = b[sortColumn as keyof typeof b];

      if (sortColumn === "total") {
        aVal = a.xG + a.xA;
        bVal = b.xG + b.xA;
      }

      if (typeof aVal === "string" && typeof bVal === "string") {
        return sortDirection === "asc"
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }
      // numeric comparison
      const aNum = Number(aVal);
      const bNum = Number(bVal);
      return sortDirection === "asc" ? aNum - bNum : bNum - aNum;
    });
  }, [filteredPlayers, sortColumn, sortDirection]);

  const handleSort = (column: SortColumn) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortColumn(column);
      setSortDirection("asc");
    }
  };

  const renderSortIcon = (column: SortColumn) => {
    if (sortColumn !== column) return null;
    return sortDirection === "asc" ? (
      <ChevronUp className="ml-1 h-4 w-4" />
    ) : (
      <ChevronDown className="ml-1 h-4 w-4" />
    );
  };

  const formatNumber = (value: number, decimals: number = 2) => {
    return Number(value.toFixed(decimals)).toLocaleString();
  };

  return (
    <div className="w-full">
      {/* Search Bar */}
      <div className="mb-6 flex items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search player or team..."
            className="w-full rounded-lg border border-slate-300 bg-white py-3 pl-10 pr-4 text-slate-900 shadow-sm focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/30 focus:outline-none"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="text-sm text-slate-500">
          Showing <span className="font-semibold text-emerald-700">{sortedPlayers.length}</span>{" "}
          of {players.length} players
        </div>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-slate-200 shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-gradient-to-r from-slate-800 to-emerald-900">
              <tr>
                {[
                  { key: "rank", label: "Rank" },
                  { key: "name", label: "Player Name" },
                  { key: "team", label: "Team" },
                  { key: "goals", label: "Goals" },
                  { key: "xG", label: "xG" },
                  { key: "assists", label: "Assists" },
                  { key: "xA", label: "xA" },
                  { key: "total", label: "Total (xG + xA)" },
                ].map((col) => (
                  <th
                    key={col.key}
                    scope="col"
                    className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-white cursor-pointer select-none hover:bg-slate-800/80 transition-colors"
                    onClick={() => handleSort(col.key as SortColumn)}
                  >
                    <div className="flex items-center">
                      {col.label}
                      {renderSortIcon(col.key as SortColumn)}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {sortedPlayers.length > 0 ? (
                sortedPlayers.map((player) => (
                  <tr
                    key={player.id}
                    className="hover:bg-slate-50 transition-colors"
                  >
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="flex items-center">
                        <span
                          className={`inline-flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold ${
                            player.rank <= 3
                              ? "bg-gradient-to-br from-amber-100 to-amber-300 text-amber-900"
                              : "bg-slate-100 text-slate-700"
                          }`}
                        >
                          {player.rank}
                        </span>
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="text-sm font-semibold text-slate-900">
                        {player.name}
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="text-sm text-slate-700">{player.team}</div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="text-center text-lg font-bold text-slate-900">
                        {player.goals}
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="text-center">
                        <span className="text-sm font-medium text-slate-900">
                          {formatNumber(player.xG)}
                        </span>
                        <div
                          className={`text-xs ${
                            player.xG > player.goals
                              ? "text-rose-600"
                              : "text-emerald-600"
                          }`}
                        >
                          {player.xG > player.goals ? "Overperforming" : "Underperforming"}
                        </div>
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="text-center text-lg font-bold text-slate-900">
                        {player.assists}
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="text-center">
                        <span className="text-sm font-medium text-slate-900">
                          {formatNumber(player.xA)}
                        </span>
                        <div
                          className={`text-xs ${
                            player.xA > player.assists
                              ? "text-rose-600"
                              : "text-emerald-600"
                          }`}
                        >
                          {player.xA > player.assists ? "Overperforming" : "Underperforming"}
                        </div>
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="text-center">
                        <span className="text-lg font-bold text-emerald-800">
                          {formatNumber(player.xG + player.xA)}
                        </span>
                        <div className="text-xs text-slate-500">xG + xA</div>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center">
                    <div className="text-slate-500">No players found matching your search.</div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-6 flex flex-wrap items-center justify-between text-sm text-slate-600">
        <div className="flex items-center space-x-4">
          <div className="flex items-center">
            <div className="mr-2 h-3 w-3 rounded-full bg-gradient-to-r from-emerald-500 to-cyan-400"></div>
            <span>Advanced Analytics Engine metrics</span>
          </div>
          <div className="flex items-center">
            <div className="mr-2 h-3 w-3 rounded-full bg-amber-300"></div>
            <span>Top 3 rank highlight</span>
          </div>
        </div>
        <div>
          <span className="font-medium">xG</span>: Expected Goals |{" "}
          <span className="font-medium">xA</span>: Expected Assists
        </div>
      </div>
    </div>
  );
}