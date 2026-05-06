import SquadraClientWrapper from "../components/SquadraClientWrapper";

// Same 8 teams as homepage strip
const VALID_SQUADRE = [
  "sassuolo", "como", "atalanta", "palermo",
  "fiorentina", "lecce", "parma", "torino",
];

// Capitalize first letter for display
const NAMES: Record<string, string> = {
  sassuolo: "Sassuolo", como: "Como", atalanta: "Atalanta",
  palermo: "Palermo", fiorentina: "Fiorentina",
  lecce: "Lecce", parma: "Parma", torino: "Torino",
};

// Mockup files that exist in public/mockup/
// NOTE: fiorentina-full-mockup.png is missing — add it to show Fiorentina mockup
const EXISTING_MOCKUPS = new Set([
  "sassuolo", "como", "atalanta", "palermo",
  "lecce", "parma", "torino",
]);

export function generateStaticParams() {
  return VALID_SQUADRE.map((squadra) => ({ squadra }));
}

export default function SquadraMockupPage({
  params,
}: {
  params: { squadra: string };
}) {
  const { squadra } = params;

  if (!VALID_SQUADRE.includes(squadra)) {
    throw new Error(`Invalid squadra: ${squadra}`);
  }

  const name = NAMES[squadra];
  const hasMockup = EXISTING_MOCKUPS.has(squadra);

  return (
    <SquadraClientWrapper
      squadra={squadra}
      name={name}
      hasMockup={hasMockup}
    />
  );
}
