# Homepage Redesign — Optical Editorial
**Date:** 2026-04-24  
**Status:** Approved  
**Style Reference:** theanalyst.com (Opta Analyst) × Financial Times

---

## 1. Concept

barsport.club transitions from a dark-theme app to a **Football Intelligence Magazine**. The page reads like a premium editorial publication: clean white canvas, authoritative typography, data surfaces that feel like data journalism — not dashboards.

Tone: *"If Opta Analyst and the Financial Times had a child dedicated to football."*

---

## 2. Color System

| Token | Value | Usage |
|---|---|---|
| `navy` | `#0a192f` | Topbar, widget headers, left-border accents, CTAs |
| `hot` | `#ff0055` | All live data (IMR, xG, goals, TAI), eyebrow rules, active states |
| `canvas` | `#f8f9fb` | Page background, card backgrounds |
| `subtle` | `#f1f5f9` | Alternating rows, secondary backgrounds |
| `border` | `#e2e8f0` | All dividers and card borders |
| `body-text` | `#475569` | Article decks and descriptions |
| `headline` | `#0f172a` | Headlines, team names, data labels |
| `muted` | `#94a3b8` | Timestamps, secondary labels, column headers |

---

## 3. Typography

- **Heading font:** Oswald (`var(--font-oswald)`) — all uppercase labels, section eyebrows, headline H1/H2
- **Body font:** Inter (`var(--font-inter)`) — decks, descriptions, data tables
- **Eyebrow pattern:** `8px / 900 weight / uppercase / tracking-[0.22em] / #ff0055` + 14px red rule left
- **Data numbers:** `font-variant-numeric: tabular-nums` everywhere

---

## 4. Layout Architecture

```
┌─────────────────────────────────────────────────────┐
│  UniversalHeader (sticky, navy)                     │
│  [logo] [nav: Campionati Apuestas Meritómetro...]  │
│  [lang switcher: IT/EN/ES/FR]                       │
├─────────────────────────────────────────────────────┤
│  League Sub-bar (sticky, #0d2137)                   │
│  DATABASE ATTIVO: [Serie A●] [PL] [La Liga] ...    │
├─────────────────────┬───────────────────────────────┤
│  MAIN COLUMN        │  SIDEBAR (272px, white bg)    │
│  (flex: 1)          │                               │
│  ─ Section eyebrow  │  Widget: Meritometro IMR      │
│  ─ Hero image slot  │  Widget: Standings table      │
│  ─ Hero headline    │  Promo: Scout Engine          │
│  ─ Hero deck        │  Promo: Fanta Draft           │
│  ─ CTA link         │  Promo: Nerd Zone             │
│  ─ Divider          │                               │
│  ─ 2-col sec grid   │                               │
├─────────────────────┴───────────────────────────────┤
│  Footer (navy, minimal)                             │
└─────────────────────────────────────────────────────┘
```

**Max-width:** 1200px, centered. Grid: `1fr 272px`.  
**Responsive:** Stack to single column at `lg` breakpoint (1024px).

---

## 5. Component Specs

### 5.1 Hero Story
- Full-width image: `w-full aspect-[16/9]` or fixed `h-[320px]`, `object-cover`
- Image source: `public/images/home/[slug].webp` — passed as prop per article
- Gradient overlay: `linear-gradient(to top, rgba(10,25,47,0.88), transparent 55%)`
- Floating caption (category + short title) on bottom-left over image
- Below image: uppercase H1, italic magenta highlight on key phrase, deck paragraph, CTA button

### 5.2 Secondary Article Grid
- 2 columns, `gap-4`
- Each card: image thumbnail (`h-[120px]`), category eyebrow, title
- Images: `public/images/home/[slug].webp`
- On hover: title color transitions to `#ff0055`

### 5.3 Sidebar — Meritometro Widget
- Header: left-border `3px solid #0a192f`, small-caps label + matchday badge
- Rows: `rank | team-name | IMR-score | progress-bar`
- Progress bar: 3px high, `#ff0055` at 0.65 opacity, relative to max score
- Scores fetched from `GET /api/meritometro/top?league={activeLeague}&limit=5`

### 5.4 Sidebar — Standings Widget  
- Column headers: `# | Squadra | G | W | D | PTS` (7px muted all-caps)
- Rows: position, logo (32px from `/public/logos/{team}.png`), name, stats, pts
- PTS in navy bold; stats in muted
- Data from `GET /api/standings?league={activeLeague}`

### 5.5 Sidebar — Module Promo Cards
- Header bar: navy bg, white title (Oswald), magenta tag right
- Body: white bg, 10px Inter description, CTA text with `→` red arrow
- Border: `1px solid #e2e8f0`, `border-radius: 4px`
- Links to: `/scout-engine`, `/fanta-draft`, `/nerd-zone`

---

## 6. Animations (framer-motion)

All animations are **invisible to the eye** — they run once on mount, fast, professional:

```ts
const fadeUpVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' } }
}
const staggerContainer = {
  visible: { transition: { staggerChildren: 0.08 } }
}
```

- Hero section: `fadeUp` on mount, `duration: 0.5`
- Secondary cards: `staggerChildren: 0.08` on parent, each card `fadeUp`
- Sidebar widgets: `fadeUp` with `delay: 0.2`
- League sub-bar buttons: `whileTap: { scale: 0.96 }` only — no entrance animation

---

## 7. i18n — Home Section

Add `home` key to all 4 locale files (`it.json`, `en.json`, `es.json`, `fr.json`).

### Keys required:
```json
{
  "home": {
    "analysis_of_week": "...",
    "hero_category": "...",
    "hero_title": "...",
    "hero_deck": "...",
    "read_full_analysis": "...",
    "read_more": "...",
    "db_active": "...",
    "live_data": "...",
    "top5": "Top 5",
    "matchday": "...",
    "scout_desc": "...",
    "scout_cta": "...",
    "fanta_desc": "...",
    "fanta_cta": "...",
    "nerd_desc": "...",
    "nerd_cta": "..."
  }
}
```

### Tone of voice per lingua:
- **IT:** Autorevole, giornalistico, leggermente drammatico. "L'Analisi della Settimana", "Il colpo che nessuno ha visto"
- **EN:** Sharp and analytic. "The Weekly Breakdown", "The Data Doesn't Lie"
- **ES:** Apasionado pero preciso. "El Análisis de la Semana", "Los Números Mandan"
- **FR:** Élégant et incisif. "L'Analyse de la Semaine", "Les Chiffres Parlent"

---

## 8. Tailwind Config Changes

Add `tailwindcss-animate` to `tailwind.config.ts` plugins array:
```ts
plugins: [
  require('@tailwindcss/typography'),
  require('tailwindcss-animate'),   // ← ADD
],
```

---

## 9. File Changes Summary

| File | Action |
|---|---|
| `app/page.tsx` | Full rewrite — Optical Editorial layout |
| `tailwind.config.ts` | Add `tailwindcss-animate` plugin |
| `app/i18n/locales/it.json` | Add `home` section |
| `app/i18n/locales/en.json` | Add `home` section |
| `app/i18n/locales/es.json` | Add `home` section |
| `app/i18n/locales/fr.json` | Add `home` section |
| `public/images/home/` | Create dir (images to be added by user) |

**Do NOT modify:** `UniversalHeader.tsx`, `layout.tsx`, `globals.css`

---

## 10. Data Dependencies

The page fetches from two existing endpoints:
- `GET /api/standings?league={league}` → top 5 standings
- `GET /api/meritometro/imr_standings?league={league}` → IMR full standings (slice to top 5 client-side)

Both use `activeLeague` state (default: `"Serie A"`), updated by the league sub-bar.  
Fetch on `activeLeague` change. Show skeleton loaders (animate-pulse) while loading.

---

## 11. Out of Scope

- Article detail pages (not part of this task)
- CMS or dynamic editorial content
- User authentication
- Mobile nav drawer changes (UniversalHeader handles this already)
