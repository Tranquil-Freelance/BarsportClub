# Scout Engine Overhaul — Design Spec
**Date:** 2026-04-27  
**Project:** barsport.club  
**Scope:** Full overhaul of `frontend/app/scout-engine/` and related backend endpoints

---

## 1. Goals

- Eliminate slow initial load (no 5000+ player fetch on mount)
- Fix Cloni PSI drill-down bug
- Rebuild H2H Duel with Statbomb-style laser radar (Recharts)
- Expand TalentRadar to Top 5 leagues with 5 intelligence categories
- Silence the console (hydration errors, 404 image logs, hardcoded ports)
- Split 1293-line monolith into maintainable component files

---

## 2. Architecture

### Frontend file structure

```
frontend/app/scout-engine/
├── page.tsx                    # Shell only: tab state, search bar, route (~120 lines)
├── components/
│   ├── HomeTab.tsx             # Leaders leaderboard
│   ├── TargetTab.tsx           # DNA Target + shot map + radar
│   ├── ReplaceTab.tsx          # Cloni PSI with drill-down
│   ├── H2HTab.tsx              # H2H Duel with Recharts LaserRadar
│   ├── DiscoverTab.tsx         # TalentRadar sidebar war room
│   ├── PitchSVG.tsx            # Shot map SVG (extracted)
│   ├── LaserRadar.tsx          # Recharts overlapping radar (shared)
│   └── SearchHub.tsx           # Reusable search bar + suggestions
├── hooks/
│   ├── usePlayerSearch.ts      # SWR: lightweight search (name/team only)
│   ├── usePlayerDNA.ts         # SWR: full stats, on-demand
│   ├── usePlayerReplacement.ts # SWR: PSE clones, keyed on player name
│   └── useTalentRadar.ts       # SWR: keyed on {category, league, pos}
└── lib/
    └── scoutApi.ts             # Typed fetch helpers, API URL constants
```

### Backend additions (`backend/app/api/scout_routes.py`)

New endpoints — existing endpoints unchanged:

| Endpoint | Description |
|---|---|
| `GET /api/scout/talent-radar` | Intelligence categories query. Params: `category`, `league`, `pos`, `limit` |
| `GET /api/shots/player?name={name}` | Player shot map (was called by frontend but never implemented) |

---

## 3. Data Fetching

**Rule:** No stats loaded until a player is selected by the user.

| Hook | SWR key | Fetches | Cache |
|---|---|---|---|
| `usePlayerSearch` | `['search', q]` when `q.length >= 2` | `name, team` only | 60s |
| `usePlayerDNA` | `['dna', name]` when name set | `/dna` + `/radar` + `/shots/player` in parallel | 5 min |
| `usePlayerReplacement` | `['replace', name]` | `/replacement` | 5 min |
| `useTalentRadar` | `['talent', category, league, pos]` | `/talent-radar` | 5 min |

**Global SWR config:**
```ts
{
  revalidateOnFocus: false,
  errorRetryCount: 2,
  dedupingInterval: 300_000,
}
```

HomeTab leaders: fetched once on mount via SWR with 5-minute cache. No change to behavior.

---

## 4. Bug Fixes

### Cloni PSI drill-down (was: redirect to DNA Target)
- `ReplaceTab` receives `onDrillDown(name: string)` prop
- Clicking a clone card calls `setReplacementTarget(name)` on `usePlayerReplacement`
- Tab stays on "replace"; SWR re-fetches clones for the new target
- Breadcrumb trail rendered above the target bar: `Leão → Thuram → ...` with back navigation

### H2H dual search
- Two independent `SearchHub` instances, one per player slot
- Each manages its own `query` state
- Eliminates the `(!p1 ? setP1 : setP2)` sequential fill logic

### Console cleanup
| Source | Fix |
|---|---|
| `components/ShotMap.tsx` hardcoded `http://127.0.0.1:8001` | Replace with `process.env.NEXT_PUBLIC_API_URL` |
| German strings in `ShotMap.tsx` | Replace with Italian/English |
| Player headshot 404s | `onError` fallback to `/images/player-placeholder.svg` |
| `echarts-for-react` hydration errors | Eliminated by Recharts migration |
| `useEffect` missing dep warnings | Resolved by SWR hooks (no manual effect dep arrays) |

---

## 5. H2H Duel — Laser Radar

### Layout
```
┌─────────────────────────────────────────────────┐
│  [Search Challenger 1]   [Search Challenger 2]  │
├──────────────────┬──────────────────────────────┤
│  Stat card P1    │  Stat card P2                │  ← white cards, color-coded top border
├──────────────────┴──────────────────────────────┤
│         RECHARTS OVERLAPPING RADAR              │  ← white bg, laser neon
│      xG/90 · Goals/90 · xA/90 · xGChain · CII  │
├─────────────────────────────────────────────────┤
│  METRIC COMPARISON TABLE (6 rows)               │  ← winner highlighted per row
└─────────────────────────────────────────────────┘
```

### `LaserRadar.tsx` spec
- `RadarChart` + `PolarGrid` + `PolarAngleAxis` + `PolarRadiusAxis` from recharts
- **Challenger 1:** `stroke="#00D1FF"` `fill="rgba(0,209,255,0.20)"` `strokeWidth={2.5}`
- **Challenger 2:** `stroke="#FF5C00"` `fill="rgba(255,92,0,0.20)"` `strokeWidth={2.5}`
- SVG `<filter id="laser-glow">` with `feGaussianBlur stdDeviation="3"` injected via `customized` prop
- Overlap interference: additive alpha compositing (~0.40 combined opacity) — no extra code
- Dot `r={5}` with matching glow filter
- Axes: percentile 0–100, same 5 metrics as existing radar
- White background (`#FFFFFF`), `shadow-sm` on outer container

### Metric comparison table
- 6 rows: PIR · OIS · xG/90 · xA/90 · FES · CII
- Winner per row: colored background pill matching their laser color
- Loser: muted `text-slate-400`
- No borders — `bg-slate-50` alternating rows

---

## 6. TalentRadar — Sidebar War Room

### Layout
```
┌──────────────┬──────────────────────────────────────────┐
│ 💎 DIAMONDS  │  [SerieA][PL][BL][Liga][L1]   pos: [▾]  │
│ 💰 MONEYBALL │  ──────────────────────────────────────  │
│ 🚜 ENGINE    │  Category title + description            │
│ 🎯 UNLUCKY   │                                          │
│ 🔥 OVER      │  [card][card][card][card]                │
│              │  [card][card][card][card]                │
│  bg:#0A192F  │  bg:#F8F9FA, cards: #FFFFFF shadow-sm   │
└──────────────┴──────────────────────────────────────────┘
```

### Intelligence categories — backend SQL logic

All queries extend `_FROM_JOIN` with a `HAVING` clause. The `league` param replaces the hardcoded `Serie A` league name lookup.

| Category | HAVING filter | Sort |
|---|---|---|
| 💎 Hidden Diamonds | `SUM(time) BETWEEN 300 AND 1200 AND SUM("xGChain") / NULLIF(SUM(time),0) * 90 > 0.40` | xGChain/90 DESC |
| 💰 Moneyball | `SUM("xGBuildup") / NULLIF(SUM(time),0) * 90 > 0.20 AND SUM("xG") < 2.0` | xGBuildup/90 DESC |
| 🚜 Engine Room | `SUM(key_passes) / NULLIF(SUM(time),0) * 90 > 1.5 AND SUM("xGBuildup") / NULLIF(SUM(time),0) * 90 > 0.15` | xGBuildup/90 DESC |
| 🎯 Unlucky Masters | `SUM("xG") > 3.0 AND SUM(goals) <= 1` | SUM(xG) DESC |
| 🔥 Overperformers | `SUM(goals) > SUM("xG") * 1.5 AND SUM(shots) >= 5` | (SUM(goals) - SUM(xG)) DESC |

### New backend endpoint
```
GET /api/scout/talent-radar?category={diamonds|moneyball|engine|unlucky|overperformers}
                             &league={serie_a|pl|bundesliga|liga|ligue1}
                             &pos=ALL
                             &limit=24
```

### Player cards
- White `#FFFFFF` card, `shadow-sm`
- Left border color per category: cyan (Diamonds) / green (Moneyball) / amber (Engine) / purple (Unlucky) / red (Overperformers)
- Hero metric displayed large, then 3 mini stats below
- Click → `loadPlayer(name, "target")` (navigates to DNA Target)

---

## 7. Color System

| Token | Value | Used for |
|---|---|---|
| `bg-page` | `#F8F9FA` | All tab content backgrounds |
| `bg-panel` | `#FFFFFF` | All cards, stat tiles, radar panels — `shadow-sm` |
| `bg-sidebar` | `#0A192F` | TalentRadar left sidebar **only** |
| `bg-header` | `#0A192F` | Page header + tab bar |
| `text-primary` | `#334155` | Body text on light backgrounds |
| `text-muted` | `#94A3B8` | Secondary labels |
| `accent-red` | `#FF2A6D` | Brand accent (tabs, borders, PIR) |
| `laser-blue` | `#00D1FF` | H2H Challenger 1, Diamonds category |
| `laser-orange` | `#FF5C00` | H2H Challenger 2 |

Dark navy (`#0A192F`) appears **only** in: page header, tab bar, TalentRadar sidebar.

---

## 8. Implementation Order

1. Backend: add `/api/shots/player` endpoint
2. Backend: add `/api/scout/talent-radar` endpoint with 5 category filters
3. Frontend: create `lib/scoutApi.ts` + 4 SWR hooks
4. Frontend: extract `SearchHub.tsx`, `LaserRadar.tsx`, `PitchSVG.tsx`
5. Frontend: rebuild `H2HTab.tsx` (white bg + Recharts + dual search)
6. Frontend: rebuild `DiscoverTab.tsx` (sidebar war room + intelligence categories)
7. Frontend: rebuild `ReplaceTab.tsx` (drill-down fix + breadcrumb)
8. Frontend: rebuild `TargetTab.tsx` + `HomeTab.tsx` (light panels)
9. Frontend: rebuild `page.tsx` shell
10. Console cleanup: ShotMap port fix, image fallbacks, German strings
11. Create `/public/images/player-placeholder.svg`
