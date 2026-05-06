# BARSPORT SCOUT ENGINE — 4 Fix Urgenti
**Data:** 2026-04-20  
**Scope:** Sicurezza, funzionamento finder, endpoint scout, performance DB

---

## Fix 1 — Secrets in `.env` (priorità: CRITICA)

**Problema:** API keys DeepSeek/Odds e password DB hardcoded in 4 file Python.

**Soluzione:**
- Creare `backend/.env` con le variabili: `DATABASE_URL`, `DEEPSEEK_API_KEY`, `ODDS_API_KEY`
- Creare `backend/.env.example` con placeholder sicuri
- Creare `.gitignore` nella root del progetto
- `python-dotenv` già presente in requirements.txt
- `app/db/database.py` già usa `os.getenv` — non toccare
- File da aggiornare: `main.py` (righe 44-45, 50-62), `fanta_routes.py` (riga 24), `replacement_engine.py`
- `scout_routes.py` gestito interamente dal Fix 3

**Variabili .env:**
```
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat
DEEPSEEK_API_KEY=<la_tua_chiave>
ODDS_API_KEY=<la_tua_chiave>
```

**Caricamento in main.py:**
```python
from dotenv import load_dotenv
import os
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
```

---

## Fix 2 — Porta 9000→8000 in finder.html (priorità: ALTA)

**Problema:** `finder.html:743` punta a porta 9000 inesistente; l'intera UI è morta.

**Soluzione:** Una riga: `const API = "http://127.0.0.1:8000"`

**Stato endpoint su porta 8000:**
- `/api/scout/leaders` ✓ (scout_routes.py)
- `/api/scout/search` ✓
- `/api/scout/player/{name}` ✓
- `/api/shots/{name}` ✓ (main.py:1031)
- `/api/undervalued` ✓ (main.py:1060)
- `/api/h2h` ✓ (main.py:1178)
- `/replacement/{name}` ✗ — `replacement_engine.py` è un'app FastAPI standalone **non montata** in main.py → montarla come router nel Fix 2

---

## Fix 3 — scout_routes.py: da `master_europe_players` a `rosters` (priorità: ALTA)

**Problema:** Tutti gli endpoint scout usano `master_europe_players` (materialized view inesistente).

**Soluzione:** Riscrivere le query per usare `rosters` (tabella reale, schema confermato).

**Schema rosters:**
`id, match_id, player_id, player, position, time, goals, assists, shots, key_passes, xG, xA, xGChain, xGBuildup, yellow_card, red_card, team_type`

**JOIN pattern** (già validato in meritometro.py:605):
```sql
FROM rosters r
JOIN matchcalendar mc ON mc.id = r.match_id
JOIN team t ON (CASE WHEN r.team_type = 'h' 
                THEN mc.home_team_id ELSE mc.away_team_id END) = t.id
```

**Nuova AGG constant:**
```sql
r.player                                AS player_name,
MAX(t.name)                             AS team_name,
MAX(r.position)                         AS position,
COALESCE(SUM(r.goals::float),       0)  AS goals,
0                                       AS npg,
COALESCE(SUM(r.shots::float),       0)  AS shots,
COALESCE(SUM(r.assists::float),     0)  AS assists,
COALESCE(SUM(r.key_passes::float),  0)  AS key_passes,
COALESCE(SUM(r."xG"::float),        0)  AS xg,
0                                       AS npxg,
COALESCE(SUM(r."xA"::float),        0)  AS xa,
COALESCE(SUM(r."xGChain"::float),   0)  AS xgchain,
COALESCE(SUM(r."xGBuildup"::float), 0)  AS xgbuildup,
COALESCE(SUM(r.time::float),        1)  AS minutes,
COUNT(DISTINCT r.match_id)              AS games
```

**`season` → sostituito con:**
- `ORDER BY MAX(season::int) DESC` → `ORDER BY MAX(mc.match_datetime) DESC`
- `WHERE season::int = :s` → rimosso (non necessario per il funzionamento dello scout)
- `SELECT MAX(season::int)` in `/leaders` → `EXTRACT(YEAR FROM MAX(mc.match_datetime))`

**GROUP BY:** `r.player` (non più `player_name`)

**Normalizzazione accenti:** adattare `NAME_NORM` da `player_name` a `r.player`

---

## Fix 4 — Un solo DB engine condiviso (priorità: MEDIA — performance)

**Problema:** 4 engine indipendenti → spreco connessioni PostgreSQL, alto consumo RAM.

**Motore canonico:** `app/db/database.py` — già legge `DATABASE_URL` da env, usato da `get_db()`.

**Pool consigliato** (da configurare solo nell'engine canonico):
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

**File da aggiornare:**
- `scout_routes.py`: rimuovere `DB_URL` e `engine` locali, aggiungere `from app.db.database import engine`
- `fanta_routes.py`: stesso
- `replacement_engine.py`: stesso  
- `main.py`: rimuovere `local_engine` (pool_size=30/max_overflow=20), importare engine da `app.db.database`
- Verificare `app/db/session.py`: se ridondante rispetto a `database.py`, unificare

**Nota:** `app/db/database.py` va aggiornato per aggiungere i parametri pool_size/max_overflow/pool_recycle (ora ha solo `echo=False, future=True`).

---

## Ordine di esecuzione

1. Fix 1 — `.env` + `.gitignore`
2. Fix 2 — porta finder.html
3. Fix 4 — engine condiviso in `app/db/database.py` (deve essere pronto prima di Fix 3)
4. Fix 3 — riscrittura scout_routes.py con nuovo engine e nuove query

---

## File toccati

| File | Operazione |
|------|-----------|
| `backend/.env` | CREA |
| `backend/.env.example` | CREA |
| `.gitignore` | CREA |
| `backend/main.py` | MODIFICA (load_dotenv, rimuovi local_engine) |
| `backend/app/api/fanta_routes.py` | MODIFICA (env var, import engine) |
| `backend/replacement_engine.py` | MODIFICA (env var, import engine) |
| `backend/app/db/database.py` | MODIFICA (pool params) |
| `backend/app/api/scout_routes.py` | RISCRITTURA COMPLETA query |
| `frontend/finder.html` | MODIFICA (1 riga, porta) |
