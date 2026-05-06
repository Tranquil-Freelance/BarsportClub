import Link from 'next/link';

export interface Match {
  id: number;
  home_team: string;
  away_team: string;
}

interface MatchWidgetProps {
  match: Match;
}

export default function MatchWidget({ match }: MatchWidgetProps) {
  return (
    <div className="bg-gradient-to-br from-como-blue to-como-dark text-white rounded-2xl p-6 shadow-2xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-2xl font-bold">Ultima Partita</h3>
          <p className="text-como-white/80">Dati analytics avanzati</p>
        </div>
        <div className="bg-white/10 rounded-full p-3">
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
      </div>

      <div className="bg-white/10 rounded-xl p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="text-center flex-1">
            <div className="text-3xl font-bold">{match.home_team}</div>
            <div className="text-sm text-como-white/60">Home</div>
          </div>
          <div className="mx-6">
            <div className="text-5xl font-black">vs</div>
          </div>
          <div className="text-center flex-1">
            <div className="text-3xl font-bold">{match.away_team}</div>
            <div className="text-sm text-como-white/60">Away</div>
          </div>
        </div>
        <div className="mt-6 text-center text-como-white/80">
          Match ID: <span className="font-mono font-bold">{match.id}</span>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-4">
        <Link
          href={`/matches/${match.id}`}
          className="flex-1 bg-white text-como-blue font-bold py-3 px-6 rounded-lg text-center hover:bg-gray-100 transition-colors"
        >
          Vedi Tactical Board
        </Link>
        <button className="flex-1 bg-transparent border-2 border-white text-white font-bold py-3 px-6 rounded-lg hover:bg-white/10 transition-colors">
          Dettagli Match
        </button>
      </div>
    </div>
  );
}