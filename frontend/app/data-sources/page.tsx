import Link from 'next/link';

export const metadata = {
  title: 'Fonti Dati | Barsport.club',
  description: 'Fonti dei dati utilizzati su Barsport.club',
};

export default function DataSourcesPage() {
  return (
    <div className="min-h-screen bg-[#0A192F] text-white p-8">
      <div className="max-w-2xl mx-auto">
        <Link href="/" className="text-[#FF2A6D] hover:underline text-sm">
          ← Back
        </Link>
        <h1 className="text-3xl font-bold mt-6 mb-4">Fonti Dati</h1>
        <p className="text-slate-300 leading-relaxed">
          I dati relativi agli Expected Goals (xG) e alle statistiche delle partite sono forniti da{' '}
          <a
            href="https://understat.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[#FF2A6D] hover:underline"
          >
            Understat.com
          </a>
          , una piattaforma terza di analisi calcistica avanzata. I restanti dati provengono da fonti
          pubbliche ufficiali e API di statistiche sportive.
        </p>
        <p className="text-slate-400 text-sm mt-4">
          Questo sito è un progetto amatoriale senza scopo di lucro. Tutti i marchi appartengono ai
          rispettivi proprietari.
        </p>
      </div>
    </div>
  );
}
