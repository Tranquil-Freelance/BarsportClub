# Global i18n + Hydration Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix Next.js hydration error in UniversalHeader and wire `useTranslation()` into all pages (meritometro, nerd-zone, scout-engine, fanta-draft) replacing all hardcoded Italian strings.

**Architecture:** `isMounted` guard prevents SSR/client language mismatch in UniversalHeader. Each page imports `useTranslation` from react-i18next and calls `t(key)`. Locale JSON files expanded with all missing keys for IT/EN/ES/FR.

**Tech Stack:** Next.js 14 App Router, react-i18next, i18next-browser-languagedetector, TypeScript

---

## File Map

| File | Change |
|------|--------|
| `app/components/UniversalHeader.tsx` | Add `isMounted` guard → skeleton until hydrated |
| `app/i18n/locales/it.json` | Add ~30 missing keys |
| `app/i18n/locales/en.json` | Add ~30 missing keys |
| `app/i18n/locales/es.json` | Add ~30 missing keys |
| `app/i18n/locales/fr.json` | Add ~30 missing keys |
| `app/meritometro/page.tsx` | Add `useTranslation`, replace hardcoded IT strings |
| `app/nerd-zone/page.tsx` | Add `useTranslation`, replace hardcoded IT strings |
| `app/scout-engine/page.tsx` | Add `useTranslation`, translate TABS dynamically |
| `app/fanta-draft/page.tsx` | Add `useTranslation`, replace hardcoded IT strings |

---

## Task 1: Fix Hydration Error in UniversalHeader

**Root cause:** `i18n.language` is `"en"` on SSR (no localStorage). On client hydration, LanguageDetector reads `barsport_lang` from localStorage (e.g. `"it"`). All `t()` calls and `i18n.language` reads mismatch → React hydration error.

**Fix:** `isMounted` pattern. Return a pixel-perfect skeleton header until client mount completes.

**Files:**
- Modify: `app/components/UniversalHeader.tsx`

- [ ] **Step 1: Add `isMounted` to UniversalHeader**

Replace the top of `UniversalHeader` function (line 86–99) with:

```tsx
export default function UniversalHeader() {
  const pathname = usePathname();
  const { t } = useTranslation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => { setIsMounted(true); }, []);
```

- [ ] **Step 2: Return skeleton before mount**

Add immediately after the hooks (before `const navItems`):

```tsx
  if (!isMounted) {
    return (
      <header className="h-20 bg-[#0a192f] border-b border-slate-800 sticky top-0 z-[100] shadow-lg" />
    );
  }
```

- [ ] **Step 3: Verify — run dev server and open browser console**

```bash
npm run dev
```

Open `http://localhost:3000`. Console should have zero hydration errors. Header should appear after a single paint. Switch language → should persist on reload.

- [ ] **Step 4: Commit**

```bash
git add app/components/UniversalHeader.tsx
git commit -m "fix(header): isMounted guard kills SSR/i18n hydration mismatch"
```

---

## Task 2: Add Missing Locale Keys to All 4 JSON Files

**Strategy:** Replace entire locale files with expanded versions. All existing keys preserved, new keys appended per section.

**Files:**
- Modify: `app/i18n/locales/it.json`
- Modify: `app/i18n/locales/en.json`
- Modify: `app/i18n/locales/es.json`
- Modify: `app/i18n/locales/fr.json`

- [ ] **Step 1: Write `app/i18n/locales/it.json`**

```json
{
  "nav": {
    "campionati": "Campionati",
    "betting": "Betting",
    "meritometro": "Meritometro",
    "scout_engine": "Scout Engine",
    "fanta_draft": "Fanta Draft",
    "nerd_zone": "Nerd Zone"
  },
  "common": {
    "loading": "Caricamento...",
    "no_data": "Nessun dato disponibile",
    "search": "Cerca",
    "filter": "Filtra",
    "close": "Chiudi",
    "back": "Indietro",
    "update": "Aggiorna",
    "season": "Stagione",
    "league": "Lega",
    "team": "Squadra",
    "player": "Giocatore",
    "position": "Posizione",
    "goals": "Gol",
    "assists": "Assist",
    "minutes": "Minuti",
    "matches": "Partite",
    "error": "Errore"
  },
  "meritometro": {
    "title": "Meritometro",
    "subtitle": "Analisi del merito partita",
    "ranking": "Classifica IMR",
    "round": "Giorno",
    "final": "Finale",
    "day": "Giorno",
    "imr_total": "IMR Totale",
    "computing": "Calcolo ranking in corso...",
    "db_loading": "Accesso al database...",
    "no_ranking": "Dati Classifica Assenti",
    "pos": "Pos",
    "club": "Club"
  },
  "scout": {
    "title": "Scout Engine",
    "home_tab": "Classifica",
    "target_tab": "DNA Target",
    "replace_tab": "Cloni PSE",
    "h2h_tab": "H2H Duel",
    "discover_tab": "TalentRadar",
    "top_scorers": "Top Scorers",
    "top_architects": "Top Architects",
    "search_placeholder": "Cerca giocatore...",
    "search_for": "Cerca per",
    "appearances": "Presenze",
    "empty_target_title": "Analisi DNA Target",
    "empty_target_desc": "Cerca un giocatore per visualizzare il profilo offensivo completo con metriche avanzate, radar percentili e shot map interattiva",
    "empty_replace_title": "Sostituti PSE",
    "empty_replace_desc": "Cerca un giocatore per trovare i suoi cloni statistici",
    "empty_h2h_title": "H2H Duel",
    "empty_h2h_desc": "Cerca due giocatori da confrontare",
    "empty_discover_title": "TalentRadar",
    "empty_discover_desc": "Scopri talenti emergenti per posizione",
    "percentiles_vs_role": "Percentili vs Ruolo",
    "trend_xg_goals": "Trend xG vs Gol",
    "shot": "Tiro",
    "size_equals_xg": "Dimensione = xG",
    "action": "Azione",
    "shot_type": "Tipo",
    "backend_offline": "Backend offline · Avvia il server",
    "top_performers_sub": "Top performers per metriche avanzate — stagione 25/26",
    "similarity": "Similarità",
    "all_positions": "Tutti",
    "select_first": "Seleziona primo giocatore",
    "select_second": "Seleziona secondo giocatore"
  },
  "fanta": {
    "title": "FantaDraft",
    "dashboard": "Dashboard",
    "search_player": "Cerca Giocatore",
    "auction": "Asta",
    "period": "Periodo",
    "current_season": "Stagione in Corso",
    "previous_season": "Stagione Precedente",
    "last_5": "Ultime 5 Partite",
    "hidden_gems": "Hidden Gems",
    "assist_kings": "Assist Kings",
    "league": "Lega",
    "position_filter": "Posizione",
    "sort_by": "Ordina per",
    "breakout_badge": "BREAKOUT",
    "no_players": "Nessun giocatore trovato",
    "shots_count": "tiri",
    "goals_count": "gol",
    "max_bid": "Offerta Max",
    "value_score": "Value Score",
    "production": "Produzione",
    "auction_targets": "Target Asta",
    "team_attack_index": "TAI",
    "empty_search": "Cerca un giocatore per visualizzare il profilo",
    "empty_auction": "Configura il budget e cerca obiettivi per l'asta",
    "profile_title": "Profilo Giocatore",
    "trend_title": "Trend xG",
    "percentiles_title": "Percentili vs Ruolo",
    "shotmap_title": "Shot Map",
    "season_stats": "Statistiche Stagione",
    "budget": "Budget",
    "num_players": "N. Giocatori",
    "search_targets": "Cerca Obiettivi"
  },
  "nerd": {
    "title": "Nerd Zone",
    "subtitle": "BI Analytics · God Mode",
    "bubble": "Bubble Scatter",
    "radar": "Radar Compare",
    "raw_data": "Raw Data",
    "entity": "Entità",
    "player": "Giocatore",
    "team": "Squadra",
    "season": "Stagione",
    "chart_axes": "Assi del Grafico",
    "x_axis": "Asse X",
    "y_axis": "Asse Y",
    "bubble_z": "Bolla Z",
    "color_by": "Colora per",
    "role": "Ruolo",
    "advanced_filters": "Filtri Avanzati",
    "min_minutes": "Min. Minuti",
    "home_away": "Casa / Trasferta",
    "all": "Tutti",
    "home": "Casa",
    "away": "Tra.",
    "leagues": "Leghe",
    "roles": "Ruoli",
    "update_data": "Aggiorna Dati",
    "entities": "entità",
    "no_data": "Configura i parametri → Aggiorna Dati",
    "querying": "Interrogo il database...",
    "select_max3": "Seleziona (max 3)",
    "compare": "Confronta →",
    "select_players": "Seleziona giocatori e premi Confronta",
    "radar_player_only": "Radar disponibile solo per entità Giocatore",
    "normalized": "Valori normalizzati su massimi di riferimento (0–100%)",
    "points": "Punti",
    "none_option": "— Nessuno —",
    "entity_season": "Entità & Stagione",
    "unknown_error": "Errore sconosciuto",
    "shots": "Tiri"
  }
}
```

- [ ] **Step 2: Write `app/i18n/locales/en.json`**

```json
{
  "nav": {
    "campionati": "Leagues",
    "betting": "Betting",
    "meritometro": "Meritometer",
    "scout_engine": "Scout Engine",
    "fanta_draft": "Fanta Draft",
    "nerd_zone": "Nerd Zone"
  },
  "common": {
    "loading": "Loading...",
    "no_data": "No data available",
    "search": "Search",
    "filter": "Filter",
    "close": "Close",
    "back": "Back",
    "update": "Update",
    "season": "Season",
    "league": "League",
    "team": "Team",
    "player": "Player",
    "position": "Position",
    "goals": "Goals",
    "assists": "Assists",
    "minutes": "Minutes",
    "matches": "Matches",
    "error": "Error"
  },
  "meritometro": {
    "title": "Meritometer",
    "subtitle": "Match merit analysis",
    "ranking": "IMR Ranking",
    "round": "Round",
    "final": "Final",
    "day": "Round",
    "imr_total": "Total IMR",
    "computing": "Computing ranking...",
    "db_loading": "Accessing database...",
    "no_ranking": "No Ranking Data",
    "pos": "Pos",
    "club": "Club"
  },
  "scout": {
    "title": "Scout Engine",
    "home_tab": "Standings",
    "target_tab": "DNA Target",
    "replace_tab": "PSE Clones",
    "h2h_tab": "H2H Duel",
    "discover_tab": "TalentRadar",
    "top_scorers": "Top Scorers",
    "top_architects": "Top Architects",
    "search_placeholder": "Search player...",
    "search_for": "Search by",
    "appearances": "Appearances",
    "empty_target_title": "DNA Target Analysis",
    "empty_target_desc": "Search a player to view their full offensive profile with advanced metrics, percentile radar, and interactive shot map",
    "empty_replace_title": "PSE Substitutes",
    "empty_replace_desc": "Search a player to find their statistical clones",
    "empty_h2h_title": "H2H Duel",
    "empty_h2h_desc": "Search two players to compare them",
    "empty_discover_title": "TalentRadar",
    "empty_discover_desc": "Discover emerging talents by position",
    "percentiles_vs_role": "Percentiles vs Role",
    "trend_xg_goals": "xG vs Goals Trend",
    "shot": "Shot",
    "size_equals_xg": "Size = xG",
    "action": "Action",
    "shot_type": "Type",
    "backend_offline": "Backend offline · Start the server",
    "top_performers_sub": "Top performers by advanced metrics — season 25/26",
    "similarity": "Similarity",
    "all_positions": "All",
    "select_first": "Select first player",
    "select_second": "Select second player"
  },
  "fanta": {
    "title": "FantaDraft",
    "dashboard": "Dashboard",
    "search_player": "Search Player",
    "auction": "Auction",
    "period": "Period",
    "current_season": "Current Season",
    "previous_season": "Previous Season",
    "last_5": "Last 5 Matches",
    "hidden_gems": "Hidden Gems",
    "assist_kings": "Assist Kings",
    "league": "League",
    "position_filter": "Position",
    "sort_by": "Sort by",
    "breakout_badge": "BREAKOUT",
    "no_players": "No players found",
    "shots_count": "shots",
    "goals_count": "goals",
    "max_bid": "Max Bid",
    "value_score": "Value Score",
    "production": "Production",
    "auction_targets": "Auction Targets",
    "team_attack_index": "TAI",
    "empty_search": "Search a player to view their profile",
    "empty_auction": "Configure budget and search auction targets",
    "profile_title": "Player Profile",
    "trend_title": "xG Trend",
    "percentiles_title": "Percentiles vs Role",
    "shotmap_title": "Shot Map",
    "season_stats": "Season Stats",
    "budget": "Budget",
    "num_players": "No. Players",
    "search_targets": "Search Targets"
  },
  "nerd": {
    "title": "Nerd Zone",
    "subtitle": "BI Analytics · God Mode",
    "bubble": "Bubble Scatter",
    "radar": "Radar Compare",
    "raw_data": "Raw Data",
    "entity": "Entity",
    "player": "Player",
    "team": "Team",
    "season": "Season",
    "chart_axes": "Chart Axes",
    "x_axis": "X Axis",
    "y_axis": "Y Axis",
    "bubble_z": "Bubble Z",
    "color_by": "Color by",
    "role": "Role",
    "advanced_filters": "Advanced Filters",
    "min_minutes": "Min. Minutes",
    "home_away": "Home / Away",
    "all": "All",
    "home": "Home",
    "away": "Away",
    "leagues": "Leagues",
    "roles": "Roles",
    "update_data": "Update Data",
    "entities": "entities",
    "no_data": "Configure parameters → Update Data",
    "querying": "Querying the database...",
    "select_max3": "Select (max 3)",
    "compare": "Compare →",
    "select_players": "Select players and press Compare",
    "radar_player_only": "Radar available for Player entity only",
    "normalized": "Values normalized to reference maxima (0–100%)",
    "points": "Points",
    "none_option": "— None —",
    "entity_season": "Entity & Season",
    "unknown_error": "Unknown error",
    "shots": "Shots"
  }
}
```

- [ ] **Step 3: Write `app/i18n/locales/es.json`**

```json
{
  "nav": {
    "campionati": "Ligas",
    "betting": "Apuestas",
    "meritometro": "Meritómetro",
    "scout_engine": "Motor Scout",
    "fanta_draft": "Fanta Draft",
    "nerd_zone": "Zona Nerd"
  },
  "common": {
    "loading": "Cargando...",
    "no_data": "Sin datos disponibles",
    "search": "Buscar",
    "filter": "Filtrar",
    "close": "Cerrar",
    "back": "Volver",
    "update": "Actualizar",
    "season": "Temporada",
    "league": "Liga",
    "team": "Equipo",
    "player": "Jugador",
    "position": "Posición",
    "goals": "Goles",
    "assists": "Asistencias",
    "minutes": "Minutos",
    "matches": "Partidos",
    "error": "Error"
  },
  "meritometro": {
    "title": "Meritómetro",
    "subtitle": "Análisis del mérito del partido",
    "ranking": "Clasificación IMR",
    "round": "Jornada",
    "final": "Final",
    "day": "Jornada",
    "imr_total": "IMR Total",
    "computing": "Calculando ranking...",
    "db_loading": "Accediendo a la base de datos...",
    "no_ranking": "Sin datos de clasificación",
    "pos": "Pos",
    "club": "Club"
  },
  "scout": {
    "title": "Motor Scout",
    "home_tab": "Clasificación",
    "target_tab": "ADN Objetivo",
    "replace_tab": "Clones PSE",
    "h2h_tab": "Duelo H2H",
    "discover_tab": "TalentRadar",
    "top_scorers": "Máximos Goleadores",
    "top_architects": "Mejores Creadores",
    "search_placeholder": "Buscar jugador...",
    "search_for": "Buscar por",
    "appearances": "Apariciones",
    "empty_target_title": "Análisis ADN Objetivo",
    "empty_target_desc": "Busca un jugador para ver su perfil ofensivo completo con métricas avanzadas, radar de percentiles y mapa de disparos interactivo",
    "empty_replace_title": "Sustitutos PSE",
    "empty_replace_desc": "Busca un jugador para encontrar sus clones estadísticos",
    "empty_h2h_title": "Duelo H2H",
    "empty_h2h_desc": "Busca dos jugadores para compararlos",
    "empty_discover_title": "TalentRadar",
    "empty_discover_desc": "Descubre talentos emergentes por posición",
    "percentiles_vs_role": "Percentiles vs Posición",
    "trend_xg_goals": "Tendencia xG vs Goles",
    "shot": "Disparo",
    "size_equals_xg": "Tamaño = xG",
    "action": "Acción",
    "shot_type": "Tipo",
    "backend_offline": "Backend offline · Inicia el servidor",
    "top_performers_sub": "Mejores jugadores por métricas avanzadas — temporada 25/26",
    "similarity": "Similitud",
    "all_positions": "Todos",
    "select_first": "Selecciona el primer jugador",
    "select_second": "Selecciona el segundo jugador"
  },
  "fanta": {
    "title": "FantaDraft",
    "dashboard": "Panel",
    "search_player": "Buscar Jugador",
    "auction": "Subasta",
    "period": "Período",
    "current_season": "Temporada Actual",
    "previous_season": "Temporada Anterior",
    "last_5": "Últimos 5 Partidos",
    "hidden_gems": "Joyas Ocultas",
    "assist_kings": "Reyes de Asistencias",
    "league": "Liga",
    "position_filter": "Posición",
    "sort_by": "Ordenar por",
    "breakout_badge": "BREAKOUT",
    "no_players": "No se encontraron jugadores",
    "shots_count": "disparos",
    "goals_count": "goles",
    "max_bid": "Oferta Máx.",
    "value_score": "Puntuación de Valor",
    "production": "Producción",
    "auction_targets": "Objetivos de Subasta",
    "team_attack_index": "TAI",
    "empty_search": "Busca un jugador para ver su perfil",
    "empty_auction": "Configura el presupuesto y busca objetivos para la subasta",
    "profile_title": "Perfil del Jugador",
    "trend_title": "Tendencia xG",
    "percentiles_title": "Percentiles vs Posición",
    "shotmap_title": "Mapa de Disparos",
    "season_stats": "Estadísticas de Temporada",
    "budget": "Presupuesto",
    "num_players": "Nº Jugadores",
    "search_targets": "Buscar Objetivos"
  },
  "nerd": {
    "title": "Zona Nerd",
    "subtitle": "BI Analytics · Modo Dios",
    "bubble": "Burbuja Scatter",
    "radar": "Radar Comparativo",
    "raw_data": "Datos Brutos",
    "entity": "Entidad",
    "player": "Jugador",
    "team": "Equipo",
    "season": "Temporada",
    "chart_axes": "Ejes del Gráfico",
    "x_axis": "Eje X",
    "y_axis": "Eje Y",
    "bubble_z": "Burbuja Z",
    "color_by": "Colorear por",
    "role": "Rol",
    "advanced_filters": "Filtros Avanzados",
    "min_minutes": "Mín. Minutos",
    "home_away": "Local / Visitante",
    "all": "Todos",
    "home": "Local",
    "away": "Visit.",
    "leagues": "Ligas",
    "roles": "Roles",
    "update_data": "Actualizar Datos",
    "entities": "entidades",
    "no_data": "Configura los parámetros → Actualizar Datos",
    "querying": "Consultando la base de datos...",
    "select_max3": "Selecciona (máx. 3)",
    "compare": "Comparar →",
    "select_players": "Selecciona jugadores y pulsa Comparar",
    "radar_player_only": "Radar disponible solo para la entidad Jugador",
    "normalized": "Valores normalizados sobre máximos de referencia (0–100%)",
    "points": "Puntos",
    "none_option": "— Ninguno —",
    "entity_season": "Entidad & Temporada",
    "unknown_error": "Error desconocido",
    "shots": "Tiros"
  }
}
```

- [ ] **Step 4: Write `app/i18n/locales/fr.json`**

```json
{
  "nav": {
    "campionati": "Championnats",
    "betting": "Paris",
    "meritometro": "Méritomètre",
    "scout_engine": "Scout Engine",
    "fanta_draft": "Fanta Draft",
    "nerd_zone": "Zone Nerd"
  },
  "common": {
    "loading": "Chargement...",
    "no_data": "Aucune donnée disponible",
    "search": "Rechercher",
    "filter": "Filtrer",
    "close": "Fermer",
    "back": "Retour",
    "update": "Actualiser",
    "season": "Saison",
    "league": "Ligue",
    "team": "Équipe",
    "player": "Joueur",
    "position": "Poste",
    "goals": "Buts",
    "assists": "Passes déc.",
    "minutes": "Minutes",
    "matches": "Matchs",
    "error": "Erreur"
  },
  "meritometro": {
    "title": "Méritomètre",
    "subtitle": "Analyse du mérite du match",
    "ranking": "Classement IMR",
    "round": "Journée",
    "final": "Final",
    "day": "Journée",
    "imr_total": "IMR Total",
    "computing": "Calcul du classement...",
    "db_loading": "Accès à la base de données...",
    "no_ranking": "Données de classement absentes",
    "pos": "Pos",
    "club": "Club"
  },
  "scout": {
    "title": "Scout Engine",
    "home_tab": "Classement",
    "target_tab": "ADN Cible",
    "replace_tab": "Clones PSE",
    "h2h_tab": "Duel H2H",
    "discover_tab": "TalentRadar",
    "top_scorers": "Meilleurs Buteurs",
    "top_architects": "Meilleurs Créateurs",
    "search_placeholder": "Rechercher un joueur...",
    "search_for": "Rechercher par",
    "appearances": "Apparitions",
    "empty_target_title": "Analyse ADN Cible",
    "empty_target_desc": "Recherchez un joueur pour voir son profil offensif complet avec métriques avancées, radar de percentiles et carte de tirs interactive",
    "empty_replace_title": "Substituts PSE",
    "empty_replace_desc": "Recherchez un joueur pour trouver ses clones statistiques",
    "empty_h2h_title": "Duel H2H",
    "empty_h2h_desc": "Recherchez deux joueurs pour les comparer",
    "empty_discover_title": "TalentRadar",
    "empty_discover_desc": "Découvrez les talents émergents par poste",
    "percentiles_vs_role": "Percentiles vs Poste",
    "trend_xg_goals": "Tendance xG vs Buts",
    "shot": "Tir",
    "size_equals_xg": "Taille = xG",
    "action": "Action",
    "shot_type": "Type",
    "backend_offline": "Backend hors ligne · Démarrez le serveur",
    "top_performers_sub": "Meilleurs joueurs par métriques avancées — saison 25/26",
    "similarity": "Similarité",
    "all_positions": "Tous",
    "select_first": "Sélectionnez le premier joueur",
    "select_second": "Sélectionnez le deuxième joueur"
  },
  "fanta": {
    "title": "FantaDraft",
    "dashboard": "Tableau de bord",
    "search_player": "Rechercher Joueur",
    "auction": "Enchères",
    "period": "Période",
    "current_season": "Saison en Cours",
    "previous_season": "Saison Précédente",
    "last_5": "5 Derniers Matchs",
    "hidden_gems": "Pépites Cachées",
    "assist_kings": "Rois des Passes",
    "league": "Ligue",
    "position_filter": "Poste",
    "sort_by": "Trier par",
    "breakout_badge": "BREAKOUT",
    "no_players": "Aucun joueur trouvé",
    "shots_count": "tirs",
    "goals_count": "buts",
    "max_bid": "Offre Max.",
    "value_score": "Score de Valeur",
    "production": "Production",
    "auction_targets": "Cibles Enchères",
    "team_attack_index": "TAI",
    "empty_search": "Recherchez un joueur pour voir son profil",
    "empty_auction": "Configurez le budget et recherchez des cibles pour les enchères",
    "profile_title": "Profil du Joueur",
    "trend_title": "Tendance xG",
    "percentiles_title": "Percentiles vs Poste",
    "shotmap_title": "Carte de Tirs",
    "season_stats": "Stats de Saison",
    "budget": "Budget",
    "num_players": "Nb Joueurs",
    "search_targets": "Rechercher Cibles"
  },
  "nerd": {
    "title": "Zone Nerd",
    "subtitle": "BI Analytics · Mode Dieu",
    "bubble": "Nuage de Points",
    "radar": "Radar Comparatif",
    "raw_data": "Données Brutes",
    "entity": "Entité",
    "player": "Joueur",
    "team": "Équipe",
    "season": "Saison",
    "chart_axes": "Axes du Graphique",
    "x_axis": "Axe X",
    "y_axis": "Axe Y",
    "bubble_z": "Bulle Z",
    "color_by": "Colorier par",
    "role": "Rôle",
    "advanced_filters": "Filtres Avancés",
    "min_minutes": "Min. Minutes",
    "home_away": "Domicile / Extérieur",
    "all": "Tous",
    "home": "Domicile",
    "away": "Ext.",
    "leagues": "Ligues",
    "roles": "Rôles",
    "update_data": "Actualiser les Données",
    "entities": "entités",
    "no_data": "Configurez les paramètres → Actualiser les Données",
    "querying": "Interrogation de la base de données...",
    "select_max3": "Sélectionner (max 3)",
    "compare": "Comparer →",
    "select_players": "Sélectionnez des joueurs et appuyez sur Comparer",
    "radar_player_only": "Radar disponible uniquement pour l'entité Joueur",
    "normalized": "Valeurs normalisées sur maxima de référence (0–100%)",
    "points": "Points",
    "none_option": "— Aucun —",
    "entity_season": "Entité & Saison",
    "unknown_error": "Erreur inconnue",
    "shots": "Tirs"
  }
}
```

- [ ] **Step 5: Commit locale changes**

```bash
git add app/i18n/locales/
git commit -m "i18n(locales): add missing keys for meritometro, nerd, scout, fanta (IT/EN/ES/FR)"
```

---

## Task 3: Translate meritometro/page.tsx

**Files:**
- Modify: `app/meritometro/page.tsx`

Strings to replace:
| Hardcoded | Key |
|-----------|-----|
| `"Accesso al database..."` | `t('meritometro.db_loading')` |
| `"Giorno {match.round}"` | `` `${t('meritometro.day')} ${match.round}` `` |
| `"Finale"` | `t('meritometro.final')` |
| `"Meritometro"` in h2 | `t('meritometro.title')` |
| `"Ranking IMR"` | `t('meritometro.ranking')` |
| `"Pos"` | `t('meritometro.pos')` |
| `"Club"` | `t('meritometro.club')` |
| `"IMR Totale"` | `t('meritometro.imr_total')` |
| `"Calcolo Ranking in corso..."` | `t('meritometro.computing')` |
| `"Dati Classifica Assenti"` | `t('meritometro.no_ranking')` |
| `"Nessun dato disponibile"` | `t('common.no_data')` |

- [ ] **Step 1: Add useTranslation hook and suppressHydrationWarning**

At top of `MeritometroPage()`:

```tsx
import { useTranslation } from "react-i18next";
import "../../i18n/config";

export default function MeritometroPage() {
  const { t } = useTranslation();
  const [isMounted, setIsMounted] = useState(false);
  // ...existing state...

  useEffect(() => { setIsMounted(true); }, []);
```

Add `suppressHydrationWarning` to root div:
```tsx
<div className="min-h-screen bg-[#F1F5F9] text-[#1E293B] font-sans pb-20" suppressHydrationWarning>
```

- [ ] **Step 2: Replace all hardcoded strings in JSX**

Line 116: `"Accesso al database..."` → `{t('meritometro.db_loading')}`

Line 121: `` "Giorno {match.round}" `` →
```tsx
<div className="absolute top-0 left-0 bg-slate-100 text-slate-400 text-[9px] font-black px-4 py-1 rounded-br-xl uppercase tracking-tighter">
  {t('meritometro.day')} {match.round}
</div>
```

Line 134: `"Finale"` → `{t('meritometro.final')}`

Line 109: `"Meritometro"` in h2 → `{t('meritometro.title')}`

Line 174: `"Nessun dato disponibile"` → `{t('common.no_data')}`

Line 186: `"Ranking IMR"` → `{t('meritometro.ranking')}`

Lines 194–196 (table headers):
```tsx
<th ...>Pos</th>  →  <th ...>{t('meritometro.pos')}</th>
<th ...>Club</th>  →  <th ...>{t('meritometro.club')}</th>
<th ...>IMR Totale</th>  →  <th ...>{t('meritometro.imr_total')}</th>
```

Line 201: `"Calcolo Ranking in corso..."` → `{t('meritometro.computing')}`

Line 216: `"Dati Classifica Assenti"` → `{t('meritometro.no_ranking')}`

- [ ] **Step 3: Verify**

Switch to ES in browser → "Méritomètre", "Jornada", "Final", etc. appear correctly.

- [ ] **Step 4: Commit**

```bash
git add app/meritometro/page.tsx
git commit -m "i18n(meritometro): replace all hardcoded IT strings with t() calls"
```

---

## Task 4: Translate nerd-zone/page.tsx

**Files:**
- Modify: `app/nerd-zone/page.tsx`

Key changes: (a) convert METRICS to a function using t(), (b) wire all sidebar labels, (c) translate tab labels, empty states, tooltips.

- [ ] **Step 1: Add imports at top of file**

```tsx
import { useTranslation } from "react-i18next";
import "../../i18n/config";
```

- [ ] **Step 2: In `NerdZonePage`, add hook and replace hardcoded strings**

```tsx
export default function NerdZonePage() {
  const { t } = useTranslation();
  // ...existing state...
```

Build localized METRICS inside component (after the hook):
```tsx
  const METRICS_LOC = [
    { value: "xG_p90",         label: "xG / 90" },
    { value: "xA_p90",         label: "xA / 90" },
    { value: "shots_p90",      label: `${t('nerd.shots')} / 90` },
    { value: "goals_p90",      label: `${t('common.goals')} / 90` },
    { value: "assists_p90",    label: `${t('common.assists')} / 90` },
    { value: "key_passes_p90", label: "Key Passes / 90" },
    { value: "xGChain_p90",    label: "xGChain / 90" },
    { value: "xGBuildup_p90",  label: "xGBuildup / 90" },
    { value: "xG",             label: "xG (tot)" },
    { value: "xA",             label: "xA (tot)" },
    { value: "shots",          label: `${t('nerd.shots')} (tot)` },
    { value: "goals",          label: `${t('common.goals')} (tot)` },
    { value: "assists",        label: `${t('common.assists')} (tot)` },
    { value: "key_passes",     label: "Key Passes (tot)" },
    { value: "xGChain",        label: "xGChain (tot)" },
    { value: "xGBuildup",      label: "xGBuildup (tot)" },
    { value: "time",           label: `${t('common.minutes')} (tot)` },
  ];
```

Update `xLabel`, `yLabel`, `zLabel`:
```tsx
const xLabel = METRICS_LOC.find(m => m.value === controls.xAxis)?.label ?? controls.xAxis;
const yLabel = METRICS_LOC.find(m => m.value === controls.yAxis)?.label ?? controls.yAxis;
const zLabel = METRICS_LOC.find(m => m.value === controls.zAxis)?.label ?? controls.zAxis;
```

- [ ] **Step 3: Replace TABS labels**

```tsx
const TABS = [
  { id: "bubble", labelKey: "nerd.bubble",   emoji: "🌌" },
  { id: "radar",  labelKey: "nerd.radar",    emoji: "🕸️" },
  { id: "grid",   labelKey: "nerd.raw_data", emoji: "📋" },
] as const;
```

In JSX tab bar: `{t.label}` → `` `${t_item.emoji} ${t(t_item.labelKey)}` ``

- [ ] **Step 4: Replace all sidebar hardcoded strings**

Section titles:
- `"Entità & Stagione"` → `{t('nerd.entity_season')}`
- `"Assi del Grafico"` → `{t('nerd.chart_axes')}`
- `"Filtri Avanzati"` → `{t('nerd.advanced_filters')}`

Entity toggle: `"Giocatore"` → `{t('nerd.player')}`, `"Squadra"` → `{t('nerd.team')}`
Season label: `"Stagione"` → `{t('nerd.season')}`

Axes labels: `"Asse X"` → `{t('nerd.x_axis')}`, `"Asse Y"` → `{t('nerd.y_axis')}`, `"Bolla Z"` → `{t('nerd.bubble_z')}`

zAxis select none: `"— Nessuno —"` → `{t('nerd.none_option')}`

Metric select options: replace module-level METRICS with METRICS_LOC in select options too.

Color by: `"Colora per"` → `{t('nerd.color_by')}`, `"Ruolo"` → `{t('nerd.role')}`, `"Squadra"` → `{t('nerd.team')}`

Filters: `"Min. Minuti"` → `{t('nerd.min_minutes')}`, `"Casa / Trasferta"` → `{t('nerd.home_away')}`

Location filter buttons: `"Tutti"` → `{t('nerd.all')}`, `"Casa"` → `{t('nerd.home')}`, `"Tra."` → `{t('nerd.away')}`

Leagues label: `"Leghe"` → `{t('nerd.leagues')}`
Roles label: `"Ruoli"` → `{t('nerd.roles')}`

Update button: `"⚡ Aggiorna Dati"` → `` `⚡ ${t('nerd.update_data')}` ``
Loading button: `"Carico..."` → `{t('common.loading')}`

- [ ] **Step 5: Replace header and main area strings**

Header h1: `"Nerd Zone"` → `{t('nerd.title')}`
Header p: `"BI Analytics · God Mode"` → `{t('nerd.subtitle')}`
Count span: `` `${data.length} entità` `` → `` `${data.length} ${t('nerd.entities')}` ``

Error div: `"Errore:"` → `{t('common.error')}:`

Empty state (no query): `"Configura i parametri → Aggiorna Dati"` → `{t('nerd.no_data')}`
Loading state: `"Interrogo il database..."` → `{t('nerd.querying')}`

- [ ] **Step 6: Replace strings in sub-components (RadarTab, GridTab, BubbleTab)**

Pass `t` as prop or invoke `useTranslation()` inside each sub-component:

`RadarTab`: add `const { t } = useTranslation();`
- `"Seleziona (max 3)"` → `{t('nerd.select_max3')}`
- `"Cerca giocatore..."` placeholder → `{t('scout.search_placeholder')}`
- `"Confronta →"` → `{t('nerd.compare')}`
- `"Seleziona giocatori e premi Confronta"` → `{t('nerd.select_players')}`
- `"Radar disponibile solo per entità Giocatore"` → `{t('nerd.radar_player_only')}`
- `"Valori normalizzati su massimi di riferimento (0–100%)"` → `{t('nerd.normalized')}`

`BubbleTab`: add `const { t } = useTranslation();`
- `"Punti"` → `{t('nerd.points')}`
- `"Nessun dato — premi Aggiorna"` → `{t('nerd.no_data')}`
- `"Trendline"` → keep as-is (proper noun)

`GridTab`: add `const { t } = useTranslation();`
- `"Giocatore"` column header → `{t('nerd.player')}`
- `"Squadra"` column header → `{t('nerd.team')}`
- `"Nessun dato disponibile"` → `{t('common.no_data')}`

- [ ] **Step 7: Add suppressHydrationWarning to root div**

```tsx
<div className="min-h-screen bg-[#060911] text-white flex flex-col" ... suppressHydrationWarning>
```

- [ ] **Step 8: Commit**

```bash
git add app/nerd-zone/page.tsx
git commit -m "i18n(nerd-zone): wire useTranslation, localize all sidebar/tabs/empty states/sub-components"
```

---

## Task 5: Translate scout-engine/page.tsx

**Files:**
- Modify: `app/scout-engine/page.tsx`

Key issue: `TABS` is a module-level const with hardcoded Italian labels. Must convert labels to translation keys.

- [ ] **Step 1: Add import and convert TABS to use tKey**

```tsx
import { useTranslation } from "react-i18next";
import "../../i18n/config";
```

Replace module-level TABS:
```tsx
const TABS: { id: Tab; tKey: string; Icon: React.ElementType }[] = [
  { id: "home",     tKey: "scout.home_tab",    Icon: Flame },
  { id: "target",   tKey: "scout.target_tab",  Icon: Target },
  { id: "replace",  tKey: "scout.replace_tab", Icon: Repeat },
  { id: "h2h",      tKey: "scout.h2h_tab",     Icon: Scale },
  { id: "discover", tKey: "scout.discover_tab",Icon: Zap },
];
```

- [ ] **Step 2: Add hook in ScoutEnginePage**

```tsx
export default function ScoutEnginePage() {
  const { t } = useTranslation();
  // ...
```

Replace TABS render:
```tsx
{TABS.map(({ id, tKey, Icon }) => (
  <button key={id} onClick={() => setTab(id)} ...>
    <Icon size={13} />
    {t(tKey)}
  </button>
))}
```

Replace search placeholder:
```tsx
placeholder={`${t('scout.search_for')} ${t(TABS.find(tb => tb.id === tab)?.tKey ?? '')}...`}
```

Add `suppressHydrationWarning` to root div.

- [ ] **Step 3: Translate HomeTab sub-component**

```tsx
function HomeTab({ leaders, onLoad, t }: { leaders: Leaders; onLoad: (n: string) => void; t: Function }) {
```

Or add `const { t } = useTranslation();` inside HomeTab.

Replace:
- `"Top performers per metriche avanzate — stagione 25/26"` → `{t('scout.top_performers_sub')}`
- `"Top Scorers"` title → `{t('scout.top_scorers')}`
- `"Top Architects"` title → `{t('scout.top_architects')}`

In `LeaderList`:
- `"Backend offline · Avvia il server"` → `{t('scout.backend_offline')}`

- [ ] **Step 4: Translate TargetTab sub-component**

Add `const { t } = useTranslation();` inside TargetTab.

Empty state:
```tsx
<EmptyState
  Icon={Target}
  title={t('scout.empty_target_title')}
  desc={t('scout.empty_target_desc')}
/>
```

Stats in hero row:
```tsx
{ l: t('scout.appearances'), v: dna.games },
{ l: t('common.minutes'),    v: `${dna.minutes}'` },
{ l: t('common.goals'),      v: Math.round(dna.totals.goals ?? 0) },
{ l: t('common.assists'),    v: Math.round(dna.totals.assists ?? 0) },
```

- [ ] **Step 5: Translate shot map strings in ShotMapComponent**

In ShotMap (if defined in scout-engine, otherwise handle in fanta-draft similarly):
- `` `${shots.length} tiri` `` → `` `${shots.length} ${t('fanta.shots_count')}` ``
- `` `${goals.length} gol` `` → `` `${goals.length} ${t('fanta.goals_count')}` ``
- `"Azione"` → `{t('scout.action')}`
- `"Tipo"` → `{t('scout.shot_type')}`
- `"Tiro"` → `{t('scout.shot')}`
- `"Dimensione = xG"` → `{t('scout.size_equals_xg')}`

Radar sub-component:
- `"Percentili vs Ruolo"` → `{t('scout.percentiles_vs_role')}`

TrendChart sub-component:
- `"Trend xG vs Gol"` → `{t('scout.trend_xg_goals')}`
- `"Nessun dato disponibile"` → `{t('common.no_data')}`

- [ ] **Step 6: Translate ReplaceTab, H2HTab, DiscoverTab**

For each sub-component with empty states, add `const { t } = useTranslation();` and replace:
- ReplaceTab empty: title → `t('scout.empty_replace_title')`, desc → `t('scout.empty_replace_desc')`
- H2HTab empty: title → `t('scout.empty_h2h_title')`, desc → `t('scout.empty_h2h_desc')`
- DiscoverTab empty: title → `t('scout.empty_discover_title')`, desc → `t('scout.empty_discover_desc')`
- Similarity label → `t('scout.similarity')`
- Position filter "Tutti" → `t('scout.all_positions')`

- [ ] **Step 7: Commit**

```bash
git add app/scout-engine/page.tsx
git commit -m "i18n(scout-engine): convert TABS to tKeys, localize all sub-components"
```

---

## Task 6: Translate fanta-draft/page.tsx

**Files:**
- Modify: `app/fanta-draft/page.tsx`

The fanta-draft page is large. Key areas: tab labels, period filter, dashboard table headers, player profile sub-components.

- [ ] **Step 1: Add import**

```tsx
import { useTranslation } from "react-i18next";
import "../../i18n/config";
```

- [ ] **Step 2: Add hook and suppressHydrationWarning in main component**

```tsx
export default function FantaDraftPage() {
  const { t } = useTranslation();
  // ...
```

Add `suppressHydrationWarning` to root div.

- [ ] **Step 3: Translate tab labels**

The tabs in fanta (dashboard, search_player, auction) use the fanta locale keys. Find the tab definitions (typically an array like `TABS`) and replace hardcoded labels with `t('fanta.dashboard')`, `t('fanta.search_player')`, `t('fanta.auction')`.

- [ ] **Step 4: Translate period filter**

The time filter uses "current"/"previous"/"last5" which map to:
- `t('fanta.current_season')`
- `t('fanta.previous_season')`
- `t('fanta.last_5')`

- [ ] **Step 5: Translate league + position labels**

- League label → `t('fanta.league')`
- Position label → `t('fanta.position_filter')`
- Sort by → `t('fanta.sort_by')`

- [ ] **Step 6: Translate table headers in dashboard**

Common columns: goals → `t('common.goals')`, assists → `t('common.assists')`, minutes → `t('common.minutes')`, matches → `t('common.matches')`

Fanta-specific: `"Max Bid"` → `t('fanta.max_bid')`, `"Value Score"` → `t('fanta.value_score')`, `"Produzione"` → `t('fanta.production')`

- [ ] **Step 7: Translate player profile sub-component**

- Profile title → `t('fanta.profile_title')`
- Shot map title → `t('fanta.shotmap_title')`
- Shots count: `` `${n} tiri` `` → `` `${n} ${t('fanta.shots_count')}` ``
- Goals count: `` `${n} gol` `` → `` `${n} ${t('fanta.goals_count')}` ``
- Action/Type labels in shot tooltip → `t('scout.action')`, `t('scout.shot_type')`
- Trend title → `t('fanta.trend_title')`
- Percentiles title → `t('fanta.percentiles_title')`

- [ ] **Step 8: Translate Hidden Gems + Assist Kings sections**

- `"Hidden Gems"` → `t('fanta.hidden_gems')`
- `"Assist Kings"` → `t('fanta.assist_kings')`

- [ ] **Step 9: Translate auction tab**

- `"Target Asta"` / auction targets → `t('fanta.auction_targets')`
- Budget label → `t('fanta.budget')`
- `"Cerca Obiettivi"` → `t('fanta.search_targets')`
- Empty state → `t('fanta.empty_auction')`

- [ ] **Step 10: Translate BREAKOUT badge**

- `"BREAKOUT"` → `t('fanta.breakout_badge')` (keeps the label consistent, EN already "BREAKOUT")

- [ ] **Step 11: Commit**

```bash
git add app/fanta-draft/page.tsx
git commit -m "i18n(fanta-draft): wire useTranslation across all tabs and sub-components"
```

---

## Self-Review Checklist

- [ ] Hydration error: isMounted in UniversalHeader returns matching skeleton for SSR
- [ ] Locale files: all 4 languages (IT/EN/ES/FR) have matching key sets — no key missing in one language that exists in another
- [ ] meritometro: zero hardcoded Italian strings remain
- [ ] nerd-zone: METRICS labels localized, sub-components use t()
- [ ] scout-engine: TABS use tKey, all sub-components localized
- [ ] fanta-draft: all tabs, table headers, sub-components localized
- [ ] No `t()` calls with keys missing from locale files
- [ ] `suppressHydrationWarning` on root div of each translated page
