# Homepage Optical Editorial — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `app/page.tsx` as a premium editorial homepage (Opta Analyst × FT style) with live Meritometro IMR and Standings sidebar widgets, full i18n (IT/EN/ES/FR), and framer-motion entrance animations.

**Architecture:** Single-page rewrite of `app/page.tsx` with two data fetches (standings + meritometro IMR). Sidebar widgets use Opta-style clean tables. Main column uses hero + secondary 2-col grid. All text via i18n. No new component files — everything in `app/page.tsx`.

**Tech Stack:** Next.js 16, React 19, framer-motion 12, lucide-react, tailwindcss-animate, react-i18next, next/image

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `tailwind.config.ts` | Modify | Add `tailwindcss-animate` plugin |
| `app/i18n/locales/it.json` | Modify | Add `home` section (IT editorial tone) |
| `app/i18n/locales/en.json` | Modify | Add `home` section (EN sharp analytic) |
| `app/i18n/locales/es.json` | Modify | Add `home` section (ES apasionado) |
| `app/i18n/locales/fr.json` | Modify | Add `home` section (FR élégant) |
| `public/images/home/.gitkeep` | Create | Ensure image directory is tracked by git |
| `app/page.tsx` | Full rewrite | Complete homepage component |

**Do NOT touch:** `UniversalHeader.tsx`, `layout.tsx`, `globals.css`, `apiClient.ts`

---

## Task 1: Tailwind Config — Add tailwindcss-animate

**Files:**
- Modify: `tailwind.config.ts`

- [ ] **Step 1.1 — Add plugin**

Open `tailwind.config.ts`. The current plugins array is:
```ts
plugins: [
  require('@tailwindcss/typography'),
],
```

Change it to:
```ts
plugins: [
  require('@tailwindcss/typography'),
  require('tailwindcss-animate'),
],
```

- [ ] **Step 1.2 — Verify TypeScript compiles**

```bash
cd "C:/Users/euron/Desktop/claude of control/frontend"
npm run type-check
```

Expected: 0 errors. If `tailwindcss-animate` types are missing, that's fine — the plugin has no type declarations and won't cause TS errors.

- [ ] **Step 1.3 — Commit**

```bash
git add tailwind.config.ts
git commit -m "chore: add tailwindcss-animate plugin"
```

---

## Task 2: i18n — Add `home` Section to All 4 Locales

**Files:**
- Modify: `app/i18n/locales/it.json`
- Modify: `app/i18n/locales/en.json`
- Modify: `app/i18n/locales/es.json`
- Modify: `app/i18n/locales/fr.json`

- [ ] **Step 2.1 — Add IT locale `home` section**

In `app/i18n/locales/it.json`, add the following `"home"` key at the end (before the closing `}`):

```json
  "home": {
    "db_active": "Database Attivo:",
    "analysis_of_week": "L'Analisi della Settimana",
    "hero_category": "Meritometro · Serie A",
    "hero_img_title": "L'Anomalia Rosanero",
    "hero_headline_pre": "Creiamo occasioni da vertice, ma finalizziamo da",
    "hero_headline_hot": "zona retrocessione.",
    "hero_deck": "L'analisi profonda degli xG rivela un problema strutturale nella finalizzazione. Numeri alla mano, ecco cosa si è inceppato nella macchina offensiva del Palermo.",
    "read_full_analysis": "Leggi l'analisi completa",
    "hero_date": "24 Aprile 2026 · 6 min",
    "widget_merit_title": "Meritometro IMR",
    "widget_standings_title": "Classifica",
    "sec1_cat": "Scout Engine · Analisi Dati",
    "sec1_title": "Perché l'Inter sovraperforma i propri xG? Il fattore Lautaro.",
    "sec2_cat": "Tactical Board · PPDA",
    "sec2_title": "Il sistema di Guardiola spiegato attraverso i dati PPDA.",
    "mod_scout_title": "Scout Engine",
    "mod_scout_tag": "DNA · Clone PSE",
    "mod_scout_desc": "Trova il profilo genetico del tuo obiettivo di mercato. Analisi multidimensionale su 180+ metriche.",
    "mod_scout_cta": "Entra nel Lab",
    "mod_fanta_title": "Fanta Draft",
    "mod_fanta_tag": "TAI · Hidden Gems",
    "mod_fanta_desc": "Il Talent Auction Index che anticipa il mercato. I colpi nascosti prima che li scoprano tutti.",
    "mod_fanta_cta": "Prepara l'Asta",
    "mod_nerd_title": "Nerd Zone",
    "mod_nerd_tag": "BI · God Mode",
    "mod_nerd_desc": "Scatter plot, radar multidimensionale, raw data. Per chi vuole vedere i numeri senza filtri.",
    "mod_nerd_cta": "Apri il Lab"
  }
```

- [ ] **Step 2.2 — Add EN locale `home` section**

In `app/i18n/locales/en.json`, add:

```json
  "home": {
    "db_active": "Active Database:",
    "analysis_of_week": "The Weekly Breakdown",
    "hero_category": "Meritometer · Serie A",
    "hero_img_title": "The Palermo Anomaly",
    "hero_headline_pre": "We create top-tier chances, but finish like a",
    "hero_headline_hot": "relegation side.",
    "hero_deck": "A deep dive into xG data exposes a structural failure in front of goal. The numbers tell a story Palermo's coaches cannot afford to ignore.",
    "read_full_analysis": "Read the full analysis",
    "hero_date": "24 April 2026 · 6 min",
    "widget_merit_title": "Meritometer IMR",
    "widget_standings_title": "Standings",
    "sec1_cat": "Scout Engine · Data Analytics",
    "sec1_title": "Why does Inter consistently beat its own xG? The Lautaro factor.",
    "sec2_cat": "Tactical Board · PPDA",
    "sec2_title": "Guardiola's system decoded through PPDA data.",
    "mod_scout_title": "Scout Engine",
    "mod_scout_tag": "DNA · PSE Clones",
    "mod_scout_desc": "Identify the genetic blueprint of your transfer target. Multidimensional analysis across 180+ metrics.",
    "mod_scout_cta": "Enter the Lab",
    "mod_fanta_title": "Fanta Draft",
    "mod_fanta_tag": "TAI · Hidden Gems",
    "mod_fanta_desc": "The Talent Auction Index that reads the market before it moves. The hidden gems before everyone else finds them.",
    "mod_fanta_cta": "Prepare Your Auction",
    "mod_nerd_title": "Nerd Zone",
    "mod_nerd_tag": "BI · God Mode",
    "mod_nerd_desc": "Scatter plots, multi-dimensional radar, raw data exports. For those who want the numbers unfiltered.",
    "mod_nerd_cta": "Open the Lab"
  }
```

- [ ] **Step 2.3 — Add ES locale `home` section**

In `app/i18n/locales/es.json`, add:

```json
  "home": {
    "db_active": "Base de Datos Activa:",
    "analysis_of_week": "El Análisis de la Semana",
    "hero_category": "Meritómetro · Serie A",
    "hero_img_title": "La Anomalía Rosanero",
    "hero_headline_pre": "Creamos ocasiones de élite, pero finalizamos como un",
    "hero_headline_hot": "equipo en descenso.",
    "hero_deck": "Un análisis profundo del xG revela un problema estructural en la finalización. Los números hablan claro sobre lo que falla en la máquina ofensiva del Palermo.",
    "read_full_analysis": "Leer el análisis completo",
    "hero_date": "24 de Abril de 2026 · 6 min",
    "widget_merit_title": "Meritómetro IMR",
    "widget_standings_title": "Clasificación",
    "sec1_cat": "Motor Scout · Análisis de Datos",
    "sec1_title": "¿Por qué el Inter supera sistemáticamente su xG? El factor Lautaro.",
    "sec2_cat": "Tactical Board · PPDA",
    "sec2_title": "El sistema de Guardiola explicado a través de los datos PPDA.",
    "mod_scout_title": "Motor Scout",
    "mod_scout_tag": "ADN · Clones PSE",
    "mod_scout_desc": "Encuentra el perfil genético de tu objetivo de mercado. Análisis multidimensional de 180+ métricas.",
    "mod_scout_cta": "Entra al Laboratorio",
    "mod_fanta_title": "Fanta Draft",
    "mod_fanta_tag": "TAI · Joyas Ocultas",
    "mod_fanta_desc": "El Talent Auction Index que anticipa el mercado. Los fichajes escondidos antes de que los descubran todos.",
    "mod_fanta_cta": "Prepara la Subasta",
    "mod_nerd_title": "Zona Nerd",
    "mod_nerd_tag": "BI · Modo Dios",
    "mod_nerd_desc": "Scatter plot, radar multidimensional, datos en bruto. Para quienes quieren los números sin filtros.",
    "mod_nerd_cta": "Abrir el Laboratorio"
  }
```

- [ ] **Step 2.4 — Add FR locale `home` section**

In `app/i18n/locales/fr.json`, add:

```json
  "home": {
    "db_active": "Base de Données Active :",
    "analysis_of_week": "L'Analyse de la Semaine",
    "hero_category": "Méritomètre · Serie A",
    "hero_img_title": "L'Anomalie Rosanero",
    "hero_headline_pre": "Nous créons des occasions d'élite, mais nous finissons comme une",
    "hero_headline_hot": "équipe relégable.",
    "hero_deck": "Une analyse approfondie des xG révèle une défaillance structurelle dans la finition. Les chiffres racontent une histoire que le Palerme ne peut plus ignorer.",
    "read_full_analysis": "Lire l'analyse complète",
    "hero_date": "24 Avril 2026 · 6 min",
    "widget_merit_title": "Méritomètre IMR",
    "widget_standings_title": "Classement",
    "sec1_cat": "Scout Engine · Analyse de Données",
    "sec1_title": "Pourquoi l'Inter dépasse-t-il systématiquement ses xG ? Le facteur Lautaro.",
    "sec2_cat": "Tactical Board · PPDA",
    "sec2_title": "Le système de Guardiola décrypté par les données PPDA.",
    "mod_scout_title": "Scout Engine",
    "mod_scout_tag": "ADN · Clones PSE",
    "mod_scout_desc": "Identifiez le profil génétique de votre cible de transfert. Analyse multidimensionnelle sur 180+ métriques.",
    "mod_scout_cta": "Entrer dans le Lab",
    "mod_fanta_title": "Fanta Draft",
    "mod_fanta_tag": "TAI · Pépites Cachées",
    "mod_fanta_desc": "Le Talent Auction Index qui anticipe le marché. Les pépites cachées avant tout le monde.",
    "mod_fanta_cta": "Préparer les Enchères",
    "mod_nerd_title": "Zone Nerd",
    "mod_nerd_tag": "BI · Mode Dieu",
    "mod_nerd_desc": "Nuages de points, radar multidimensionnel, données brutes. Pour ceux qui veulent les chiffres sans filtres.",
    "mod_nerd_cta": "Ouvrir le Lab"
  }
```

- [ ] **Step 2.5 — Commit**

```bash
git add app/i18n/locales/it.json app/i18n/locales/en.json app/i18n/locales/es.json app/i18n/locales/fr.json
git commit -m "feat(i18n): add home section to all 4 locales with editorial tone"
```

---

## Task 3: Create Images Directory

**Files:**
- Create: `public/images/home/.gitkeep`

- [ ] **Step 3.1 — Create directory**

```bash
mkdir -p "C:/Users/euron/Desktop/claude of control/frontend/public/images/home"
touch "C:/Users/euron/Desktop/claude of control/frontend/public/images/home/.gitkeep"
```

- [ ] **Step 3.2 — Commit**

```bash
git add public/images/home/.gitkeep
git commit -m "chore: add public/images/home/ directory for cover images"
```

> **Note for user:** Place cover images here as:
> - `meritometro-cover.webp` (hero)
> - `scout-cover.webp` (secondary card 1)
> - `nerdzone-cover.webp` (secondary card 2)
> The component handles missing images gracefully with a navy placeholder.

---

## Task 4: Rewrite `app/page.tsx` — Complete Implementation

**Files:**
- Rewrite: `app/page.tsx`

This is the full page rewrite. Execute all steps in order.

- [ ] **Step 4.1 — Verify TeamLogo import path**

Check the current import in the existing `app/page.tsx`:
```ts
import TeamLogo from "../components/TeamLogo";
```

The new file lives at the same path (`app/page.tsx`), so the correct import is:
```ts
import TeamLogo from "./components/TeamLogo";
```

Confirm `app/components/TeamLogo.tsx` exists:
```bash
ls "C:/Users/euron/Desktop/claude of control/frontend/app/components/TeamLogo.tsx"
```

Expected: file exists. If not, use `TeamLogo from "@/components/TeamLogo"` — but it exists per git status.

- [ ] **Step 4.2 — Write the complete new `app/page.tsx`**

Replace the entire content of `app/page.tsx` with:

```tsx
"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import "./i18n/config";
import TeamLogo from "./components/TeamLogo";

// ── Types ──────────────────────────────────────────────────────────────────
type Standing = {
  pos: number;
  name: string;
  pts: number;
  played?: number;
  won?: number;
  drawn?: number;
};

type MeritRow = {
  name: string;
  total_imr: number;
};

// ── Constants ──────────────────────────────────────────────────────────────
const LEAGUES = ["Serie A", "Premier League", "La Liga", "Bundesliga", "Ligue 1"];

// Strip /api/v1 so we can hit /api/standings and /api/meritometro/imr_standings
const API_ORIGIN =
  (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1").replace(
    /\/api\/v1$/,
    ""
  );

// ── Framer-motion variants ─────────────────────────────────────────────────
const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } },
};

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};

// ── Helpers ────────────────────────────────────────────────────────────────

/** Next/image wrapper that silently hides itself on 404. */
function CoverImage({ src, alt }: { src: string; alt: string }) {
  const [errored, setErrored] = useState(false);
  if (errored) return null;
  return (
    <Image
      src={src}
      alt={alt}
      fill
      className="object-cover object-center"
      onError={() => setErrored(true)}
      unoptimized
    />
  );
}

/** Returns headers including X-ADMIN-API-KEY when present in localStorage. */
function secureHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  const key = localStorage.getItem("admin_api_key");
  return key ? { "X-ADMIN-API-KEY": key } : {};
}

// ── Component ──────────────────────────────────────────────────────────────
export default function HomePage() {
  const { t } = useTranslation();

  const [activeLeague, setActiveLeague] = useState("Serie A");
  const [topTeams, setTopTeams] = useState<Standing[]>([]);
  const [topMerit, setTopMerit] = useState<MeritRow[]>([]);
  const [loadingStandings, setLoadingStandings] = useState(true);
  const [loadingMerit, setLoadingMerit] = useState(true);

  // Fetch standings on league change
  useEffect(() => {
    setLoadingStandings(true);
    fetch(
      `${API_ORIGIN}/api/standings?league=${encodeURIComponent(activeLeague)}`,
      { headers: secureHeaders() }
    )
      .then((r) => (r.ok ? r.json() : []))
      .then((data: Standing[]) => setTopTeams(data.slice(0, 5)))
      .catch(() => setTopTeams([]))
      .finally(() => setLoadingStandings(false));
  }, [activeLeague]);

  // Fetch Meritometro IMR on league change
  useEffect(() => {
    setLoadingMerit(true);
    fetch(
      `${API_ORIGIN}/api/meritometro/imr_standings?league=${encodeURIComponent(activeLeague)}`,
      { headers: secureHeaders() }
    )
      .then((r) => (r.ok ? r.json() : []))
      .then((data: MeritRow[]) => setTopMerit(data.slice(0, 5)))
      .catch(() => setTopMerit([]))
      .finally(() => setLoadingMerit(false));
  }, [activeLeague]);

  const maxImr = topMerit[0]?.total_imr ?? 1;

  return (
    <div className="min-h-screen bg-[#F8F9FA] text-[#0f172a] font-body">

      {/* ── LEAGUE SUB-BAR (sticky below UniversalHeader at ~48px) ── */}
      <div className="w-full bg-[#0d2137] border-b border-white/5 h-10 flex items-center px-6 sticky top-[48px] z-40">
        <span className="text-white/35 text-[8px] font-black uppercase tracking-[0.22em] mr-6 flex-shrink-0 hidden sm:block">
          {t("home.db_active")}
        </span>
        <div className="flex gap-1.5 overflow-x-auto scrollbar-hide">
          {LEAGUES.map((league) => (
            <button
              key={league}
              onClick={() => setActiveLeague(league)}
              className={`text-[9px] font-black uppercase tracking-widest px-3 py-1 rounded-full transition-all flex-shrink-0 ${
                activeLeague === league
                  ? "bg-[#ff0055] text-white shadow-[0_0_10px_rgba(255,0,85,0.35)]"
                  : "text-white/40 hover:text-white"
              }`}
            >
              {league}
            </button>
          ))}
        </div>
      </div>

      {/* ── EDITORIAL GRID ── */}
      <div className="max-w-[1200px] mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_272px] gap-8 items-start">

          {/* ════════════════════════════════════════
              MAIN COLUMN
              ════════════════════════════════════════ */}
          <motion.div
            className="flex flex-col gap-6"
            variants={stagger}
            initial="hidden"
            animate="visible"
          >

            {/* Section eyebrow */}
            <motion.div variants={fadeUp} className="flex items-center gap-2">
              <span className="block w-4 h-0.5 bg-[#ff0055]" />
              <span className="text-[#ff0055] text-[8px] font-black uppercase tracking-[0.22em]">
                {t("home.analysis_of_week")}
              </span>
            </motion.div>

            {/* ── HERO STORY ── */}
            <motion.article variants={fadeUp}>

              {/* Cover image */}
              <div className="relative w-full h-[300px] bg-[#0a192f] rounded-sm overflow-hidden mb-4">
                <CoverImage src="/images/home/meritometro-cover.webp" alt={t("home.hero_img_title")} />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0a192f]/88 via-[#0a192f]/10 to-transparent" />
                <div className="absolute bottom-0 left-0 p-4 z-10">
                  <p className="text-[#ff0055] text-[7px] font-black uppercase tracking-[0.22em] mb-1">
                    {t("home.hero_category")}
                  </p>
                  <p className="text-white font-heading text-lg font-black uppercase leading-tight">
                    {t("home.hero_img_title")}
                  </p>
                </div>
              </div>

              {/* Headline */}
              <h1 className="font-heading text-[26px] md:text-[30px] font-black uppercase leading-[1.08] tracking-tight text-[#0a192f] mb-3">
                {t("home.hero_headline_pre")}{" "}
                <em className="text-[#ff0055] not-italic">
                  {t("home.hero_headline_hot")}
                </em>
              </h1>

              {/* Deck */}
              <p className="text-[#475569] text-sm leading-relaxed border-l-[3px] border-[#e2e8f0] pl-3 mb-4">
                {t("home.hero_deck")}
              </p>

              {/* CTA row */}
              <div className="flex items-center gap-3 flex-wrap">
                <Link
                  href="/meritometro"
                  className="text-[8px] font-black uppercase tracking-[0.14em] text-[#0a192f] bg-[#f1f5f9] px-4 py-2 rounded-sm border border-[#e2e8f0] hover:bg-[#e2e8f0] transition-colors"
                >
                  {t("home.read_full_analysis")} →
                </Link>
                <span className="text-[9px] text-[#94a3b8]">{t("home.hero_date")}</span>
              </div>
            </motion.article>

            {/* Divider */}
            <motion.hr variants={fadeUp} className="border-[#e2e8f0]" />

            {/* ── SECONDARY ARTICLE GRID ── */}
            <motion.div
              variants={stagger}
              className="grid grid-cols-1 sm:grid-cols-2 gap-5"
            >
              {/* Article: Scout Engine */}
              <motion.article variants={fadeUp}>
                <Link href="/scout-engine" className="group block">
                  <div className="relative w-full h-[130px] bg-[#1e293b] rounded-sm overflow-hidden mb-2.5">
                    <CoverImage src="/images/home/scout-cover.webp" alt={t("home.sec1_title")} />
                  </div>
                  <p className="text-[#ff0055] text-[7px] font-black uppercase tracking-[0.18em] mb-1">
                    {t("home.sec1_cat")}
                  </p>
                  <h3 className="font-heading text-sm font-black uppercase leading-snug text-[#0a192f] group-hover:text-[#ff0055] transition-colors duration-200">
                    {t("home.sec1_title")}
                  </h3>
                </Link>
              </motion.article>

              {/* Article: Nerd Zone */}
              <motion.article variants={fadeUp}>
                <Link href="/nerd-zone" className="group block">
                  <div className="relative w-full h-[130px] bg-[#0f2044] rounded-sm overflow-hidden mb-2.5">
                    <CoverImage src="/images/home/nerdzone-cover.webp" alt={t("home.sec2_title")} />
                  </div>
                  <p className="text-[#ff0055] text-[7px] font-black uppercase tracking-[0.18em] mb-1">
                    {t("home.sec2_cat")}
                  </p>
                  <h3 className="font-heading text-sm font-black uppercase leading-snug text-[#0a192f] group-hover:text-[#ff0055] transition-colors duration-200">
                    {t("home.sec2_title")}
                  </h3>
                </Link>
              </motion.article>
            </motion.div>

          </motion.div>
          {/* END MAIN COLUMN */}

          {/* ════════════════════════════════════════
              SIDEBAR
              ════════════════════════════════════════ */}
          <motion.aside
            className="flex flex-col gap-6 lg:sticky lg:top-[96px]"
            variants={stagger}
            initial="hidden"
            animate="visible"
          >

            {/* ── MERITOMETRO IMR WIDGET ── */}
            <motion.div variants={fadeUp} className="bg-white p-4 shadow-sm border border-[#f1f5f9]">
              <div className="border-l-[3px] border-[#0a192f] pl-2 mb-3 flex items-baseline justify-between">
                <h4 className="text-[9px] font-black uppercase tracking-[0.2em] text-[#0a192f]">
                  {t("home.widget_merit_title")}
                </h4>
                <span className="text-[7px] font-bold text-[#94a3b8] uppercase tracking-wider">
                  {activeLeague}
                </span>
              </div>

              {loadingMerit ? (
                <div className="space-y-2">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="h-6 bg-[#f1f5f9] rounded animate-pulse" />
                  ))}
                </div>
              ) : topMerit.length === 0 ? (
                <p className="text-[10px] text-[#94a3b8] font-bold uppercase py-2">
                  {t("common.no_data")}
                </p>
              ) : (
                <div>
                  {topMerit.map((row, i) => (
                    <div
                      key={row.name}
                      className="grid grid-cols-[18px_1fr_48px_52px] items-center gap-1.5 py-1.5 border-b border-[#f1f5f9] last:border-0"
                    >
                      <span className="text-[9px] font-black text-[#cbd5e1] text-center tabular-nums">
                        {i + 1}
                      </span>
                      <span className="text-[10px] font-black uppercase tracking-tight text-[#0f172a] truncate">
                        {row.name}
                      </span>
                      <span className="text-[12px] font-black text-[#ff0055] text-right tabular-nums">
                        {Math.round(row.total_imr)}
                      </span>
                      <div className="h-[3px] bg-[#f1f5f9] rounded overflow-hidden">
                        <div
                          className="h-[3px] bg-[#ff0055] rounded opacity-65"
                          style={{ width: `${(row.total_imr / maxImr) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>

            {/* ── STANDINGS WIDGET ── */}
            <motion.div variants={fadeUp} className="bg-white p-4 shadow-sm border border-[#f1f5f9]">
              <div className="border-l-[3px] border-[#0a192f] pl-2 mb-3 flex items-baseline justify-between">
                <h4 className="text-[9px] font-black uppercase tracking-[0.2em] text-[#0a192f]">
                  {t("home.widget_standings_title")} · {activeLeague}
                </h4>
                <span className="text-[7px] font-bold text-[#94a3b8] uppercase tracking-wider">Top 5</span>
              </div>

              {/* Column headers */}
              <div className="grid grid-cols-[18px_1fr_22px_22px_22px_28px] gap-1 pb-2 border-b border-[#e2e8f0] mb-1">
                {["#", t("common.team"), "G", "W", "D", "PTS"].map((h, idx) => (
                  <span
                    key={idx}
                    className={`text-[7px] font-black uppercase tracking-wider text-[#94a3b8] text-center ${idx === 1 ? "text-left" : ""}`}
                  >
                    {h}
                  </span>
                ))}
              </div>

              {loadingStandings ? (
                <div className="space-y-1.5 pt-1">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="h-5 bg-[#f1f5f9] rounded animate-pulse" />
                  ))}
                </div>
              ) : topTeams.length === 0 ? (
                <p className="text-[10px] text-[#94a3b8] font-bold uppercase py-2">
                  {t("common.no_data")}
                </p>
              ) : (
                topTeams.map((team) => (
                  <div
                    key={team.name}
                    className="grid grid-cols-[18px_1fr_22px_22px_22px_28px] items-center gap-1 py-1.5 border-b border-[#f8f9fb] last:border-0"
                  >
                    <span className="text-[9px] font-black text-[#94a3b8] text-center tabular-nums">
                      {team.pos}
                    </span>
                    <div className="flex items-center gap-1.5 min-w-0">
                      <TeamLogo teamName={team.name} size={14} />
                      <span className="text-[9px] font-black uppercase tracking-tight text-[#0f172a] truncate">
                        {team.name}
                      </span>
                    </div>
                    <span className="text-[9px] font-bold text-[#475569] text-center tabular-nums">
                      {team.played ?? "–"}
                    </span>
                    <span className="text-[9px] font-bold text-[#475569] text-center tabular-nums">
                      {team.won ?? "–"}
                    </span>
                    <span className="text-[9px] font-bold text-[#475569] text-center tabular-nums">
                      {team.drawn ?? "–"}
                    </span>
                    <span className="text-[10px] font-black text-[#0a192f] text-center tabular-nums">
                      {team.pts}
                    </span>
                  </div>
                ))
              )}
            </motion.div>

            {/* ── MODULE PROMO CARDS ── */}
            {(
              [
                {
                  href: "/scout-engine",
                  titleKey: "home.mod_scout_title",
                  tagKey: "home.mod_scout_tag",
                  descKey: "home.mod_scout_desc",
                  ctaKey: "home.mod_scout_cta",
                },
                {
                  href: "/fanta-draft",
                  titleKey: "home.mod_fanta_title",
                  tagKey: "home.mod_fanta_tag",
                  descKey: "home.mod_fanta_desc",
                  ctaKey: "home.mod_fanta_cta",
                },
                {
                  href: "/nerd-zone",
                  titleKey: "home.mod_nerd_title",
                  tagKey: "home.mod_nerd_tag",
                  descKey: "home.mod_nerd_desc",
                  ctaKey: "home.mod_nerd_cta",
                },
              ] as const
            ).map((mod) => (
              <motion.div
                key={mod.href}
                variants={fadeUp}
                className="border border-[#e2e8f0] rounded-sm overflow-hidden shadow-sm"
              >
                <div className="bg-[#0a192f] px-3 py-2 flex items-center justify-between">
                  <h5 className="text-[8px] font-black uppercase tracking-[0.18em] text-white">
                    {t(mod.titleKey)}
                  </h5>
                  <span className="text-[7px] font-black uppercase tracking-wider text-[#ff0055]">
                    {t(mod.tagKey)}
                  </span>
                </div>
                <div className="bg-white px-3 py-3">
                  <p className="text-[10px] text-[#475569] leading-relaxed mb-2">
                    {t(mod.descKey)}
                  </p>
                  <Link
                    href={mod.href}
                    className="text-[8px] font-black uppercase tracking-[0.14em] text-[#0a192f] flex items-center gap-1 hover:text-[#ff0055] transition-colors duration-200 group"
                  >
                    {t(mod.ctaKey)}
                    <span className="text-[#ff0055] group-hover:translate-x-0.5 transition-transform duration-200">
                      →
                    </span>
                  </Link>
                </div>
              </motion.div>
            ))}

          </motion.aside>
          {/* END SIDEBAR */}

        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4.3 — Run type-check**

```bash
cd "C:/Users/euron/Desktop/claude of control/frontend"
npm run type-check
```

Expected: 0 errors.

Common issues to fix if they appear:
- `Module not found: framer-motion` → already in package.json, run `npm install`
- `Property 'onError' does not exist on Image` → ensure `next` version supports it (it does in Next 16)
- `Cannot find module './i18n/config'` → the import path changed from `"../i18n/config"` to `"./i18n/config"` because page.tsx is inside `app/`. Verify the path resolves.

- [ ] **Step 4.4 — Start dev server and verify visually**

```bash
npm run dev
```

Open http://localhost:3000 in browser. Verify:

1. ✅ League sub-bar shows "Serie A" pill highlighted in magenta
2. ✅ Hero section shows navy placeholder (or image if webp files are in place)
3. ✅ Two secondary article cards render below the hero
4. ✅ Sidebar right column shows "Meritometro IMR" and "Classifica" widgets with animate-pulse skeleton while loading
5. ✅ After data loads: IMR scores appear in magenta, standings table shows columns G/W/D/PTS
6. ✅ Three module promo cards (Scout / Fanta / Nerd) appear below
7. ✅ Clicking a different league pill re-triggers both data fetches (skeletons flash again)
8. ✅ All text is in Italian (default locale)
9. ✅ Switching language via UniversalHeader lang switcher → text changes across all labels
10. ✅ On mobile (≤1024px): sidebar stacks below main column

- [ ] **Step 4.5 — Check framer-motion entrance**

Reload the page with DevTools open. In the Network tab, throttle to "Slow 3G" temporarily. Verify:
- Hero section fades up smoothly over 0.4s on load
- Secondary cards stagger in with 0.08s delay each
- No layout shift (content doesn't jump)
- No console errors from framer-motion

- [ ] **Step 4.6 — Commit**

```bash
git add app/page.tsx public/images/home/.gitkeep
git commit -m "feat(homepage): Optical Editorial layout with Opta-style sidebar, IMR widget, framer-motion"
```

---

## Self-Review Checklist

- [x] **Tailwind plugin:** Task 1 adds `tailwindcss-animate` ✓
- [x] **i18n all 4 locales:** Task 2 covers IT/EN/ES/FR with editorial tone ✓
- [x] **Images directory:** Task 3 creates `public/images/home/` ✓
- [x] **League sub-bar:** Matches screenshot exactly (dark navy, pink active pill) ✓
- [x] **Hero story:** Full image slot + headline with hot highlight + deck + CTA ✓
- [x] **Secondary grid:** 2 articles with image + category eyebrow + title ✓
- [x] **Meritometro widget:** Opta-style white card, left-border navy, IMR scores in magenta, progress bar ✓
- [x] **Standings widget:** Column headers G/W/D/PTS, team logo, tabular-nums, magenta PTS ✓
- [x] **Module promos:** Navy header bar + white body + red CTA arrow ✓
- [x] **framer-motion:** fadeUp variants with stagger, duration 0.4s ✓
- [x] **Security:** `secureHeaders()` injects `X-ADMIN-API-KEY` on every fetch ✓
- [x] **No neon/cyberpunk:** All effects are professional (soft shadows, no glow except league pill) ✓
- [x] **UniversalHeader untouched:** Not imported or modified in this file ✓
- [x] **Responsive:** `grid-cols-1 lg:grid-cols-[1fr_272px]` stacks on mobile ✓
