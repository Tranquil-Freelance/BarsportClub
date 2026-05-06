/**
 * Barsport.club — 5 articoli fondamentali in 5 lingue (IT, EN, ES, FR, DE).
 * Struttura dati per il blog multilingua.
 *
 * Ogni articolo ha: slug, category, title, excerpt, content (HTML base),
 * e un'immagine hero generica.
 */

export interface BlogArticleTranslation {
  title: string;
  excerpt: string;
  category: string;
  content: string;
}

export type BlogArticleLocale = "it" | "en" | "es" | "fr" | "de";

export interface BlogArticleData {
  id: number;
  slug: string;
  hero_image: string;
  date: string;
  translations: Record<BlogArticleLocale, BlogArticleTranslation>;
}

export const blogArticles: BlogArticleData[] = [
  // ──────────────────────────────────────────────
  // 1. TIMELINE
  // ──────────────────────────────────────────────
  {
    id: 4,
    slug: "timeline-barsport-club",
    hero_image: "/images/home/timeline-cover.webp",
    date: "2026-04-01T09:00:00",
    translations: {
      it: {
        title: "La Timeline di Barsport.club",
        category: "Annunci",
        excerpt:
          "<p>Dall'idea al lancio: la cronologia completa del progetto Barsport.club, dalla prima bozza al blog provinciale che vede i numeri come nessuno.</p>",
        content: `
          <h2>Come nasce Barsport.club</h2>
          <p>Tutto inizia con un foglio Excel e un'ossessione: <strong>capire il calcio attraverso i numeri</strong>. Non i soliti highlights, ma i dati grezzi: xG, passaggi chiave, pressione, percentile ranking.</p>
          <p>Barsport.club è un progetto nato dalla voglia di portare l'analisi avanzata fuori dai circuiti chiusi delle società professionistiche. Un blog provinciale con ambizioni globali.</p>

          <h2>2024 — La genesi</h2>
          <p>I primi scraper Python per raccogliere dati da fonti esterne di analisi calcistica. Database PostgreSQL. Le prime visualizzazioni. Era tutto rudimentale, ma la direzione era chiara.</p>

          <h2>2025 — I primi moduli</h2>
          <p>Nascono il <strong>Meritometro</strong> (un modo nuovo di valutare le prestazioni), lo <strong>Scout Engine</strong> (analisi multidimensionale dei giocatori) e il <strong>Fanta Draft</strong> (Talent Auction Index).</p>

          <h2>2026 — Il blog provinciale</h2>
          <p>Il sito prende forma: Homepage, Nerd Zone, e ora il blog. Barsport.club diventa un punto di riferimento per chi vuole vedere il calcio da un'altra angolazione.</p>

          <p>Questa è solo l'inizio.</p>
        `,
      },
      en: {
        title: "The Barsport.club Timeline",
        category: "Announcements",
        excerpt:
          "<p>From idea to launch: the complete timeline of the Barsport.club project, from the first draft to the provincial blog that sees numbers like no one else.</p>",
        content: `
          <h2>How Barsport.club was born</h2>
          <p>It all starts with an Excel sheet and an obsession: <strong>understanding football through numbers</strong>. Not the usual highlights, but raw data: xG, key passes, pressure, percentile rankings.</p>
          <p>Barsport.club is a project born from the desire to bring advanced analytics outside the closed circles of professional clubs. A provincial blog with global ambitions.</p>

          <h2>2024 — The genesis</h2>
          <p>The first Python scrapers to collect data from external analytics sources. PostgreSQL database. First visualizations. Everything was rudimentary, but the direction was clear.</p>

          <h2>2025 — The first modules</h2>
          <p>The <strong>Meritometro</strong> (a new way to evaluate performances), the <strong>Scout Engine</strong> (multidimensional player analysis), and the <strong>Fanta Draft</strong> (Talent Auction Index) are born.</p>

          <h2>2026 — The provincial blog</h2>
          <p>The site takes shape: Homepage, Nerd Zone, and now the blog. Barsport.club becomes a reference point for those who want to see football from a different angle.</p>

          <p>This is just the beginning.</p>
        `,
      },
      es: {
        title: "La Cronología de Barsport.club",
        category: "Anuncios",
        excerpt:
          "<p>Desde la idea hasta el lanzamiento: la cronología completa del proyecto Barsport.club, desde el primer borrador hasta el blog provincial que ve los números como nadie.</p>",
        content: `
          <h2>Cómo nace Barsport.club</h2>
          <p>Todo comienza con una hoja de Excel y una obsesión: <strong>entender el fútbol a través de los números</strong>. No los típicos resúmenes, sino datos brutos: xG, pases clave, presión, rankings percentiles.</p>
          <p>Barsport.club es un proyecto nacido del deseo de llevar el análisis avanzado fuera de los círculos cerrados de los clubes profesionales. Un blog provincial con ambiciones globales.</p>

          <h2>2024 — La génesis</h2>
          <p>Los primeros scrapers en Python para recolectar datos de fuentes externas de análisis. Base de datos PostgreSQL. Primeras visualizaciones. Todo era rudimentario, pero la dirección estaba clara.</p>

          <h2>2025 — Los primeros módulos</h2>
          <p>Nacen el <strong>Meritómetro</strong> (una nueva forma de evaluar rendimientos), el <strong>Scout Engine</strong> (análisis multidimensional de jugadores) y el <strong>Fanta Draft</strong> (Talent Auction Index).</p>

          <h2>2026 — El blog provincial</h2>
          <p>El sitio toma forma: Homepage, Nerd Zone, y ahora el blog. Barsport.club se convierte en un punto de referencia para quienes quieren ver el fútbol desde otro ángulo.</p>

          <p>Esto es solo el principio.</p>
        `,
      },
      fr: {
        title: "La Chronologie de Barsport.club",
        category: "Annonces",
        excerpt:
          "<p>De l'idée au lancement : la chronologie complète du projet Barsport.club, depuis la première ébauche jusqu'au blog provincial qui voit les chiffres comme personne.</p>",
        content: `
          <h2>Comment est né Barsport.club</h2>
          <p>Tout commence avec une feuille Excel et une obsession : <strong>comprendre le football à travers les chiffres</strong>. Pas les résumés habituels, mais les données brutes : xG, passes clés, pression, classements percentiles.</p>
          <p>Barsport.club est un projet né de l'envie d'apporter l'analyse avancée en dehors des cercles fermés des clubs professionnels. Un blog provincial avec des ambitions globales.</p>

          <h2>2024 — La genèse</h2>
          <p>Les premiers scrapers Python pour collecter les données de sources d'analyse externes. Base de données PostgreSQL. Premières visualisations. Tout était rudimentaire, mais la direction était claire.</p>

          <h2>2025 — Les premiers modules</h2>
          <p>Naissent le <strong>Meritomètre</strong> (une nouvelle façon d'évaluer les performances), le <strong>Scout Engine</strong> (analyse multidimensionnelle des joueurs) et le <strong>Fanta Draft</strong> (Talent Auction Index).</p>

          <h2>2026 — Le blog provincial</h2>
          <p>Le site prend forme : Homepage, Nerd Zone, et maintenant le blog. Barsport.club devient une référence pour ceux qui veulent voir le football sous un angle différent.</p>

          <p>Ce n'est que le début.</p>
        `,
      },
      de: {
        title: "Die Zeitleiste von Barsport.club",
        category: "Ankündigungen",
        excerpt:
          "<p>Von der Idee zum Launch: die komplette Chronologie des Barsport.club-Projekts, vom ersten Entwurf bis zum provinziellen Blog, der Zahlen sieht wie kein anderer.</p>",
        content: `
          <h2>Wie Barsport.club entstand</h2>
          <p>Alles beginnt mit einer Excel-Tabelle und einer Obsession: <strong>Fußball durch Zahlen verstehen</strong>. Nicht die üblichen Highlights, sondern Rohdaten: xG, Schlüsselpässe, Pressing, Perzentil-Rankings.</p>
          <p>Barsport.club ist ein Projekt, das aus dem Wunsch entstand, fortgeschrittene Analysen aus den geschlossenen Kreisen der Profivereine herauszutragen. Ein provinzieller Blog mit globalen Ambitionen.</p>

          <h2>2024 — Die Genesis</h2>
          <p>Die ersten Python-Scraper zur Datensammlung von externen Analysequellen. PostgreSQL-Datenbank. Erste Visualisierungen. Alles war rudimentär, aber die Richtung war klar.</p>

          <h2>2025 — Die ersten Module</h2>
          <p>Der <strong>Meritometer</strong> (eine neue Art, Leistungen zu bewerten), der <strong>Scout Engine</strong> (multidimensionale Spieleranalyse) und der <strong>Fanta Draft</strong> (Talent Auction Index) entstehen.</p>

          <h2>2026 — Der provinzielle Blog</h2>
          <p>Die Website nimmt Gestalt an: Homepage, Nerd Zone und jetzt der Blog. Barsport.club wird zur Referenz für alle, die Fußball aus einem anderen Blickwinkel sehen wollen.</p>

          <p>Dies ist erst der Anfang.</p>
        `,
      },
    },
  },

  // ──────────────────────────────────────────────
  // 2. MERITOMETRO
  // ──────────────────────────────────────────────
  {
    id: 5,
    slug: "meritometro-come-funziona",
    hero_image: "/images/home/meritometro-cover.webp",
    date: "2026-04-03T10:00:00",
    translations: {
      it: {
        title: "Meritometro: Come Funziona",
        category: "Guida",
        excerpt:
          "<p>Scopri il sistema di valutazione IMR (Individual Match Rating) che assegna un punteggio a ogni prestazione basandosi su oltre 40 metriche calcolate in tempo reale.</p>",
        content: `
          <h2>Cos'è il Meritometro?</h2>
          <p>Il <strong>Meritometro</strong> è il cuore analitico di Barsport.club. Un sistema proprietario di valutazione che assegna un <em>Individual Match Rating (IMR)</em> a ogni giocatore, partita dopo partita.</p>

          <h2>Come viene calcolato l'IMR</h2>
          <p>L'IMR aggrega oltre 40 metriche in 5 macro-dimensioni:</p>
          <ul>
            <li><strong>Attacco</strong> — tiri, xG, dribbling, passaggi chiave</li>
            <li><strong>Difesa</strong> — contrasti, intercetti, recuperi</li>
            <li><strong>Costruzione</strong> — precisione passaggi, progressione palla</li>
            <li><strong>Fisico</strong> — duelli vinti, km percorsi</li>
            <li><strong>Impatto</strong> — contributo ai gol, momenti decisivi</li>
          </ul>

          <h2>La classifica IMR</h2>
          <p>La classifica generale del Meritometro mostra la media IMR di ogni giocatore stagione per stagione. Puoi filtrare per ruolo, lega e minutaggio minimo.</p>

          <p>Il Meritometro è disponibile nella sezione <a href="/meritometro">omonima</a> del sito.</p>
        `,
      },
      en: {
        title: "Meritometro: How It Works",
        category: "Guide",
        excerpt:
          "<p>Discover the IMR (Individual Match Rating) evaluation system that scores every performance based on over 40 real-time calculated metrics.</p>",
        content: `
          <h2>What is the Meritometro?</h2>
          <p>The <strong>Meritometro</strong> is the analytical heart of Barsport.club. A proprietary evaluation system that assigns an <em>Individual Match Rating (IMR)</em> to every player, match after match.</p>

          <h2>How IMR is calculated</h2>
          <p>IMR aggregates over 40 metrics into 5 macro-dimensions:</p>
          <ul>
            <li><strong>Attack</strong> — shots, xG, dribbles, key passes</li>
            <li><strong>Defense</strong> — tackles, interceptions, recoveries</li>
            <li><strong>Build-up</strong> — pass accuracy, ball progression</li>
            <li><strong>Physical</strong> — duels won, km covered</li>
            <li><strong>Impact</strong> — goal contribution, decisive moments</li>
          </ul>

          <h2>The IMR Ranking</h2>
          <p>The overall Meritometro ranking shows every player's average IMR season by season. You can filter by role, league, and minimum minutes played.</p>

          <p>Meritometro is available in the <a href="/meritometro">dedicated section</a> of the site.</p>
        `,
      },
      es: {
        title: "Meritómetro: Cómo Funciona",
        category: "Guía",
        excerpt:
          "<p>Descubre el sistema de evaluación IMR (Individual Match Rating) que puntúa cada rendimiento basándose en más de 40 métricas calculadas en tiempo real.</p>",
        content: `
          <h2>¿Qué es el Meritómetro?</h2>
          <p>El <strong>Meritómetro</strong> es el corazón analítico de Barsport.club. Un sistema de evaluación propio que asigna un <em>Individual Match Rating (IMR)</em> a cada jugador, partido tras partido.</p>

          <h2>Cómo se calcula el IMR</h2>
          <p>El IMR agrega más de 40 métricas en 5 macro-dimensiones:</p>
          <ul>
            <li><strong>Ataque</strong> — tiros, xG, regates, pases clave</li>
            <li><strong>Defensa</strong> — entradas, interceptaciones, recuperaciones</li>
            <li><strong>Construcción</strong> — precisión de pases, progresión de balón</li>
            <li><strong>Físico</strong> — duelos ganados, km recorridos</li>
            <li><strong>Impacto</strong> — contribución a goles, momentos decisivos</li>
          </ul>

          <h2>El Ranking IMR</h2>
          <p>La clasificación general del Meritómetro muestra el IMR medio de cada jugador temporada por temporada. Puedes filtrar por rol, liga y minutos mínimos.</p>

          <p>El Meritómetro está disponible en la <a href="/meritometro">sección dedicada</a> del sitio.</p>
        `,
      },
      fr: {
        title: "Meritomètre : Comment ça Marche",
        category: "Guide",
        excerpt:
          "<p>Découvrez le système d'évaluation IMR (Individual Match Rating) qui note chaque performance en se basant sur plus de 40 métriques calculées en temps réel.</p>",
        content: `
          <h2>Qu'est-ce que le Meritomètre ?</h2>
          <p>Le <strong>Meritomètre</strong> est le cœur analytique de Barsport.club. Un système d'évaluation propriétaire qui attribue un <em>Individual Match Rating (IMR)</em> à chaque joueur, match après match.</p>

          <h2>Comment l'IMR est calculé</h2>
          <p>L'IMR agrège plus de 40 métriques en 5 macro-dimensions :</p>
          <ul>
            <li><strong>Attaque</strong> — tirs, xG, dribbles, passes clés</li>
            <li><strong>Défense</strong> — tacles, interceptions, récupérations</li>
            <li><strong>Construction</strong> — précision des passes, progression du ballon</li>
            <li><strong>Physique</strong> — duels gagnés, km parcourus</li>
            <li><strong>Impact</strong> — contribution aux buts, moments décisifs</li>
          </ul>

          <h2>Le Classement IMR</h2>
          <p>Le classement général du Meritomètre montre la moyenne IMR de chaque joueur saison par saison. Vous pouvez filtrer par rôle, ligue et minutes minimales.</p>

          <p>Le Meritomètre est disponible dans la <a href="/meritometro">section dédiée</a> du site.</p>
        `,
      },
      de: {
        title: "Meritometer: Wie es Funktioniert",
        category: "Leitfaden",
        excerpt:
          "<p>Entdecke das IMR-Bewertungssystem (Individual Match Rating), das jede Leistung auf Basis von über 40 in Echtzeit berechneten Metriken bewertet.</p>",
        content: `
          <h2>Was ist der Meritometer?</h2>
          <p>Der <strong>Meritometer</strong> ist das analytische Herz von Barsport.club. Ein proprietäres Bewertungssystem, das jedem Spieler ein <em>Individual Match Rating (IMR)</em> zuweist, Spiel für Spiel.</p>

          <h2>Wie der IMR berechnet wird</h2>
          <p>Der IMR aggregiert über 40 Metriken in 5 Makro-Dimensionen:</p>
          <ul>
            <li><strong>Angriff</strong> — Schüsse, xG, Dribblings, Torschussvorlagen</li>
            <li><strong>Verteidigung</strong> — Tacklings, Abfangen, Balleroberungen</li>
            <li><strong>Spielaufbau</strong> — Passgenauigkeit, Ballprogression</li>
            <li><strong>Physis</strong> — gewonnene Zweikämpfe, gelaufene km</li>
            <li><strong>Impact</strong> — Torbeteiligung, entscheidende Momente</li>
          </ul>

          <h2>Das IMR-Ranking</h2>
          <p>Die Meritometer-Gesamtwertung zeigt den durchschnittlichen IMR jedes Spielers Saison für Saison. Du kannst nach Rolle, Liga und Mindesteinsatzzeit filtern.</p>

          <p>Der Meritometer ist im <a href="/meritometro">entsprechenden Bereich</a> der Website verfügbar.</p>
        `,
      },
    },
  },

  // ──────────────────────────────────────────────
  // 3. SCOUT ENGINE
  // ──────────────────────────────────────────────
  {
    id: 6,
    slug: "scout-engine-dna-target-cloni",
    hero_image: "/images/home/scout-cover.webp",
    date: "2026-04-06T11:00:00",
    translations: {
      it: {
        title: "Scout Engine: DNA Target, Cloni PSE e H2H Duel",
        category: "Guida",
        excerpt:
          "<p>Il motore di scouting avanzato che confronta giocatori su 180+ metriche. Trova il clone perfetto, sfida i talenti uno contro uno e scopri i profili che il mercato non ha ancora scoperto.</p>",
        content: `
          <h2>Lo Scout Engine</h2>
          <p>Lo <strong>Scout Engine</strong> è il modulo di analisi talent-scouting di Barsport.club. Confronta, valuta e scopri giocatori su oltre 180 metriche, divise in 6 macro-aree.</p>

          <h2>DNA Target</h2>
          <p>Inserisci un giocatore-obiettivo (es. uno di cui la tua squadra ha bisogno) e lo Scout Engine cerca nel database il profilo più simile. Percentili, statistiche, ruolo: tutto confrontato istantaneamente.</p>

          <h2>Cloni PSE</h2>
          <p>La funzione <strong>Player Similarity Engine</strong> trova i giocatori statisticamente più simili a un dato profilo. Utile per scovare alternative low-cost o sostituti ideali.</p>

          <h2>H2H Duel</h2>
          <p>Confronta due giocatori testa a testa: i radar dei percentili vengono sovrapposti per mostrare chi domina in ogni dimensione del gioco.</p>

          <p>Esplora lo Scout Engine nella <a href="/scout-engine">sezione dedicata</a>.</p>
        `,
      },
      en: {
        title: "Scout Engine: DNA Target, PSE Clones & H2H Duel",
        category: "Guide",
        excerpt:
          "<p>The advanced scouting engine that compares players across 180+ metrics. Find the perfect clone, duel talents head-to-head, and discover profiles the market hasn't found yet.</p>",
        content: `
          <h2>The Scout Engine</h2>
          <p>The <strong>Scout Engine</strong> is Barsport.club's talent-scouting analysis module. Compare, evaluate, and discover players across over 180 metrics, divided into 6 macro-areas.</p>

          <h2>DNA Target</h2>
          <p>Enter a target player (e.g., one your team needs) and the Scout Engine searches the database for the most similar profile. Percentiles, stats, role: everything compared instantly.</p>

          <h2>PSE Clones</h2>
          <p>The <strong>Player Similarity Engine</strong> finds statistically similar players to a given profile. Great for uncovering low-cost alternatives or ideal replacements.</p>

          <h2>H2H Duel</h2>
          <p>Compare two players head-to-head: percentile radars are overlaid to show who dominates in every dimension of the game.</p>

          <p>Explore the Scout Engine in its <a href="/scout-engine">dedicated section</a>.</p>
        `,
      },
      es: {
        title: "Scout Engine: DNA Target, Clones PSE y Duelo H2H",
        category: "Guía",
        excerpt:
          "<p>El motor de scouting avanzado que compara jugadores en más de 180 métricas. Encuentra el clon perfecto, enfrenta talentos uno contra uno y descubre perfiles que el mercado aún no ha encontrado.</p>",
        content: `
          <h2>El Scout Engine</h2>
          <p>El <strong>Scout Engine</strong> es el módulo de análisis de talent-scouting de Barsport.club. Compara, evalúa y descubre jugadores en más de 180 métricas, divididas en 6 macro-áreas.</p>

          <h2>DNA Target</h2>
          <p>Ingresa un jugador objetivo (ej. uno que tu equipo necesita) y el Scout Engine busca en la base de datos el perfil más similar. Percentiles, estadísticas, rol: todo comparado al instante.</p>

          <h2>Clones PSE</h2>
          <p>El <strong>Player Similarity Engine</strong> encuentra jugadores estadísticamente similares a un perfil dado. Ideal para descubrir alternativas low-cost o sustitutos ideales.</p>

          <h2>Duelo H2H</h2>
          <p>Compara dos jugadores cara a cara: los radares de percentiles se superponen para mostrar quién domina en cada dimensión del juego.</p>

          <p>Explora el Scout Engine en su <a href="/scout-engine">sección dedicada</a>.</p>
        `,
      },
      fr: {
        title: "Scout Engine : DNA Target, Clones PSE et Duel H2H",
        category: "Guide",
        excerpt:
          "<p>Le moteur de scouting avancé qui compare les joueurs sur plus de 180 métriques. Trouvez le clone parfait, confrontez les talents tête-à-tête et découvrez des profils que le marché n'a pas encore trouvés.</p>",
        content: `
          <h2>Le Scout Engine</h2>
          <p>Le <strong>Scout Engine</strong> est le module d'analyse de talent-scouting de Barsport.club. Comparez, évaluez et découvrez des joueurs sur plus de 180 métriques, réparties en 6 macro-zones.</p>

          <h2>DNA Target</h2>
          <p>Entrez un joueur cible (ex. un dont votre équipe a besoin) et le Scout Engine cherche dans la base de données le profil le plus similaire. Percentiles, statistiques, rôle : tout est comparé instantanément.</p>

          <h2>Clones PSE</h2>
          <p>Le <strong>Player Similarity Engine</strong> trouve les joueurs statistiquement les plus similaires à un profil donné. Idéal pour dénicher des alternatives low-cost ou des remplaçants idéaux.</p>

          <h2>Duel H2H</h2>
          <p>Comparez deux joueurs tête-à-tête : les radars de percentiles sont superposés pour montrer qui domine dans chaque dimension du jeu.</p>

          <p>Explorez le Scout Engine dans sa <a href="/scout-engine">section dédiée</a>.</p>
        `,
      },
      de: {
        title: "Scout Engine: DNA Target, PSE-Klone & H2H-Duell",
        category: "Leitfaden",
        excerpt:
          "<p>Die erweiterte Scouting-Engine, die Spieler anhand von über 180 Metriken vergleicht. Finde den perfekten Klon, stelle Talente im direkten Duell gegenüber und entdecke Profile, die der Markt noch nicht gefunden hat.</p>",
        content: `
          <h2>Der Scout Engine</h2>
          <p>Der <strong>Scout Engine</strong> ist das Talent-Scouting-Analysemodul von Barsport.club. Vergleiche, bewerte und entdecke Spieler anhand von über 180 Metriken, aufgeteilt in 6 Makro-Bereiche.</p>

          <h2>DNA Target</h2>
          <p>Gib einen Zielspieler ein (z.B. einen, den dein Team benötigt) und der Scout Engine durchsucht die Datenbank nach dem ähnlichsten Profil. Perzentile, Statistiken, Rolle: alles wird sofort verglichen.</p>

          <h2>PSE-Klone</h2>
          <p>Der <strong>Player Similarity Engine</strong> findet statistisch ähnliche Spieler zu einem gegebenen Profil. Ideal, um Low-Cost-Alternativen oder ideale Ersatzspieler zu entdecken.</p>

          <h2>H2H-Duell</h2>
          <p>Vergleiche zwei Spieler direkt: die Perzentil-Radare werden überlagert, um zu zeigen, wer in jeder Spiel-Dimension dominiert.</p>

          <p>Erkunde den Scout Engine in der <a href="/scout-engine">entsprechenden Sektion</a>.</p>
        `,
      },
    },
  },

  // ──────────────────────────────────────────────
  // 4. FANTA DRAFT
  // ──────────────────────────────────────────────
  {
    id: 7,
    slug: "fanta-draft-tai-hidden-gems",
    hero_image: "/images/home/fanta-cover.webp",
    date: "2026-04-10T10:30:00",
    translations: {
      it: {
        title: "Fanta Draft: TAI, Hidden Gems e Assist Kings",
        category: "Guida",
        excerpt:
          "<p>Il Talent Auction Index che anticipa il mercato. Scopri i giocatori sottovalutati, i re degli assist e prepara l'asta con dati oggettivi.</p>",
        content: `
          <h2>Il Fanta Draft</h2>
          <p>Il <strong>Fanta Draft</strong> è il modulo per il fantacalcio avanzato di Barsport.club. Non più valutazioni a sentimento, ma dati oggettivi per preparare la tua asta.</p>

          <h2>Talent Auction Index (TAI)</h2>
          <p>Il <strong>TAI</strong> è un indice proprietario che stima il valore reale di un giocatore al fantacalcio, combinando: rendimento attuale, trend storico, minutaggio, ruolo e potenziale di crescita.</p>

          <h2>Hidden Gems</h2>
          <p>La sezione <strong>Hidden Gems</strong> mostra i giocatori con il miglior rapporto qualità-prezzo: quelli che il mercato sta sottovalutando ma che i numeri dicono essere pronti per il salto.</p>

          <h2>Assist Kings</h2>
          <p>I veri registi non segnano sempre, ma costruiscono. La classifica degli Assist Kings premia i costruttori di gioco: passaggi chiave, xA, chances create.</p>

          <p>Prepara l'asta nella <a href="/fanta-draft">sezione Fanta Draft</a>.</p>
        `,
      },
      en: {
        title: "Fanta Draft: TAI, Hidden Gems & Assist Kings",
        category: "Guide",
        excerpt:
          "<p>The Talent Auction Index that anticipates the market. Discover undervalued players, assist kings, and prepare your auction with objective data.</p>",
        content: `
          <h2>Fanta Draft</h2>
          <p>The <strong>Fanta Draft</strong> is Barsport.club's advanced fantasy football module. No more gut-feeling evaluations, just objective data to prepare your auction.</p>

          <h2>Talent Auction Index (TAI)</h2>
          <p><strong>TAI</strong> is a proprietary index that estimates a player's real fantasy football value, combining: current performance, historical trend, minutes played, role, and growth potential.</p>

          <h2>Hidden Gems</h2>
          <p>The <strong>Hidden Gems</strong> section shows players with the best value-for-money ratio: those the market is underestimating but the numbers say are ready for the leap.</p>

          <h2>Assist Kings</h2>
          <p>The true playmakers don't always score, but they build. The Assist Kings ranking rewards the game constructors: key passes, xA, chances created.</p>

          <p>Prepare your auction in the <a href="/fanta-draft">Fanta Draft section</a>.</p>
        `,
      },
      es: {
        title: "Fanta Draft: TAI, Hidden Gems y Assist Kings",
        category: "Guía",
        excerpt:
          "<p>El Talent Auction Index que anticipa el mercado. Descubre jugadores infravalorados, reyes de la asistencia y prepara tu subasta con datos objetivos.</p>",
        content: `
          <h2>Fanta Draft</h2>
          <p>El <strong>Fanta Draft</strong> es el módulo de fantasy football avanzado de Barsport.club. Ya no más evaluaciones intuitivas, solo datos objetivos para preparar tu subasta.</p>

          <h2>Talent Auction Index (TAI)</h2>
          <p>El <strong>TAI</strong> es un índice propio que estima el valor real de un jugador en el fantasy football, combinando: rendimiento actual, tendencia histórica, minutos jugados, rol y potencial de crecimiento.</p>

          <h2>Hidden Gems</h2>
          <p>La sección <strong>Hidden Gems</strong> muestra los jugadores con la mejor relación calidad-precio: aquellos que el mercado está subestimando pero los números dicen que están listos para el salto.</p>

          <h2>Assist Kings</h2>
          <p>Los verdaderos creadores de juego no siempre marcan, pero construyen. El ranking de Assist Kings premia a los constructores de juego: pases clave, xA, ocasiones creadas.</p>

          <p>Prepara tu subasta en la <a href="/fanta-draft">sección Fanta Draft</a>.</p>
        `,
      },
      fr: {
        title: "Fanta Draft : TAI, Hidden Gems et Assist Kings",
        category: "Guide",
        excerpt:
          "<p>Le Talent Auction Index qui anticipe le marché. Découvrez les joueurs sous-évalués, les rois de la passe décisive et préparez votre enchère avec des données objectives.</p>",
        content: `
          <h2>Fanta Draft</h2>
          <p>Le <strong>Fanta Draft</strong> est le module de fantasy football avancé de Barsport.club. Fini les évaluations à l'instinct, place aux données objectives pour préparer votre enchère.</p>

          <h2>Talent Auction Index (TAI)</h2>
          <p>Le <strong>TAI</strong> est un indice propriétaire qui estime la valeur réelle d'un joueur au fantasy football, combinant : performance actuelle, tendance historique, temps de jeu, rôle et potentiel de croissance.</p>

          <h2>Hidden Gems</h2>
          <p>La section <strong>Hidden Gems</strong> montre les joueurs avec le meilleur rapport qualité-prix : ceux que le marché sous-estime mais que les chiffres disent prêts pour le saut.</p>

          <h2>Assist Kings</h2>
          <p>Les vrais maîtres à jouer ne marquent pas toujours, mais ils construisent. Le classement des Assist Kings récompense les constructeurs de jeu : passes clés, xA, occasions créées.</p>

          <p>Préparez votre enchère dans la <a href="/fanta-draft">section Fanta Draft</a>.</p>
        `,
      },
      de: {
        title: "Fanta Draft: TAI, Hidden Gems & Assist Kings",
        category: "Leitfaden",
        excerpt:
          "<p>Der Talent Auction Index, der den Markt antizipiert. Entdecke unterbewertete Spieler, Assist-Könige und bereite deine Auktion mit objektiven Daten vor.</p>",
        content: `
          <h2>Fanta Draft</h2>
          <p>Der <strong>Fanta Draft</strong> ist Barsport.clubs Modul für fortgeschrittenes Fantasy Football. Keine Bauchgefühl-Bewertungen mehr, sondern objektive Daten zur Vorbereitung deiner Auktion.</p>

          <h2>Talent Auction Index (TAI)</h2>
          <p>Der <strong>TAI</strong> ist ein proprietärer Index, der den tatsächlichen Fantasy-Football-Wert eines Spielers schätzt, kombiniert aus: aktueller Leistung, historischem Trend, Einsatzzeit, Rolle und Wachstumspotenzial.</p>

          <h2>Hidden Gems</h2>
          <p>Die Sektion <strong>Hidden Gems</strong> zeigt Spieler mit dem besten Preis-Leistungs-Verhältnis: jene, die der Markt unterschätzt, die aber laut Zahlen für den Durchbruch bereit sind.</p>

          <h2>Assist Kings</h2>
          <p>Die wahren Spielmacher erzielen nicht immer Tore, aber sie bauen auf. Das Assist-Kings-Ranking belohnt die Spielgestalter: Torschussvorlagen, xA, kreierte Chancen.</p>

          <p>Bereite deine Auktion in der <a href="/fanta-draft">Fanta Draft-Sektion</a> vor.</p>
        `,
      },
    },
  },

  // ──────────────────────────────────────────────
  // 5. NERD ZONE
  // ──────────────────────────────────────────────
  {
    id: 8,
    slug: "nerd-zone-bi-analytics-god-mode",
    hero_image: "/images/home/nerdzone-cover.webp",
    date: "2026-04-14T12:00:00",
    translations: {
      it: {
        title: "Nerd Zone: BI Analytics in God Mode",
        category: "Guida",
        excerpt:
          "<p>Scatter plot interattivi, radar multidimensionali, dati grezzi. Per chi vuole vedere i numeri senza filtri, con il pieno controllo su assi, filtri e metriche.</p>",
        content: `
          <h2>La Nerd Zone</h2>
          <p>La <strong>Nerd Zone</strong> è il laboratorio dati di Barsport.club. Niente storytelling, niente editoriali: solo dati grezzi, grafici interattivi e la libertà di esplorare come vuoi.</p>

          <h2>Bubble Scatter</h2>
          <p>Lo scatter plot interattivo: scegli gli assi X e Y, la dimensione delle bolle (Z) e il colore per ruolo. Ogni bolla è un giocatore. Esplora correlazioni, outlier e tendenze di mercato.</p>

          <h2>Radar Compare</h2>
          <p>Confronta fino a 6 giocatori su dimensioni statistiche a tua scelta. I radar dei percentili si sovrappongono per un confronto visivo immediato.</p>

          <h2>Raw Data</h2>
          <p>La tabella dati completa: oltre 180 colonne, filtraggio avanzato, esportazione. Per chi vuole fare le proprie analisi in Excel o Python.</p>

          <p>Entra nel laboratorio nella <a href="/nerd-zone">sezione Nerd Zone</a>.</p>
        `,
      },
      en: {
        title: "Nerd Zone: BI Analytics in God Mode",
        category: "Guide",
        excerpt:
          "<p>Interactive scatter plots, multidimensional radars, raw data. For those who want to see the numbers unfiltered, with full control over axes, filters, and metrics.</p>",
        content: `
          <h2>The Nerd Zone</h2>
          <p>The <strong>Nerd Zone</strong> is Barsport.club's data laboratory. No storytelling, no editorials: just raw data, interactive charts, and the freedom to explore as you wish.</p>

          <h2>Bubble Scatter</h2>
          <p>The interactive scatter plot: choose X and Y axes, bubble size (Z), and color by role. Each bubble is a player. Explore correlations, outliers, and market trends.</p>

          <h2>Radar Compare</h2>
          <p>Compare up to 6 players on statistical dimensions of your choice. Percentile radars overlap for an immediate visual comparison.</p>

          <h2>Raw Data</h2>
          <p>The complete data table: over 180 columns, advanced filtering, export. For those who want to do their own analysis in Excel or Python.</p>

          <p>Enter the laboratory in the <a href="/nerd-zone">Nerd Zone section</a>.</p>
        `,
      },
      es: {
        title: "Nerd Zone: BI Analytics en Modo Dios",
        category: "Guía",
        excerpt:
          "<p>Gráficos de dispersión interactivos, radares multidimensionales, datos brutos. Para quienes quieren ver los números sin filtros, con control total sobre ejes, filtros y métricas.</p>",
        content: `
          <h2>La Nerd Zone</h2>
          <p>La <strong>Nerd Zone</strong> es el laboratorio de datos de Barsport.club. Sin storytelling, sin editoriales: solo datos brutos, gráficos interactivos y la libertad de explorar como quieras.</p>

          <h2>Bubble Scatter</h2>
          <p>El gráfico de dispersión interactivo: elige los ejes X e Y, el tamaño de las burbujas (Z) y el color por rol. Cada burbuja es un jugador. Explora correlaciones, valores atípicos y tendencias de mercado.</p>

          <h2>Radar Compare</h2>
          <p>Compara hasta 6 jugadores en dimensiones estadísticas a tu elección. Los radares de percentiles se superponen para una comparación visual inmediata.</p>

          <h2>Raw Data</h2>
          <p>La tabla de datos completa: más de 180 columnas, filtrado avanzado, exportación. Para quienes quieren hacer sus propios análisis en Excel o Python.</p>

          <p>Entra al laboratorio en la <a href="/nerd-zone">sección Nerd Zone</a>.</p>
        `,
      },
      fr: {
        title: "Nerd Zone : BI Analytics en Mode Dieu",
        category: "Guide",
        excerpt:
          "<p>Nuages de points interactifs, radars multidimensionnels, données brutes. Pour ceux qui veulent voir les chiffres sans filtre, avec un contrôle total sur les axes, les filtres et les métriques.</p>",
        content: `
          <h2>La Nerd Zone</h2>
          <p>La <strong>Nerd Zone</strong> est le laboratoire de données de Barsport.club. Pas de storytelling, pas d'éditoriaux : seulement des données brutes, des graphiques interactifs et la liberté d'explorer comme vous le souhaitez.</p>

          <h2>Bubble Scatter</h2>
          <p>Le nuage de points interactif : choisissez les axes X et Y, la taille des bulles (Z) et la couleur par rôle. Chaque bulle est un joueur. Explorez les corrélations, les valeurs aberrantes et les tendances du marché.</p>

          <h2>Radar Compare</h2>
          <p>Comparez jusqu'à 6 joueurs sur des dimensions statistiques de votre choix. Les radars de percentiles se superposent pour une comparaison visuelle immédiate.</p>

          <h2>Raw Data</h2>
          <p>Le tableau de données complet : plus de 180 colonnes, filtrage avancé, exportation. Pour ceux qui veulent faire leurs propres analyses dans Excel ou Python.</p>

          <p>Entrez dans le laboratoire dans la <a href="/nerd-zone">section Nerd Zone</a>.</p>
        `,
      },
      de: {
        title: "Nerd Zone: BI Analytics im God Mode",
        category: "Leitfaden",
        excerpt:
          "<p>Interaktive Scatter-Plots, multidimensionale Radare, Rohdaten. Für alle, die Zahlen ungefiltert sehen wollen, mit voller Kontrolle über Achsen, Filter und Metriken.</p>",
        content: `
          <h2>Die Nerd Zone</h2>
          <p>Die <strong>Nerd Zone</strong> ist Barsport.clubs Datenlabor. Kein Storytelling, keine Leitartikel: nur Rohdaten, interaktive Diagramme und die Freiheit, nach Belieben zu erkunden.</p>

          <h2>Bubble Scatter</h2>
          <p>Der interaktive Scatter-Plot: wähle X- und Y-Achsen, Blasengröße (Z) und Farbe nach Rolle. Jede Blase ist ein Spieler. Erforsche Korrelationen, Ausreißer und Markttrends.</p>

          <h2>Radar Compare</h2>
          <p>Vergleiche bis zu 6 Spieler anhand frei wählbarer statistischer Dimensionen. Die Perzentil-Radare überlagern sich für einen sofortigen visuellen Vergleich.</p>

          <h2>Raw Data</h2>
          <p>Die vollständige Datentabelle: über 180 Spalten, erweiterte Filterung, Export. Für alle, die ihre eigenen Analysen in Excel oder Python durchführen möchten.</p>

          <p>Betritt das Labor in der <a href="/nerd-zone">Nerd Zone-Sektion</a>.</p>
        `,
      },
    },
  },
];

/**
 * Ottiene la traduzione di un articolo per una data lingua.
 * Fallback: DE → IT se la lingua richiesta non è disponibile.
 */
export function getArticleTranslation(
  article: BlogArticleData,
  locale: BlogArticleLocale
): BlogArticleTranslation {
  return (
    article.translations[locale] || article.translations["de"] || article.translations["it"]
  );
}

/**
 * Converte BlogArticleData in formato WpPost per una data lingua.
 */
export function toWpPost(
  article: BlogArticleData,
  locale: BlogArticleLocale = "it"
): {
  id: number;
  slug: string;
  title: { rendered: string };
  excerpt: { rendered: string };
  content: { rendered: string };
  date: string;
  _embedded: {
    "wp:featuredmedia": Array<{ source_url: string; alt_text: string; media_details: { sizes: { medium: { source_url: string } } } }>;
  };
} {
  const t = getArticleTranslation(article, locale);
  return {
    id: article.id,
    slug: article.slug,
    title: { rendered: t.title },
    excerpt: { rendered: t.excerpt },
    content: { rendered: t.content },
    date: article.date,
    _embedded: {
      "wp:featuredmedia": [
        {
          source_url: article.hero_image,
          alt_text: t.title,
          media_details: {
            sizes: {
              medium: {
                source_url: article.hero_image,
              },
            },
          },
        },
      ],
    },
  };
}
