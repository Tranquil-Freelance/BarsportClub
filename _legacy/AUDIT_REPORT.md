# Spring Cleaning Audit Report

**Generated:** 2026-04-30  
**Scope:** Full project directory (`c:/Users/euron/Desktop/claude of control`)  
**Methodology:** Import-graph analysis, dependency cross-reference, manual inspection

---

## Table of Contents

1. [Unused Frontend Files](#1-unused-frontend-files)
2. [Legacy Root-Level Files](#2-legacy-root-level-files)
3. [Legacy Backend Scripts](#3-legacy-backend-scripts)
4. [Legacy Backend Data / Artifacts](#4-legacy-backend-data--artifacts)
5. [Legacy Scrapers & Old Code](#5-legacy-scrapers--old-code)
6. [Dependency Audit](#6-dependency-audit)
7. [Archive Strategy Proposal](#7-archive-strategy-proposal)

---

## 1. Unused Frontend Files

### 1.1 Orphan Components (`frontend/components/`)

These components live in `frontend/components/` but **zero files** import them via `@/components/...` or any relative path. The active app uses components under `frontend/app/components/` instead.

| File | Size | Notes |
|------|------|-------|
| [`MatchCard.tsx`](frontend/components/MatchCard.tsx) | ~3 KB | Superseded by match widgets in `app/components/home/` |
| [`MatchLineupPitch.tsx`](frontend/components/MatchLineupPitch.tsx) | ~8 KB | Scout Engine has its own `MatchLineupPitch` |
| [`MeritometroCard.tsx`](frontend/components/MeritometroCard.tsx) | ~2 KB | Meritometro route uses inline rendering |
| [`Navbar.tsx`](frontend/components/Navbar.tsx) | ~5 KB | App uses `homepage/Navbar.tsx` or `navigation/PalermoNavbar.tsx` |
| [`PremiumShotMap.tsx`](frontend/components/PremiumShotMap.tsx) | ~10 KB | Duplicate of `app/components/PremiumShotMap.tsx` |
| [`ShotMap.tsx`](frontend/components/ShotMap.tsx) | ~8 KB | Nerd Zone has its own `ShotMap` |
| [`TacticalBoard.tsx`](frontend/components/TacticalBoard.tsx) | ~6 KB | App uses `app/components/TacticalBoard.tsx` |
| [`xGFlowChart.tsx`](frontend/components/xGFlowChart.tsx) | ~4 KB | Not imported anywhere |

**Exception:** [`TeamLogo.tsx`](frontend/components/TeamLogo.tsx) IS actively used — **keep in place**.

### 1.2 Standalone HTML / Text Files

These sit in the `frontend/` root and are **not part of the Next.js build**:

| File | Description |
|------|-------------|
| [`fanta_dashboard.html`](frontend/fanta_dashboard.html) | 504-line standalone HTML dashboard (pre-Next.js prototype) |
| [`finder.html`](frontend/finder.html) | 1308-line standalone HTML page (old search tool) |
| [`response.txt`](frontend/response.txt) | Raw API response dump (debug artifact) |

### 1.3 `frontend/docs/` — Out of Place

| File | Description |
|------|-------------|
| [`frontend/docs/superpowers/plans/2026-04-24-global-i18n-hydration.md`](frontend/docs/superpowers/plans/2026-04-24-global-i18n-hydration.md) | Plan doc inside frontend/ — root-level `docs/` already exists |

> **Recommendation:** Move to root `docs/superpowers/plans/` for consistency.

---

## 2. Legacy Root-Level Files

| File | Description |
|------|-------------|
| [`package.json`](package.json) | Contains `echarts`, `framer-motion`, `lucide-react` — these are frontend deps. The root `package.json` is **unused** (frontend has its own). |
| [`package-lock.json`](package-lock.json) | Lock file for the orphan root `package.json` |
| [`FANTA_DRAFT_ENGINE_SQL.md`](FANTA_DRAFT_ENGINE_SQL.md) | SQL reference doc — could be **kept** as documentation, but out of place at root |
| [`lineup_response.json`](lineup_response.json) | Raw API response dump (debug artifact) |

**Active files at root (DO NOT TOUCH):**
- [`main.py`](main.py) — Re-exports FastAPI app for uvicorn
- [`docker-compose.yml`](docker-compose.yml) — Defines the 3-service stack

---

## 3. Legacy Backend Scripts

### 3.1 Root-Level Python Scripts (`backend/*.py`) — All Legacy

These are **standalone scripts** not part of `backend/app/`. They were used for one-off data fixes, DB migrations, experiments, etc.

| Category | Files |
|----------|-------|
| **DB fixes** | `add_missing_columns.py`, `add_missing_columns_matches.py`, `add_round_column.py`, `add_unification_columns.py`, `add_xpts_column.py`, `add_xpts_column2.py`, `aggiusta_tabelle.py`, `alter_shots.py`, `clean_db.py`, `clean_nan.py`, `fix_future_dates.py`, `fix_missing_goals.py`, `fix_null_rounds.py`, `fix_team_names.py`, `fix_teams.py`, `force_db_fix.py`, `force_fix_db.py`, `pulisci_db.py`, `purge_mock_data.py`, `rimuovi_vincolo.py` |
| **DB inspection** | `check_columns.py`, `check_columns2.py`, `check_columns3.py`, `check_default_db.py`, `check_existing_subs.py`, `check_match_data.py`, `check_player_in_ids.py`, `check_player_registry.py`, `check_positions.py`, `check_sub_2024.py`, `check_subs.py`, `check_subs_schema.py`, `check_team_data.py`, `check_team_name.py`, `check_tiri.py`, `conta_match.py`, `count_matches_by_league.py`, `count_shots.py`, `explore_db.py`, `explore_db2.py`, `explore_db3.py`, `ispeziona_db.py`, `list_columns.py`, `list_tables.py`, `lista_squadre.py`, `query_existing_matches.py`, `query_existing_shots.py`, `query_match.py` |
| **Data seeding** | `populate_10_matches.py`, `populate_player_in.py`, `seed_standings.py`, `insert_static_match.py`, `insert_test_match.py`, `insert_test_match2.py`, `insert_test_match_calendar.py`, `costruisci_db.py`, `create_football_tables.py`, `create_substitutions_table.py`, `create_tables.py`, `ensure_tables.py`, `init_como_data_fixed.py`, `init_new_tables.py` |
| **DB sync/migration** | `aggiorna_db.py`, `migrate_substitutions.py`, `reset_scraped.py`, `reset_seriea.py`, `sync_giornate.py`, `trigger_sync.py`, `run_sync_2025.py`, `global_update.py`, `recupero_serie_a.py`, `europa_full_harvester.py` |
| **Scraper utils** | `batch_injector.py`, `debug_asyncpg_schema.py`, `debug_comunicazione.py`, `debug_match_lineup_data.py`, `decode_match_info.py`, `delete_mock_rows.py`, `delete_mock_rows2.py`, `delete_remaining_mock.py`, `delete_remaining_mock2.py`, `espandi_calendario.py`, `final_test.py`, `find_player_mapping.py`, `forza_partita.py`, `get_first_match.py`, `get_first_match_sqlite.py`, `scoutengine.py`, `sofifa.py`, `scheduler.py` |
| **Testing** | `test_async_sub.py`, `test_emergenza.py`, `test_lineup_fix.py`, `test_merito.py`, `test_mvgi.py`, `test_player.py`, `test_query.py`, `test_report.py`, `test_sync.py`, `test_tubature.py` |
| **Other** | `chi_sono.py`, `meritometro_ai.py`, `engine_barsport.py`, `replacement_engine.py`, `riconcilia.py`, `main.py` (different from root main.py) |

### 3.2 `backend/app/services/metrics_engine.py` — Python file in frontend service dir

[`frontend/app/services/metrics_engine.py`](frontend/app/services/metrics_engine.py) is a **Python file** living inside `frontend/app/services/` — it's a standalone metrics calculator, **not importable by TypeScript/Next.js**. It appears to be a misplaced backend component.

---

## 4. Legacy Backend Data / Artifacts

| File | Description |
|------|-------------|
| [`backend/players.csv`](backend/players.csv) | Old CSV data dump |
| [`backup_full_scout.sql`](backend/backup_full_scout.sql) | Full database backup (likely stale) |
| [`seriea_deep_data_2025_FIXED.json`](backend/seriea_deep_data_2025_FIXED.json) | JSON data export |
| [`seriea_deep_data_2025_PARZIALE.json`](backend/seriea_deep_data_2025_PARZIALE.json) | JSON data export (partial) |
| [`server_log.txt`](backend/server_log.txt) | Server log from debugging sessions |
| [`firefox_fail.png`](backend/firefox_fail.png) | Browser screenshot (scraper debug) |
| [`debug_match_output.html`](backend/debug_match_output.html) | HTML debug output |
| [`debug_page.html`](backend/debug_page.html) | HTML debug output |
| [`debug_timeout.html`](backend/debug_timeout.html) | HTML debug output |
| [`error_page.html`](backend/error_page.html) | HTML debug output |

### 4.1 `backend/imports/` — Old Match Imports

Contains scraped match data from an old scraper pipeline:
- [`Cagliari 1 - 2 Como.html`](backend/imports/Cagliari%201%20-%202%20Como.html)
- [`shots_30116.json`](backend/imports/shots_30116.json)
- `Cagliari 1 - 2 Como_files/` (20+ `.download` files — JS, CSS, fonts)

### 4.2 `backend/html_imports/` — Historical Season JSON

28 JSON files with per-season per-league data (2020–2025), plus a [`dbeaver-ce-26.0.1-windows-x86_64.exe`](backend/html_imports/dbeaver-ce-26.0.1-windows-x86_64.exe) installer (should not be in a project repo).

### 4.3 `backend/migrations/`

[`backend/migrations/001_add_performance_indexes.sql`](backend/migrations/001_add_performance_indexes.sql) — Single migration file. Potentially useful but **not referenced** by the active app (no Alembic setup).

---

## 5. Legacy Scrapers & Old Code

### 5.1 `backend/scrapers/` — Legacy Scraper Implementations

These are **not imported** by the active app (`backend/app/`). They are alternative scraper implementations predating the current `sniper_protocol.py` system:

| File | Description |
|------|-------------|
| [`understat.py`](backend/scrapers/understat.py) | Old Understat scraper class |
| [`understat_scraper.py`](backend/scrapers/understat_scraper.py) | Older scraper variant |
| [`understat_lib.py`](backend/scrapers/understat_lib.py) | Scraper library functions |
| [`soccerdata_engine.py`](backend/scrapers/soccerdata_engine.py) | SoccerData-based approach |
| [`palermo_full_season.py`](backend/scrapers/palermo_full_season.py) | Palermo-specific season scraper |

**Note:** `backend/app/services/understat_service.py` does a `try/except` import from `scrapers.understat import UnderstatScraper` — the active service **still references** this legacy scraper as a fallback. It should be reviewed before archiving.

### 5.2 `backend/core/scrapers/` — 80+ Debug/Experimental Scrapers

This is a graveyard of scraper experiments:

- `broad_scan.py`, `quick_scan.py`, `quick_scan2.py`
- `extract_*.py` (10+ files for extracting IDs, variables, match data, etc.)
- `fetch_*.py` (10+ files for fetching various endpoints)
- `find_*.py` (6+ files for finding matches, URLs, variables)
- `inspect_*.py` (10+ files for inspecting data)
- `search_*.py` (10+ files for searching)
- `scan_como*.py`, `sync_*.py`, `temp_*.py`, and more

### 5.3 `backend/scripts/` — 25 More Legacy Scripts

Another set of one-off scripts: `aggiornamento_bundes.py`, `audit_dati.py`, `scraper_seriea.py`, `scraper_bundesliga.py`, etc.

Many of these replicate functionality now handled by `sniper_protocol.py`.

### 5.4 `backend/archive/debug_legacy/` — Already Archived Debug Scripts

87 files already collected in `backend/archive/debug_legacy/`. These include:
- 40+ `check_*.py` files
- 30+ `test_*.py` files  
- JSON dumps (`match_27362.json`, `matches_limit5.json`, `playerradar.json`, etc.)
- HTML debug output

> These are **already archived** — just need to be moved to `_legacy/` along with everything else.

### 5.5 `vecchi_script_backup/` — Old Script Backup

Already named "old scripts backup":
- `assess_dummy.py`, `batch_scrape_*.py`, `check_*.py`, `debug_*.py`, `delete_dummy.py`, `execute_query.py`, `fetch_api.py`, `get_match.py`, `list_*.py`, `query_*.py`

### 5.6 `vecchia app/` — Old App Structure

A previous version of the backend app structure:
- `api/crud.py`, `api/app/api/analytics.py`
- `db/database.py`, `db/models.py`
- `scraper/scraper_orchestrator.py`, `scraper/understat_engine.py`
- `tasks/updater.py`

### 5.7 `scripts/` — Root-level Scripts

[`scripts/map_understat_ids.py`](scripts/map_understat_ids.py) — Appears to be a utility for mapping player IDs.

### 5.8 `show claude/` — Old Exports

- [`show claude/finder1.html`](show%20claude/finder1.html)
- [`show claude/scout1.txt`](show%20claude/scout1.txt)

---

## 6. Dependency Audit

### 6.1 Root `package.json` — **Entirely Unused**

The frontend app runs from `frontend/` with its own `package.json`. The root `package.json` is an orphan:

| Package | Status | Notes |
|---------|--------|-------|
| `echarts` ^6.0.0 | ❌ UNUSED | `frontend/package.json` has its own version |
| `echarts-for-react` ^3.0.6 | ❌ UNUSED | — |
| `framer-motion` ^12.36.0 | ❌ UNUSED | — |
| `lucide-react` ^0.577.0 | ❌ UNUSED | `frontend/` uses v0.574.0 |

### 6.2 `frontend/package.json` — All Dependencies Used ✅

| Package | Used In | Status |
|---------|---------|--------|
| `next` ^16.2.1 | Core framework | ✅ Used |
| `react` ^19.0.0 / `react-dom` ^19.0.0 | Core | ✅ Used |
| `lucide-react` ^0.574.0 | 47 files | ✅ Used |
| `framer-motion` ^12.38.0 | 23 files | ✅ Used |
| `recharts` ^3.7.0 | 11 files | ✅ Used |
| `i18next` ^26.0.8 / `react-i18next` ^17.0.6 | 7 files | ✅ Used |
| `echarts` ^6.0.0 / `echarts-for-react` ^3.0.6 | 5 files | ✅ Used |
| `swr` ^2.4.1 | 5 files | ✅ Used |
| `gray-matter` ^4.0.3 | `articles.ts` | ✅ Used |
| `remark` ^15.0.1 / `remark-html` ^16.0.1 | `articles.ts` | ✅ Used |
| `clsx` ^2.1.1 | `fanta-draft/page.tsx` | ✅ Used |
| `tailwindcss` ^3.4.0 / `postcss` ^8.4.38 / `autoprefixer` ^10.4.19 | Build tooling | ✅ Used |
| `tailwindcss-animate` ^1.0.7 / `@tailwindcss/typography` ^0.5.19 | `tailwind.config.ts` | ✅ Used |
| Dev deps (types, eslint, cross-env) | Build/lint | ✅ Used |

### 6.3 `backend/requirements.txt` — Potential Bloat

Many packages are likely unused. Notable candidates for removal:

| Package | Likely Purpose | Status |
|---------|---------------|--------|
| `behave` ^1.2.6 | BDD testing | ❌ Probably unused |
| `pdbp` ^1.8.2 | Debugger | ❌ Debug tool |
| `pynose` ^1.5.5 | Test runner | ❌ Probably unused |
| `pyotp` ^2.9.0 | 2FA | ❌ Unrelated to football |
| `pyreadline3` ^3.5.4 | Windows readline | ❌ Probably unused |
| `pytest-html` ^4.0.2 | Test reports | ❌ Probably unused |
| `pytest-metadata` ^3.1.1 | Test plugin | ❌ Probably unused |
| `pytest-ordering` ^0.6 | Test ordering | ❌ Probably unused |
| `pytest-rerunfailures` ^15.1 | Flaky test retry | ❌ Probably unused |
| `pytest-xdist` ^3.6.1 | Parallel test runner | ❌ Probably unused |
| `tabcompleter` ^1.4.0 | REPL helper | ❌ Probably unused |
| `wrapper-tls-requests` ^1.2.5 | TLS wrapper | ❌ Probably unused |
| `sbvirtualdisplay` ^1.4.0 | Selenium virtual display | ⚠️ Old scraper infra (now uses `sniper_protocol`) |
| `selenium` ^4.32.0 / `seleniumbase` ^4.38.3 | Browser automation | ⚠️ Old scraper infra |

> **Full audit of `requirements.txt`** would require checking each import across `backend/app/` — recommend deferring to a follow-up.

---

## 7. Archive Strategy Proposal

### Proposed `_legacy/` Structure

```
_legacy/
├── .gitignore                  # ensure _legacy/ is gitignored
│
├── README.md                   # Explain what _legacy/ is for
│
├── frontend/
│   ├── components/             # 8 orphan components (minus TeamLogo)
│   │   ├── MatchCard.tsx
│   │   ├── MatchLineupPitch.tsx
│   │   ├── MeritometroCard.tsx
│   │   ├── Navbar.tsx
│   │   ├── PremiumShotMap.tsx
│   │   ├── ShotMap.tsx
│   │   ├── TacticalBoard.tsx
│   │   └── xGFlowChart.tsx
│   ├── fanta_dashboard.html
│   ├── finder.html
│   └── response.txt
│
├── root/
│   ├── package.json            # orphan root package.json
│   ├── package-lock.json
│   ├── lineup_response.json
│   └── FANTA_DRAFT_ENGINE_SQL.md   # (optional — could stay)
│
├── backend/
│   ├── scripts/                # All standalone root scripts
│   │   ├── add_missing_columns.py
│   │   ├── ... (all 100+ *.py files)
│   │   └── (keep directory structure flat or by category)
│   ├── scrapers/               # Legacy scraper implementations
│   │   ├── understat.py
│   │   ├── understat_scraper.py
│   │   ├── understat_lib.py
│   │   ├── soccerdata_engine.py
│   │   └── palermo_full_season.py
│   ├── core/scrapers/          # 80+ experimental scraper files
│   │   └── (entire directory)
│   ├── imports/                # Old match HTML imports
│   │   └── (entire directory)
│   ├── html_imports/           # Historical season JSON
│   │   └── (entire directory)
│   ├── archive/                # Already-archived debug files
│   │   └── (keep nested as-is)
│   ├── migrations/             # Single migration (review before archiving)
│   │   └── 001_add_performance_indexes.sql
│   ├── data/                   # Data artifacts
│   │   ├── players.csv
│   │   ├── backup_full_scout.sql
│   │   ├── seriea_deep_data_2025_FIXED.json
│   │   ├── seriea_deep_data_2025_PARZIALE.json
│   │   ├── server_log.txt
│   │   ├── firefox_fail.png
│   │   ├── debug_match_output.html
│   │   ├── debug_page.html
│   │   ├── debug_timeout.html
│   │   └── error_page.html
│   └── metrics_engine.py       # from frontend/app/services/
│
├── vecchi_script_backup/       # Move entire directory
├── vecchia app/                # Move entire directory
├── scripts/                    # Root-level scripts
│   └── map_understat_ids.py
└── show claude/                # Old exports
    ├── finder1.html
    └── scout1.txt
```

### `.gitignore` Addition

Append to existing `.gitignore`:

```gitignore
# Legacy/archived files
_legacy/
```

### Migration Procedure (after your approval)

1. Create `_legacy/` directory at project root
2. Create subdirectories per structure above
3. `git mv` each candidate file into place
4. Add `_legacy/` to `.gitignore`
5. Verify the app still runs (`docker-compose up`)
6. Commit

### Items Requiring Special Review Before Archiving

| Item | Reason |
|------|--------|
| [`backend/app/services/understat_service.py`](backend/app/services/understat_service.py) | Still `try/except`-imports `scrapers.understat.UnderstatScraper` — refactor first |
| [`backend/scrapers/understat.py`](backend/scrapers/understat.py) | Referenced by `understat_service.py` — resolve dependency before moving |
| [`frontend/docs/...`](frontend/docs/superpowers/plans/2026-04-24-global-i18n-hydration.md) | Should move to root `docs/` instead of `_legacy/` |
| [`backend/migrations/001_add_performance_indexes.sql`](backend/migrations/001_add_performance_indexes.sql) | May still be needed for new DB deployments — consider keeping in `backend/migrations/` |
| [`FANTA_DRAFT_ENGINE_SQL.md`](FANTA_DRAFT_ENGINE_SQL.md) | Documentation — consider moving to `docs/` instead of `_legacy/` |
| [`frontend/package-lock.json`](frontend/package-lock.json) | ⚠️ DO NOT TOUCH — required by npm |

---

*Report generated by automated audit. All items listed are candidates for archiving — no files have been moved or deleted.*
