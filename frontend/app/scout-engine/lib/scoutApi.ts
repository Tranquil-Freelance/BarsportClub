export const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Suggestion { name: string; team: string; }

export interface Scores {
  OIS: number; CII: number; AIR: number; BCS: number;
  FES: number; PIR: number; MVGI: number; PPI: number;
}

export interface PlayerDNA {
  name: string; team: string; position: string;
  games: number; minutes: number;
  totals: Record<string, number>;
  p90: Record<string, number>;
  scores: Scores;
}

export interface AxisData { label: string; value: number; percentile: number; }

export interface RadarData {
  player: PlayerDNA;
  percentiles: Record<string, number>;
  axes: Record<string, AxisData>;
  pool_size: number;
}

export interface Replacement extends PlayerDNA { similarity: number; similarity_pct: number; }
export interface ReplacementData { target: PlayerDNA; substitutes: Replacement[]; }

export interface Leader { name: string; team: string; value: number; stat: string; }
export interface Leaders { scorers: Leader[]; architects: Leader[]; }

export interface Shot {
  X: number; Y: number; xG: number;
  result: string; minute: number; situation: string; shotType?: string;
}

export type TalentCategory = "diamonds" | "moneyball" | "engine" | "unlucky" | "overperformers";
export type LeagueKey = "serie_a" | "pl" | "bundesliga" | "liga" | "ligue1";

export const LEAGUE_LABELS: Record<LeagueKey, string> = {
  serie_a:    "Serie A",
  pl:         "Premier League",
  bundesliga: "Bundesliga",
  liga:       "La Liga",
  ligue1:     "Ligue 1",
};

export const CATEGORY_META: Record<TalentCategory, { emoji: string; label: string; desc: string; color: string; heroMetric: string }> = {
  diamonds:      { emoji: "💎", label: "Hidden Diamonds", desc: "High xGChain, limited minutes", color: "#00D1FF", heroMetric: "xGChain/90" },
  moneyball:     { emoji: "💰", label: "Moneyball",       desc: "High xGBuildup, low xG total",  color: "#10B981", heroMetric: "xGBuildup/90" },
  engine:        { emoji: "🚜", label: "Engine Room",     desc: "High key passes + xGBuildup",   color: "#F59E0B", heroMetric: "xGBuildup/90" },
  unlucky:       { emoji: "🎯", label: "Unlucky Masters", desc: "High xG, almost no goals",      color: "#8B5CF6", heroMetric: "xG Total" },
  overperformers:{ emoji: "🔥", label: "Overperformers",  desc: "Goals far exceed xG",           color: "#FF2A6D", heroMetric: "Goals − xG" },
};

export async function fetchSearch(q: string): Promise<Suggestion[]> {
  const r = await fetch(`${API}/api/scout/search?q=${encodeURIComponent(q)}`);
  const d = await r.json();
  const toSuggestion = (x: any): Suggestion => ({
    name: typeof x === "string" ? x : (x.name ?? String(x)),
    team: typeof x === "string" ? "" : (x.team ?? ""),
  });
  const list: any[] = d.results ?? (Array.isArray(d) ? d : []);
  return list.map(toSuggestion);
}

export async function fetchPlayerDNA(name: string): Promise<PlayerDNA | null> {
  const r = await fetch(`${API}/api/scout/dna?player_name=${encodeURIComponent(name)}`);
  const d = await r.json();
  return d.dna ?? null;
}

export async function fetchPlayerRadar(name: string): Promise<RadarData | null> {
  const r = await fetch(`${API}/api/scout/radar?player_name=${encodeURIComponent(name)}`);
  const d = await r.json();
  return d.radar ?? null;
}

export async function fetchPlayerShots(name: string): Promise<Shot[]> {
  const r = await fetch(`${API}/api/shots/${encodeURIComponent(name)}`);
  if (!r.ok) return [];
  const d = await r.json();
  return Array.isArray(d) ? d : [];
}

export async function fetchReplacement(name: string): Promise<ReplacementData | null> {
  const r = await fetch(`${API}/api/scout/replacement?player_name=${encodeURIComponent(name)}`);
  const d = await r.json();
  return d.target ? d : null;
}

export async function fetchLeaders(): Promise<Leaders> {
  const r = await fetch(`${API}/api/scout/leaders`);
  const d = await r.json();
  return d.error ? { scorers: [], architects: [] } : d;
}

export async function fetchTalentRadar(
  category: TalentCategory,
  league: LeagueKey,
  pos: string,
  limit = 24
): Promise<PlayerDNA[]> {
  const r = await fetch(
    `${API}/api/scout/talent-radar?category=${category}&league=${league}&pos=${pos}&limit=${limit}`
  );
  const d = await r.json();
  return d.talents ?? [];
}
