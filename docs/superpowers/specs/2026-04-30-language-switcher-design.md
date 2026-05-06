# Language Switcher — Design Spec

**Date:** 2026-04-30
**Scope:** Add a global language switcher to `UniversalHeader`. Client-side only (localStorage persistence). No URL routing changes.

---

## Goal

Allow users to switch between IT / EN / ES / FR / DE from any page. Selection persists across reloads via `localStorage`. The existing `react-i18next` + `i18n/config.ts` infrastructure is reused — no new libraries.

## Out of scope

Next.js i18n URL routing (`/[lang]/...`), middleware, or server-side locale detection. That is a separate feature tracked as a follow-up.

---

## Architecture

```
layout.tsx (server component)
  └── I18nWrapper.tsx  ("use client" boundary)
        ├── I18nProvider (detects & applies browser/localStorage lang after hydration)
        └── UniversalHeader
              └── LanguageSwitcher (co-located in UniversalHeader.tsx)
```

`layout.tsx` stays a pure server component. The `"use client"` boundary is isolated to `I18nWrapper.tsx`.

---

## Components

### `app/components/I18nWrapper.tsx` (new)

- `"use client"`
- Renders `<I18nProvider>{children}</I18nProvider>`
- Accepts `children: React.ReactNode`
- No other logic

### `app/layout.tsx` (modified)

- Import `I18nWrapper`
- Wrap `<UniversalHeader />` and `<main>` inside `<I18nWrapper>`

### `LanguageSwitcher` (co-located in `UniversalHeader.tsx`)

**Languages:**

| Code | Label | localStorage value |
|------|-------|--------------------|
| ITA  | Italiano | `it` |
| ENG  | English  | `en` |
| ESP  | Español  | `es` |
| FRA  | Français | `fr` |
| DEU  | Deutsch  | `de` |

**Behaviour:**

- SSR / hydration: `isMounted` state starts `false`. Before mount, renders a `<div className="w-16 h-8" />` skeleton — prevents hydration mismatch because server and first client render agree.
- After mount: reads `i18n.language` to show current code.
- Button click: toggles `isOpen` state.
- Dropdown closes on:
  - Selecting a language
  - Click outside (`mousedown` listener added/removed in `useEffect`)
  - `Escape` key (`keydown` listener added/removed in `useEffect`)
- Language change: calls `i18n.changeLanguage(code)`, writes `code` to `localStorage` under `STORAGE_KEY` (imported from `app/i18n/config.ts`).

**Styling:**

- Button: `text-sm font-bold tracking-widest text-slate-400 hover:text-white transition-colors` + pink underline when dropdown open
- Dropdown: `absolute right-0 top-full mt-1 bg-[#0d2137] border border-slate-700 rounded shadow-xl z-50 min-w-[120px]`
- Option row: `px-4 py-2 text-sm font-bold tracking-wider cursor-pointer hover:bg-slate-800 transition-colors`
- Active language: `text-[#FF2A6D]`; inactive: `text-slate-300`

**Responsive:**

- Desktop: `LanguageSwitcher` placed after the `<nav>` block inside the flex row, `flex-shrink-0`
- Mobile: nav links are `hidden md:flex`; the switcher is always visible. On very small screens (`< sm`) the label collapses to the 3-letter code only (no sub-label).

**Accessibility:**

- Trigger button: `aria-haspopup="listbox"`, `aria-expanded={isOpen}`
- Dropdown `<ul>`: `role="listbox"`
- Each `<li>`: `role="option"`, `aria-selected={lang.code === currentCode}`

---

## Files

| File | Action |
|------|--------|
| `app/components/I18nWrapper.tsx` | Create |
| `app/layout.tsx` | Modify — add `I18nWrapper` |
| `app/components/UniversalHeader.tsx` | Modify — add `LanguageSwitcher` + `isMounted` guard |

---

## Non-goals

- No emoji / flag images (Windows rendering bug)
- No URL-based routing
- No server-side locale detection
- No changes to locale JSON files
