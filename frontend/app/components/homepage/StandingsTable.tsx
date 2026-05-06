import React from 'react';
import { serieAStandings, TeamStanding } from '../../lib/mockData';

export interface StandingsTableProps {
  league?: string;
  season?: string;
}

const StandingsTable: React.FC<StandingsTableProps> = ({
  league = 'Serie A',
  season = '2023-24',
}) => {
  // Take top 8 Serie A teams plus Palermo row (if not already in top 8)
  const top8 = serieAStandings.slice(0, 8);
  const palermoRow = serieAStandings.find((row) => row.isPalermo);
  const rows = palermoRow && !top8.includes(palermoRow) 
    ? [...top8, palermoRow] 
    : top8;

  return (
    <section className="standings-table p-6 bg-white rounded-xl shadow-lg">
      <header className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">
          {league} Standings <span className="text-gray-500">({season})</span>
        </h2>
        <select className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
          <option>Serie A</option>
          <option>Serie B</option>
          <option>Premier League</option>
          <option>La Liga</option>
        </select>
      </header>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b-2 border-gray-200">
              <th className="py-3 px-4 font-semibold text-gray-700">Pos</th>
              <th className="py-3 px-4 font-semibold text-gray-700">Team</th>
              <th className="py-3 px-4 font-semibold text-gray-700 text-center">P</th>
              <th className="py-3 px-4 font-semibold text-gray-700 text-center">W</th>
              <th className="py-3 px-4 font-semibold text-gray-700 text-center">D</th>
              <th className="py-3 px-4 font-semibold text-gray-700 text-center">L</th>
              <th className="py-3 px-4 font-semibold text-gray-700 text-center">Pts</th>
              <th className="py-3 px-4 font-semibold text-gray-700 text-center">Form</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.position}
                className={`border-b border-gray-100 hover:bg-gray-50 ${
                  row.position <= 3 ? 'bg-blue-50' : ''
                } ${
                  row.isPalermo ? 'bg-palermo-pink/10 border-l-4 border-palermo-pink' : ''
                }`}
              >
                <td className="py-3 px-4 font-bold">{row.position}</td>
                <td className="py-3 px-4 font-semibold">{row.team}</td>
                <td className="py-3 px-4 text-center">{row.played}</td>
                <td className="py-3 px-4 text-center">{row.won}</td>
                <td className="py-3 px-4 text-center">{row.drawn}</td>
                <td className="py-3 px-4 text-center">{row.lost}</td>
                <td className="py-3 px-4 text-center font-bold">{row.points}</td>
                <td className="py-3 px-4 text-center">
                  <div className="flex justify-center space-x-1">
                    {row.form.map((result, idx) => (
                      <span
                        key={idx}
                        className={`w-6 h-6 flex items-center justify-center rounded-full text-xs font-bold ${
                          result === 'W'
                            ? 'bg-green-100 text-green-800'
                            : result === 'D'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {result}
                      </span>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-4 border border-gray-200 rounded-lg">
          <h3 className="font-bold mb-2">Champions League Spots</h3>
          <p className="text-gray-600 text-sm">
            Top 4 qualify for UEFA Champions League, 5th–7th enter Europa competitions.
          </p>
        </div>
        <div className="p-4 border border-gray-200 rounded-lg">
          <h3 className="font-bold mb-2">Last Updated</h3>
          <p className="text-gray-600 text-sm">Data updated after Matchday 28.</p>
        </div>
        <div className="p-4 border border-gray-200 rounded-lg">
          <h3 className="font-bold mb-2">Full Table</h3>
          <button className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors">
            View Complete Standings
          </button>
        </div>
      </div>
    </section>
  );
};

export default StandingsTable;