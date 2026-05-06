# BARSPORT SCOUT ENGINE — 4 Fix Urgenti — Piano di Implementazione

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correggere sicurezza secrets, porta del finder, engine DB duplicati e query scout su tabella inesistente.

**Architecture:** Fix applicati in ordine di dipendenza: prima .env (tutti i file lo usano), poi engine condiviso (scout_routes lo usa), poi riscrittura scout_routes, infine porta finder.html.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy async, PostgreSQL, python-dotenv, HTML/JS vanilla.

---

## File Map

| File | Operazione |
|------|-----------|
| `backend/.env` | CREA — secrets reali |
| `backend/.env.example` | CREA — placeholder |
| `.gitignore` | CREA — esclude .env e cache |
| `backend/main.py` | MODIFICA — load_dotenv, rimuovi local_engine, monta replacement router |
| `backend/app/db/database.py` | MODIFICA — aggiungi pool params |
| `backend/app/api/fanta_routes.py` | MODIFICA — usa engine condiviso |
| `backend/replacement_engine.py` | MODIFICA — converti da FastAPI app a APIRouter |
| `backend/app/api/scout_routes.py` | RISCRITTURA — da master_europe_players a rosters |
| `frontend/finder.html` | MODIFICA — porta 9000 → 8000 |

---

## Task 1: Creare `.env`, `.env.example`, `.gitignore`

**Files:**
- Create: `backend/.env`
- Create: `backend/.env.example`
- Create: `.gitignore` (root del progetto)

- [ ] **Step 1: Creare `.gitignore` nella root**

```
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
venv312/
*.egg-info/
dist/
build/

# Environment
.env
.env.local
.env.*.local

# Database
*.db
*.sqlite3

# Logs
*.log

# IDE
.vscode/
.idea/

# Node
node_modules/
```

Percorso: `C:\Users\euron\Desktop\claude of control\.gitignore`

- [ ] **Step 2: Creare `backend/.env` con i valori reali**

```
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat
DEEPSEEK_API_KEY=sk-36e8f7ea9d414acfaaeff3683d9fe8e8
ODDS_API_KEY=65a8b59488d965e7c7a87194ad275202
```

Percorso: `C:\Users\euron\Desktop\claude of control\backend\.env`

- [ ] **Step 3: Creare `backend/.env.example` con placeholder**

```
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/xpalermostat
DEEPSEEK_API_KEY=your_deepseek_api_key_here
ODDS_API_KEY=your_odds_api_key_here
```

Percorso: `C:\Users\euron\Desktop\claude of control\backend\.env.example`

---

## Task 2: Aggiornare `app/db/database.py` — engine condiviso con pool corretto

**Files:**
- Modify: `backend/app/db/database.py`

Questo è il motore canonico che tutti gli altri moduli useranno dopo il fix.

- [ ] **Step 1: Sostituire l'intero contenuto di `app/db/database.py`**

```python
"""
Async database connection and session management for xPalermoStat.
Single shared engine — all modules import from here.
"""
import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat"
)

engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

---

## Task 3: Aggiornare `main.py` — rimuovere secrets e local_engine

**Files:**
- Modify: `backend/main.py` — righe 1-63 e riga 102

- [ ] **Step 1: Sostituire le righe 1-63 di `main.py`**

Sostituire il blocco dall'inizio del file fino alla riga 63 (inclusa) con:

```python
print(print("-> TEST IDENTITA: SONO IL FILE GIUSTO"))

import logging
import traceback
import json
import httpx
import math
import random
import asyncio
import statistics
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any, Union, Tuple

from dotenv import load_dotenv
import os
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, Query, Request, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, text, func, and_, or_, update, delete
from sqlalchemy.orm import selectinload, sessionmaker

from openai import AsyncOpenAI
from scipy.stats import poisson

# Importazione Modelli e Database
from app.db.database import get_db, engine as local_engine
from app.db.models import Match, Shot, PlayerStat, Team, League

# ─── 1. CONFIGURAZIONE LOGGING PROFESSIONALE ────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("BarsportCore")

# ─── 2. CONFIGURAZIONE API E MOTORI ESTERNI ──────────────────────────
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
ODDS_API_KEY     = os.getenv("ODDS_API_KEY")

ai_client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)
```

- [ ] **Step 2: Aggiornare il lifespan per usare il nuovo engine**

Trovare (riga ~102):
```python
    await local_engine.dispose()
```
Rimane invariato — `local_engine` ora è un alias per `app.db.database.engine`, quindi funziona correttamente.

- [ ] **Step 3: Montare il replacement router in main.py**

Trovare il blocco di import router (righe ~84-93):
```python
# Altri Router
try:
    from app.api.scout_routes import router as scout_router
    from app.api.fanta_routes import router as fanta_router
    from app.api.v1.endpoints.team_metrics import router as team_metrics_router
    from app.api.v1.endpoints.team_performance import router as team_performance_router
    logger.info("✅ Altri router caricati.")
except ImportError as e:
    logger.error(f"⚠️ Errore caricamento moduli secondari: {e}")
    scout_router = fanta_router = team_metrics_router = team_performance_router = APIRouter()
```

Sostituire con:
```python
# Altri Router
try:
    from app.api.scout_routes import router as scout_router
    from app.api.fanta_routes import router as fanta_router
    from app.api.v1.endpoints.team_metrics import router as team_metrics_router
    from app.api.v1.endpoints.team_performance import router as team_performance_router
    from replacement_engine import router as replacement_router
    logger.info("✅ Altri router caricati.")
except ImportError as e:
    logger.error(f"⚠️ Errore caricamento moduli secondari: {e}")
    scout_router = fanta_router = team_metrics_router = team_performance_router = APIRouter()
    replacement_router = APIRouter()
```

- [ ] **Step 4: Registrare replacement_router nell'app**

Trovare dove vengono inclusi i router nell'app. Cercare `include_router` in main.py e aggiungere:
```python
app.include_router(replacement_router)
```
subito dopo gli altri `include_router`.

---

## Task 4: Convertire `replacement_engine.py` da app standalone a APIRouter

**Files:**
- Modify: `backend/replacement_engine.py`

- [ ] **Step 1: Sostituire l'intero contenuto di `replacement_engine.py`**

```python
import os
import pandas as pd
from fastapi import APIRouter
from dotenv import load_dotenv
from sqlalchemy import text

from app.db.database import engine

load_dotenv()

router = APIRouter()


@router.get("/replacement/{player_name}")
async def get_clones(player_name: str):
    try:
        async with engine.connect() as conn:
            query = text("""
                SELECT
                    player,
                    MAX(position) as position,
                    SUM("xG") as xg,
                    SUM("xA") as xa,
                    SUM("xGChain") as xgchain,
                    SUM("xGBuildup") as xgbuildup
                FROM rosters
                GROUP BY player
            """)
            res = await conn.execute(query)
            rows = res.mappings().all()

            if not rows:
                return {"error": "Tabella rosters vuota."}

        df = pd.DataFrame(rows)
        features = ['xg', 'xa', 'xgchain', 'xgbuildup']
        df[features] = df[features].apply(pd.to_numeric).fillna(0)
        df['player'] = df['player'].astype(str).str.strip()

        for f in features:
            df[f'p_{f}'] = df[f].rank(pct=True) * 100

        target = df[df['player'].str.lower().str.contains(player_name.lower(), na=False)]

        if target.empty:
            return {"error": f"Giocatore '{player_name}' non trovato."}

        p_cols = [f'p_{f}' for f in features]
        target_vec = target[p_cols].iloc[0]
        sim = df[p_cols].corrwith(target_vec, axis=1)
        df['similarity_score'] = ((sim + 1) / 2) * 100

        target_name = target['player'].iloc[0]
        clones = (df[df['player'] != target_name]
                  .sort_values(by='similarity_score', ascending=False)
                  .head(5))

        return clones.to_dict(orient='records')

    except Exception as e:
        return {"error": str(e)}
```

---

## Task 5: Aggiornare `fanta_routes.py` — usa engine condiviso

**Files:**
- Modify: `backend/app/api/fanta_routes.py` — righe 17-24

- [ ] **Step 1: Sostituire le righe di import DB in fanta_routes.py**

Trovare:
```python
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/fanta", tags=["Fanta Draft Engine"])

DB_URL = "postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat"
engine = create_async_engine(DB_URL, pool_pre_ping=True)
```

Sostituire con:
```python
from sqlalchemy import text

from app.db.database import engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/fanta", tags=["Fanta Draft Engine"])
```

---

## Task 6: Riscrivere `scout_routes.py` — da `master_europe_players` a `rosters`

**Files:**
- Modify: `backend/app/api/scout_routes.py` — righe 1-30 (header), poi ogni endpoint

Questa è la riscrittura più estesa. Il file viene modificato sezione per sezione.

- [ ] **Step 1: Sostituire le righe 1-30 (imports e costanti di normalizzazione)**

```python
"""
Scout Engine — insidecalcio
Implementa OIS, CII, AIR, BCS, FES, PIR, PPI, PSE, SRM
su tabella `rosters` (schema reale confermato).
"""

import math
import logging
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.db.database import engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scout", tags=["Scout Engine"])

# ─── Normalizzazione accenti per ricerca robusta ──────────────────────────────
_FROM = "'áàâäãåçéèêëíìîïñóòôöõúùûüýÿøšćž'"
_TO   = "'aaaaaaceeeeiiiinooooouuuuyyoscz'"
NAME_NORM  = f"translate(lower(r.player), {_FROM}, {_TO})"
PARAM_NORM = f"translate(lower(:p),       {_FROM}, {_TO})"
QUERY_NORM = f"translate(lower(:q),       {_FROM}, {_TO})"
```

- [ ] **Step 2: Sostituire la costante AGG (subito dopo NAME_NORM/PARAM_NORM/QUERY_NORM)**

Trovare il blocco `AGG = """` e sostituire con:

```python
# ─── JOIN base usato da tutti gli endpoint ────────────────────────────────────
_FROM_JOIN = """
    FROM rosters r
    JOIN matchcalendar mc ON mc.id = r.match_id
    JOIN team t ON (CASE WHEN r.team_type = 'h'
                    THEN mc.home_team_id ELSE mc.away_team_id END) = t.id
"""

# ─── Colonne aggregate ────────────────────────────────────────────────────────
# Indici risultante: 0=player_name 1=team_name 2=position
#   3=goals 4=npg 5=shots 6=assists 7=key_passes
#   8=xg 9=npxg 10=xa 11=xgchain 12=xgbuildup
#   13=minutes 14=games
AGG = """
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
"""
```

- [ ] **Step 3: Riscrivere `/search`**

Trovare l'endpoint `/search` e sostituire il corpo della query:

```python
@router.get("/search")
async def search_player(q: str):
    try:
        async with engine.connect() as conn:
            res = await conn.execute(
                text(f"""
                    SELECT r.player,
                           MAX(t.name)       AS team,
                           SUM(r.time::float) AS total_min
                    {_FROM_JOIN}
                    WHERE {NAME_NORM} ILIKE {QUERY_NORM}
                    GROUP BY r.player
                    HAVING SUM(r.time::float) > 500
                    ORDER BY total_min DESC
                    LIMIT 12
                """),
                {"q": f"%{q.strip().replace(' ', '%')}%"},
            )
            return {"results": [{"name": r[0], "team": r[1]} for r in res.fetchall()]}
    except Exception as e:
        logger.error(f"search error: {e}")
        return {"results": []}
```

- [ ] **Step 4: Riscrivere `/dna`**

```python
@router.get("/dna")
async def player_dna(player_name: str):
    try:
        async with engine.connect() as conn:
            res = await conn.execute(
                text(f"""
                    SELECT {AGG}
                    {_FROM_JOIN}
                    WHERE {NAME_NORM} ILIKE {PARAM_NORM}
                    GROUP BY r.player
                    ORDER BY MAX(mc.match_datetime) DESC
                    LIMIT 1
                """),
                {"p": f"%{player_name}%"},
            )
            row = res.fetchone()
            if not row:
                return {"dna": None}
            return {"dna": _build_player(row)}
    except Exception as e:
        logger.error(f"dna error: {e}")
        return {"dna": None}
```

- [ ] **Step 5: Riscrivere `/replacement`**

```python
@router.get("/replacement")
async def find_replacement(player_name: str):
    try:
        async with engine.connect() as conn:
            meta = await conn.execute(
                text(f"""
                    SELECT MAX(r.position)
                    {_FROM_JOIN}
                    WHERE {NAME_NORM} ILIKE {PARAM_NORM}
                """),
                {"p": f"%{player_name}%"},
            )
            meta_row = meta.fetchone()
            if not meta_row or not meta_row[0]:
                raise HTTPException(status_code=404, detail="Giocatore non trovato")
            position = meta_row[0] or ""

            tgt_res = await conn.execute(
                text(f"""
                    SELECT {AGG}
                    {_FROM_JOIN}
                    WHERE {NAME_NORM} ILIKE {PARAM_NORM}
                    GROUP BY r.player
                    ORDER BY MAX(mc.match_datetime) DESC
                    LIMIT 1
                """),
                {"p": f"%{player_name}%"},
            )
            tgt_row = tgt_res.fetchone()
            if not tgt_row:
                raise HTTPException(status_code=404, detail="Giocatore non trovato")
            target = _build_player(tgt_row)

            position_groups = {
                'GK': 'GK',
                'DC': 'DF', 'DL': 'DF', 'DR': 'DF', 'DMC': 'DF', 'DML': 'DF', 'DMR': 'DF',
                'MC': 'MF', 'ML': 'MF', 'MR': 'MF', 'AMC': 'MF', 'AML': 'MF', 'AMR': 'MF',
                'FW': 'FW', 'FWL': 'FW', 'FWR': 'FW',
                'Sub': 'FW'
            }
            group = position_groups.get(position, position)
            allowed_positions = tuple(p for p, g in position_groups.items() if g == group)

            pool_res = await conn.execute(
                text(f"""
                    SELECT {AGG}
                    {_FROM_JOIN}
                    WHERE r.position = ANY(:allowed_positions)
                    GROUP BY r.player
                    HAVING SUM(r.time::float) >= 600
                """),
                {"allowed_positions": list(allowed_positions)},
            )
            pool_rows = pool_res.fetchall()

        target_vec = target["_pse_vector"]
        results = []
        for row in pool_rows:
            p = _build_player(row)
            if p["name"].lower() == target["name"].lower():
                continue
            dist = euclidean_distance(target_vec, p["_pse_vector"])
            sim  = similarity_score(dist)
            p["similarity"] = round(sim, 4)
            p["similarity_pct"] = round(sim * 100, 1)
            results.append(p)

        results.sort(key=lambda x: x["similarity"], reverse=True)
        substitutes = results[:5]

        target.pop("_pse_vector", None)
        for s in substitutes:
            s.pop("_pse_vector", None)

        return {"target": target, "substitutes": substitutes}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"replacement error: {e}")
        return {"target": None, "substitutes": []}
```

- [ ] **Step 6: Riscrivere `/compare`**

```python
@router.get("/compare")
async def compare_players(p1: str, p2: str):
    try:
        async with engine.connect() as conn:
            q = text(f"""
                SELECT {AGG}
                {_FROM_JOIN}
                WHERE {NAME_NORM} ILIKE {PARAM_NORM}
                GROUP BY r.player
                ORDER BY MAX(mc.match_datetime) DESC
                LIMIT 1
            """)
            r1 = (await conn.execute(q, {"p": f"%{p1}%"})).fetchone()
            r2 = (await conn.execute(q, {"p": f"%{p2}%"})).fetchone()

        data = []
        for row in [r1, r2]:
            if row:
                p = _build_player(row)
                p.pop("_pse_vector", None)
                data.append(p)
        return {"data": data}
    except Exception as e:
        logger.error(f"compare error: {e}")
        return {"data": []}
```

- [ ] **Step 7: Riscrivere `/radar`**

```python
@router.get("/radar")
async def scouting_radar(player_name: str):
    try:
        async with engine.connect() as conn:
            tgt_res = await conn.execute(
                text(f"""
                    SELECT {AGG}
                    {_FROM_JOIN}
                    WHERE {NAME_NORM} ILIKE {PARAM_NORM}
                    GROUP BY r.player
                    ORDER BY MAX(mc.match_datetime) DESC
                    LIMIT 1
                """),
                {"p": f"%{player_name}%"},
            )
            tgt_row = tgt_res.fetchone()
            if not tgt_row:
                return {"radar": None}
            target = _build_player(tgt_row)
            position = target["position"]

            position_groups = {
                'GK': 'GK',
                'DC': 'DF', 'DL': 'DF', 'DR': 'DF', 'DMC': 'DF', 'DML': 'DF', 'DMR': 'DF',
                'MC': 'MF', 'ML': 'MF', 'MR': 'MF', 'AMC': 'MF', 'AML': 'MF', 'AMR': 'MF',
                'FW': 'FW', 'FWL': 'FW', 'FWR': 'FW',
                'Sub': 'FW'
            }
            group = position_groups.get(position, position)
            allowed_positions = tuple(p for p, g in position_groups.items() if g == group)

            dist_res = await conn.execute(
                text(f"""
                    SELECT {AGG}
                    {_FROM_JOIN}
                    WHERE r.position = ANY(:allowed_positions)
                    GROUP BY r.player
                    HAVING SUM(r.time::float) >= 600
                """),
                {"allowed_positions": list(allowed_positions)},
            )
            pool = [_build_player(r) for r in dist_res.fetchall()]

        metrics = ["xg", "goals", "xa", "xgchain", "shots"]
        distributions = {m: [p["p90"][m] for p in pool] for m in metrics}
        percentiles = {
            m: percentile_rank(target["p90"][m], distributions[m])
            for m in metrics
        }

        target.pop("_pse_vector", None)
        return {
            "radar": {
                "player": target,
                "percentiles": percentiles,
                "axes": {
                    "xg":      {"label": "xG/90",     "value": target["p90"]["xg"],      "percentile": percentiles["xg"]},
                    "goals":   {"label": "Goals/90",   "value": target["p90"]["goals"],   "percentile": percentiles["goals"]},
                    "xa":      {"label": "xA/90",      "value": target["p90"]["xa"],      "percentile": percentiles["xa"]},
                    "xgchain": {"label": "xGChain/90", "value": target["p90"]["xgchain"], "percentile": percentiles["xgchain"]},
                    "shots":   {"label": "Shots/90",   "value": target["p90"]["shots"],   "percentile": percentiles["shots"]},
                },
                "pool_size": len(pool),
            }
        }
    except Exception as e:
        logger.error(f"radar error: {e}")
        return {"radar": None}
```

- [ ] **Step 8: Riscrivere `/discover`**

```python
@router.get("/discover")
async def discover_talent(pos: str = "ALL", limit: int = 20):
    try:
        async with engine.connect() as conn:
            season_res = await conn.execute(
                text("SELECT EXTRACT(YEAR FROM MAX(match_datetime)) FROM matchcalendar")
            )
            season = int(season_res.scalar() or 2024)

            pos_filter = ""
            params: dict = {"s": season}
            if pos.upper() != "ALL":
                pos_filter = "AND r.position ILIKE :pos_val"
                params["pos_val"] = f"%{pos.upper()}%"

            res = await conn.execute(
                text(f"""
                    SELECT {AGG}
                    {_FROM_JOIN}
                    WHERE EXTRACT(YEAR FROM mc.match_datetime) = :s {pos_filter}
                    GROUP BY r.player
                    HAVING SUM(r.time::float) >= 700
                """),
                params,
            )
            rows = res.fetchall()

        players = []
        for row in rows:
            p = _build_player(row)
            p.pop("_pse_vector", None)
            players.append(p)

        players.sort(key=lambda x: x["scores"]["PPI"], reverse=True)
        return {"talents": players[:limit], "season": season}

    except Exception as e:
        logger.error(f"discover error: {e}")
        return {"talents": [], "season": 0}
```

- [ ] **Step 9: Riscrivere `/report`**

```python
@router.get("/report")
async def scout_report(player_name: str):
    try:
        async with engine.connect() as conn:
            res = await conn.execute(
                text(f"""
                    SELECT {AGG}
                    {_FROM_JOIN}
                    WHERE {NAME_NORM} ILIKE {PARAM_NORM}
                    GROUP BY r.player
                    ORDER BY MAX(mc.match_datetime) DESC
                    LIMIT 1
                """),
                {"p": f"%{player_name}%"},
            )
            row = res.fetchone()
            if not row:
                return {"report": None}

        data = _build_player(row)
        data.pop("_pse_vector", None)

        position = data["position"]
        position_groups = {
            'GK': 'GK',
            'DC': 'DF', 'DL': 'DF', 'DR': 'DF', 'DMC': 'DF', 'DML': 'DF', 'DMR': 'DF',
            'MC': 'MF', 'ML': 'MF', 'MR': 'MF', 'AMC': 'MF', 'AML': 'MF', 'AMR': 'MF',
            'FW': 'FW', 'FWL': 'FW', 'FWR': 'FW',
            'Sub': 'FW'
        }
        group = position_groups.get(position, position)
        allowed_positions = tuple(p for p, g in position_groups.items() if g == group)

        async with engine.connect() as conn2:
            dist_res = await conn2.execute(
                text(f"""
                    SELECT {AGG}
                    {_FROM_JOIN}
                    WHERE r.position = ANY(:allowed_positions)
                    GROUP BY r.player
                    HAVING SUM(r.time::float) >= 600
                """),
                {"allowed_positions": list(allowed_positions)},
            )
            pool = [_build_player(r) for r in dist_res.fetchall()]

        metrics = ["xg", "goals", "xa", "xgchain", "shots"]
        distributions = {m: [p["p90"][m] for p in pool] for m in metrics}
        percentiles = {m: percentile_rank(data["p90"][m], distributions[m]) for m in metrics}

        data["radar"] = {
            "percentiles": percentiles,
            "axes": {
                "xg":      {"label": "xG/90",     "value": data["p90"]["xg"],      "percentile": percentiles["xg"]},
                "goals":   {"label": "Goals/90",   "value": data["p90"]["goals"],   "percentile": percentiles["goals"]},
                "xa":      {"label": "xA/90",      "value": data["p90"]["xa"],      "percentile": percentiles["xa"]},
                "xgchain": {"label": "xGChain/90", "value": data["p90"]["xgchain"], "percentile": percentiles["xgchain"]},
                "shots":   {"label": "Shots/90",   "value": data["p90"]["shots"],   "percentile": percentiles["shots"]},
            },
            "pool_size": len(pool),
        }

        sc  = data["scores"]
        p90 = data["p90"]

        def _profile_text() -> str:
            lines = [f"{data['name']} ({data['team']}, {data['position']}) — {data['games']} presenze, {data['minutes']} minuti."]
            lines.append(f"PIR: {sc['PIR']:.4f} | OIS: {sc['OIS']:.4f} | CII: {sc['CII']:.4f} | FES: {sc['FES']:.3f}")
            lines.append(f"npxG/90: {p90['npxg']} — xA/90: {p90['xa']} — xGChain/90: {p90['xgchain']}")
            return " | ".join(lines)

        def _strength() -> str:
            if sc["OIS"] > 0.4 and sc["FES"] > 1.0:
                return "Finalizzatore efficiente con alto impatto offensivo."
            if sc["CII"] > sc["OIS"]:
                return "Creatore di gioco superiore alla media. Alto CII indica un contributo associativo eccezionale."
            if sc["AIR"] > 0.01:
                return "Partecipazione offensiva costante."
            return "Profilo bilanciato."

        def _weakness() -> str:
            if p90["xg"] < 0.10:
                return "Basso npxG/90. Produzione di tiri nell'area limitata."
            if p90["xa"] < 0.06:
                return "Scarsa produzione di xA/90."
            if sc["FES"] < 0.80:
                return "FES < 0.80: segna meno di quanto suggeriscano gli xG."
            return "Contributo difensivo fuori dalla zona offensiva da valutare."

        data["report_text"] = {
            "profilo": _profile_text(),
            "forza":   _strength(),
            "limiti":  _weakness(),
        }
        return {"report": data}

    except Exception as e:
        logger.error(f"report error: {e}")
        return {"report": None}
```

---

## Task 7: Fix `finder.html` — porta 9000 → 8000

**Files:**
- Modify: `frontend/finder.html:743`

- [ ] **Step 1: Cambiare la riga 743 di finder.html**

Trovare:
```javascript
const API = "http://127.0.0.1:9000";
```

Sostituire con:
```javascript
const API = "http://127.0.0.1:8000";
```

---

## Verifica Finale

- [ ] **Avviare il backend** e verificare assenza errori di import:
  ```bash
  cd backend
  uvicorn main:app --host 0.0.0.0 --port 8000 --reload
  ```
  Atteso: nessun `ImportError`, log `✅ Altri router caricati.`

- [ ] **Testare endpoint leaders** (già funzionante su rosters):
  ```
  GET http://127.0.0.1:8000/api/scout/leaders
  ```
  Atteso: JSON con `scorers` e `architects`

- [ ] **Testare scout search** (ora su rosters):
  ```
  GET http://127.0.0.1:8000/api/scout/search?q=dybala
  ```
  Atteso: `{"results": [...]}`

- [ ] **Testare replacement**:
  ```
  GET http://127.0.0.1:8000/replacement/dybala
  ```
  Atteso: lista di giocatori simili (non `{"error": ...}`)

- [ ] **Aprire `frontend/finder.html`** nel browser e verificare che la pagina carichi dati senza errori di rete nella console.
