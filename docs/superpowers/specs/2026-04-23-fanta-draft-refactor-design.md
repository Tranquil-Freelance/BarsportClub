# Fanta Draft — Refactoring Strutturale Multi-Lega

**Data:** 2026-04-23  
**Scope:** `backend/app/api/fanta_routes.py` · `frontend/app/fanta-draft/page.tsx`

---

## Obiettivo

Segmentare la sezione Fanta Draft per i 5 campionati europei (Serie A, Premier League, La Liga, Bundesliga, Ligue 1), correggere il bug delle squadre errate tramite logica basata sul match più recente, normalizzare i ruoli e aggiungere l'algoritmo xG/xA Delta per l'identificazione dei Breakout Candidates.

---

## Sezione 1 — Backend (`fanta_routes.py`)

### 1a. Nuovi helper

```python
async def _resolve_league_id(conn, league: str) -> int
```
Lookup `SELECT id FROM league WHERE name ILIKE :n LIMIT 1`. Stesso pattern di `meritometro.py`. Solleva `HTTP 404` se lega non trovata.

```python
def _latest_team_cte_sql() -> str
```
Ritorna il corpo SQL della CTE `latest_team`:

```sql
latest_team AS (
    SELECT DISTINCT ON (r_lt.player_id)
        r_lt.player_id,
        CASE WHEN r_lt.team_type ILIKE 'h%'
             THEN mc_lt.home_team_id
             ELSE mc_lt.away_team_id
        END AS current_team_id
    FROM rosters r_lt
    JOIN matchcalendar mc_lt ON mc_lt.id = r_lt.match_id
        AND mc_lt.is_completed = true
        AND mc_lt.league_id = :league_id
    ORDER BY r_lt.player_id, mc_lt.match_datetime DESC
)
```

- `DISTINCT ON (r_lt.player_id)`: previene bug da omonimie
- `team_type ILIKE 'h%'`: gestisce varianti 'H'/'h'/'Home'
- La CTE è league-scoped: la squadra attuale è quella dell'ultimo match in quella specifica lega

```python
def _combine_cte(base_cte: str, extra_cte_body: str) -> str
```
Se `base_cte` esiste (caso `last5`): appende `",\n" + extra`. Altrimenti: `"WITH\n" + extra`.

### 1b. Normalizzazione posizioni

Rimuove il vecchio `POSITION_MAP` frammentato. Nuovo dict globale:

```python
_POS_NORM = {
    "GK": "GK", "GKP": "GK",
    "DF": "DF", "CB": "DF", "LB": "DF", "RB": "DF", "WB": "DF", "LWB": "DF", "RWB": "DF",
    "MF": "MF", "CM": "MF", "CDM": "MF", "CAM": "MF", "LM": "MF", "RM": "MF",
    "AM": "MF", "DM": "MF", "DMF": "MF", "AMF": "MF",
    "FW": "FW", "LW": "FW", "RW": "FW", "CF": "FW", "ST": "FW", "SS": "FW", "WF": "FW",
}

def _normalize_position(raw: str) -> str:
    if not raw or raw.upper() in ("SUB", "N/D", "UNKNOWN", ""):
        return "N/D"
    return _POS_NORM.get(raw.upper(), "N/D")
```

Applicato su: risultato `MODE()` in `/players`, ruolo in `_compute_percentiles`, posizione in `/auction-strategy`.

### 1c. Modifiche a tutti gli endpoint

Tutti gli endpoint ricevono `league: str = Query("Serie A")`.

**Pattern comune per ogni query:**
1. `league_id = await _resolve_league_id(conn, league)`
2. `cte, extra_join, where = build_filter_parts(filter_type, with_league=True)`
3. `full_cte = _combine_cte(cte, _latest_team_cte_sql())`
4. `AND mc.league_id = :league_id` aggiunto al WHERE principale
5. `GROUP BY r.player, r.player_id` (aggiunta di `r.player_id`)
6. `LEFT JOIN latest_team lt ON lt.player_id = r.player_id`
7. `LEFT JOIN team t_curr ON t_curr.id = lt.current_team_id`
8. `t_curr.name AS team_name` al posto di `MAX(t.name)`

**`build_filter_parts` modificato:**
- Aggiunto param `with_league: bool = False`
- Quando `True` e `filter_type == "last5"`: aggiunge `AND mc_i.league_id = :league_id` dentro il CTE `ranked_matches`

**`_compute_percentiles` modificato:**
- Aggiunto param `league_id: int`
- Aggiunto `AND mc.league_id = :league_id` al WHERE interno
- Percentili calcolati vs peers della stessa lega e dello stesso ruolo normalizzato

**`get_team_attack_index` modificato:**
- Aggiunto param `league_id: int`
- Aggiunto `AND mc.league_id = :league_id` al WHERE

**`/search`:**
- Join a `matchcalendar` con `AND mc.league_id = :league_id`
- Risultati rigorosamente limitati alla lega attiva

**`/dashboard`:**
- Aggiunto `league: str = Query("Serie A")`
- `league_id` risolto e aggiunto al WHERE della query principale
- La `latest_team` CTE applicata anche qui per coerenza (sostituisce `MAX(t.name)`)
- La `legacy_q` (breakdown storico per stagione nel profilo `/player/{id}`) è anch'essa filtrata per `league_id`: le statistiche stagionali mostrano solo i dati della lega selezionata

### 1d. Algoritmo xG Delta / xA Delta

Calcolato in `/players` dopo le metriche p90 esistenti:

```python
goals_p90   = p90(total_goals,   total_minutes)
assists_p90 = p90(total_assists, total_minutes)

xg_delta_p90 = round(max(0.0, xg_p90 - goals_p90), 3)
xa_delta_p90 = round(max(0.0, xa_p90 - assists_p90), 3)

breakout_score = round(
    xg_delta_p90 * FANTASY_PTS_GOAL + xa_delta_p90 * FANTASY_PTS_ASSIST, 2
)
is_breakout = breakout_score >= 0.25 and xg_p90 >= 0.05
```

- Delta **positivo** = giocatore ha prodotto più xG/xA di quanti gol/assist ha realizzato → candidato alla regressione positiva
- Delta negativo = overperformer → non segnalato (non è un rischio che interessa il fantacalcio offensivo)
- Soglia `xg_p90 >= 0.05`: filtra giocatori con troppa poca attività offensiva

Campi aggiunti al response di `/players`: `xg_delta_p90`, `xa_delta_p90`, `breakout_score`, `is_breakout`.

---

## Sezione 2 — Frontend (`fanta-draft/page.tsx`)

### 2a. Stato lega

```typescript
type LeagueId = "Serie A" | "Premier League" | "La Liga" | "Bundesliga" | "Ligue 1"

const LEAGUES: { id: LeagueId; flag: string }[] = [
  { id: "Serie A",        flag: "🇮🇹" },
  { id: "Premier League", flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿" },
  { id: "La Liga",        flag: "🇪🇸" },
  { id: "Bundesliga",     flag: "🇩🇪" },
  { id: "Ligue 1",        flag: "🇫🇷" },
]

const [league, setLeague] = useState<LeagueId>("Serie A")
```

### 2b. UI — Posizionamento tab lega (Layout B approvato)

Tab lega integrate nell'hero section, sotto il sottotitolo esistente. Stile coerente con il resto della pagina (stesso `border`, `hover`, stato `active` con `border-[#FF2A6D]`).

```tsx
{/* Hero — tab lega */}
<div className="flex flex-wrap gap-2 mt-4">
  {LEAGUES.map(l => (
    <button key={l.id} onClick={() => setLeague(l.id)} ...>
      {l.flag} {l.id}
    </button>
  ))}
</div>
```

### 2c. Reset automatico al cambio lega

Al cambio di `league` (dentro `setLeague` handler):
- `setProfile(null)` — chiude profilo aperto
- `setAuctionTargets([])` — svuota auction

Il reset della paginazione interna di `DataTable` è gestito con `useEffect(() => setPage(0), [players])` dentro il componente stesso: ogni volta che l'array `players` cambia (cambio lega o filtro), la pagina torna a 0.

### 2d. Propagazione `league` a tutte le chiamate API

| Chiamata | Parametro aggiunto |
|---|---|
| `/players` | `?filter=...&league=...` |
| `/player/{id}` | `?filter=...&league=...` |
| `/search` | `?q=...&league=...` |
| `/auction-strategy` | `?budget=...&league=...&filter=...` |

`useEffect` per players: deps `[timeFilter, league]`.

---

## Sezione 3 — DataTable UI

### 3a. Nuove colonne

`xGChain/90` e `KeyPass/90` **sostituite** da:

| Chiave | Label | Colore header | Descrizione |
|---|---|---|---|
| `xg_delta_p90` | `xGΔ/90` | `#F59E0B` | xG atteso − Gol reali /90 |
| `xa_delta_p90` | `xAΔ/90` | `#F59E0B` | xA atteso − Assist reali /90 |

Aggiornare `COLS` array in `DataTable` component e `SortKey` type in `FPlayer`.

### 3b. Badge BREAKOUT in DataTable

Nella colonna del nome giocatore: se `p.is_breakout === true`, mostrare badge amber `BREAKOUT` inline. Il badge `STABLE` **non viene mostrato** — troppo rumore visivo, solo il segnale positivo è rilevante.

### 3c. Tipo `FPlayer` aggiornato

```typescript
type FPlayer = {
  // ... campi esistenti ...
  xg_delta_p90: number
  xa_delta_p90: number
  breakout_score: number
  is_breakout: boolean
}
```

---

## Bug critici aggiuntivi da risolvere nel piano

### Bug 1 — Scout Engine: squadre errate (cross-contamination)

**File:** `backend/app/api/scout_routes.py`

**Causa:** Il modulo usa `MAX(t.name) AS team_name` (riga 39) dentro la costante `AGG`, che aggrega su `GROUP BY r.player` senza `player_id`. `MAX` sceglie il nome squadra alfabeticamente più alto tra tutti i match di tutte le leghe e tutte le stagioni → Kane mostra "Wolverhampton", Dybala mostra "Sassuolo".

**Fix:** Aggiungere una CTE cross-league (senza filtro `league_id`) con `DISTINCT ON (r_lt.player_id)`:

```sql
_LATEST_TEAM_CTE AS (
    SELECT DISTINCT ON (r_lt.player_id)
        r_lt.player_id,
        CASE WHEN r_lt.team_type ILIKE 'h%'
             THEN mc_lt.home_team_id
             ELSE mc_lt.away_team_id
        END AS current_team_id
    FROM rosters r_lt
    JOIN matchcalendar mc_lt ON mc_lt.id = r_lt.match_id
        AND mc_lt.is_completed = true
    ORDER BY r_lt.player_id, mc_lt.match_datetime DESC
)
```

Modifiche a `scout_routes.py`:
1. Aggiungere costante `_LATEST_TEAM_SCOUT_CTE` (no `:league_id` — Scout è cross-league)
2. Modificare `AGG`: `MAX(t.name)` → `MAX(t_curr.name) AS team_name`
3. Modificare `_FROM_JOIN`: aggiungere `LEFT JOIN _LATEST_TEAM_SCOUT_CTE lt_x ON lt_x.player_id = r.player_id LEFT JOIN team t_curr ON t_curr.id = lt_x.current_team_id`
4. In ogni endpoint che usa `AGG`: prepend `WITH {_LATEST_TEAM_SCOUT_CTE}` al SELECT e cambiare `GROUP BY r.player` → `GROUP BY r.player, r.player_id`

### Bug 2 — Fanta Draft: search bar non passa `league`

**File:** `frontend/app/fanta-draft/page.tsx` + `backend/app/api/fanta_routes.py`

**Causa:** L'endpoint `/api/fanta/search` non riceve né usa `league_id` — restituisce risultati cross-league. Il frontend non passa il parametro `league`.

**Fix backend:** Già specificato in §1c — join a `matchcalendar` con `AND mc.league_id = :league_id`.

**Fix frontend:** Già specificato in §2d — la chiamata search include `&league=${encodeURIComponent(league)}`. L'`useEffect` di autocomplete aggiunge `league` alle dipendenze per rifetchare al cambio lega.

---

## Invarianti e vincoli

- **Isolamento totale**: nessun dato di una lega può comparire in un'altra. Ogni query porta `league_id` come parametro obbligatorio.
- **player_id come chiave**: mai usare la stringa `player` come chiave di join o `DISTINCT ON` — solo `player_id`.
- **team_type case-insensitive**: `ILIKE 'h%'` per coprire 'H', 'h', 'Home'.
- **Delta solo positivi**: `max(0.0, ...)` — il delta negativo (overperformer) non viene esposto come metrica di breakout.
