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
    api_key=DEEPSEEK_API_KEY or "placeholder-key-not-configured",
    base_url="https://api.deepseek.com"
)

# ─── 3. IMPORTAZIONE ROUTER MODULARE (ISOLAMENTO ERRORI) ───────────
from fastapi import APIRouter

# Tentativo Scraper (Sappiamo che fallirà per understat)
try:
    from app.api.scraper_routes import router as scraper_router
    logger.info("✅ Scraper Router caricato correttamente.")
except ImportError as e:
    logger.error(f"⚠️ Scraper non caricato (errore modulo): {e}")
    scraper_router = APIRouter()

# Tentativo Meritometro (Indipendente dallo scraper)
try:
    from app.api.meritometro import router as meritometro_router
    logger.info("✅ Meritometro Router caricato correttamente dal file esterno.")
except ImportError as e:
    logger.error(f"❌ Errore critico nel caricamento del Meritometro: {e}")
    meritometro_router = APIRouter()

# Tentativo NerdZone
try:
    from app.api.nerdzone_routes import router as nerdzone_router
    logger.info("✅ NerdZone Router caricato.")
except ImportError as e:
    logger.error(f"⚠️ NerdZone non caricato: {e}")
    nerdzone_router = APIRouter()

# Altri Router
try:
    from app.api.scout_routes import router as scout_router
    from app.api.fanta_routes import router as fanta_router
    from app.api.v1.endpoints.team_metrics import router as team_metrics_router
    from app.api.v1.endpoints.team_performance import router as team_performance_router
    from app.api.preview_routes import router as matches_preview_router
    from app.api.betting_routes import router as betting_router
    from replacement_engine import router as replacement_router
    logger.info("✅ Altri router caricati.")
except ImportError as e:
    logger.error(f"⚠️ Errore caricamento moduli secondari: {e}")
    scout_router = fanta_router = team_metrics_router = team_performance_router = APIRouter()
    matches_preview_router = APIRouter()
    betting_router = APIRouter()
    replacement_router = APIRouter()
# ─── 4. DEFINIZIONE LIFESPAN E INIZIALIZZAZIONE APP ─────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Logica di avvio: connessione database, warmup cache AI, scheduler
    logger.info("🚀 BARSPORT CLUB STATS CORE: Motore in fase di accensione...")

    # ── Avvio Scheduler Automatico (Phase 9) ─────────────────────────
    try:
        from app.core.scheduler import start_scheduler
        start_scheduler()
        logger.info("✅ Scheduler automatico avviato con successo.")
    except Exception as e:
        logger.error(f"⚠️ Impossibile avviare lo scheduler: {e}")

    yield

    # Logica di spegnimento: scheduler, chiusura pool
    logger.info("🛑 BARSPORT CLUB STATS CORE: Spegnimento in corso...")

    # ── Arresto Scheduler ────────────────────────────────────────────
    try:
        from app.core.scheduler import stop_scheduler
        stop_scheduler()
        logger.info("✅ Scheduler arrestato correttamente.")
    except Exception as e:
        logger.warning(f"⚠️ Errore nello spegnimento dello scheduler: {e}")

    await local_engine.dispose()

app = FastAPI(
    title="Barsport Club - Professional Analytics Engine",
    description="Backend ad alte prestazioni per Scout, Meritometro e Betting AI",
    version="35.5.12",
    lifespan=lifespan
)

# Configurazione CORS per permettere al frontend di comunicare
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── 5. COSTANTI DI SISTEMA E MAPPATURE ──────────────────────────────
AFFILIATE_LINKS = {
    "Betfair": "https://www.betfair.it/affiliate_link_esempio",
    "Snai": "https://www.snai.it/affiliate_link_esempio",
    "1xBet": "https://1xbet.com/affiliate",
    "default": "https://www.insidecalcio.it/registrazione"
}

ODDS_LEAGUE_MAP = {
    "Serie A": "soccer_italy_serie_a",
    "Premier League": "soccer_epl",
    "La Liga": "soccer_spain_la_liga",
    "Bundesliga": "soccer_germany_bundesliga",
    "Ligue 1": "soccer_france_ligue_one"
}

# ─── 6. MOTORE MATEMATICO CORE (SANITIZZAZIONE E POISSON) ───────────
def sanitize_metric(value: Any) -> float:
    """Trasforma qualsiasi input in un float sicuro per i calcoli."""
    if value is None:
        return 0.0
    try:
        f_val = float(value)
        if math.isnan(f_val) or math.isinf(f_val):
            return 0.0
        return f_val
    except (ValueError, TypeError):
        return 0.0

def normalize_team(val: Any) -> str:
    """Normalizza i tag 'home'/'away' provenienti dallo scraper."""
    if not val:
        return 'a'
    s = str(val).lower().replace('"', '').replace("'", "").strip()
    if s in ['h', 'home', 'casa', '1']:
        return 'h'
    return 'a'

def calculate_true_expectancy(h_xg_f, h_xg_a, a_xg_f, a_xg_a, league_avg_xg=1.35):
    """
    Motore Poisson Avanzato.
    Calcola probabilità di vittoria, pareggio e scontro basandosi sulla forza 
    relativa di attacco e difesa rispetto alla media della lega.
    """
    # 1. Forza Attacco e Difesa
    home_attack_strength = h_xg_f / league_avg_xg
    home_defense_strength = h_xg_a / league_avg_xg
    away_attack_strength = a_xg_f / league_avg_xg
    away_defense_strength = a_xg_a / league_avg_xg
    
    # 2. Calcolo Lambda (Casa) e Mu (Trasferta)
    # Applichiamo il fattore 'Home Advantage' del 10%
    HOME_ADVANTAGE = 1.10
    lmbda = float(home_attack_strength * away_defense_strength * league_avg_xg * HOME_ADVANTAGE)
    mu = float(away_attack_strength * home_defense_strength * league_avg_xg)
    
    # 3. Iterazione Matrix Poisson (fino a 12 gol per sicurezza statistica)
    prob_1 = prob_x = prob_2 = prob_o25 = prob_u25 = prob_btts_y = prob_btts_n = max_p = 0.0
    score_str = "1-1"
    
    for h in range(13):
        for a in range(13):
            # Calcolo probabilità singola combinazione
            p = poisson.pmf(h, lmbda) * poisson.pmf(a, mu)
            
            # Esito Finale
            if h > a: prob_1 += p
            elif h == a: prob_x += p
            else: prob_2 += p
                
            # Over/Under 2.5
            if (h + a) > 2.5: prob_o25 += p
            else: prob_u25 += p
                
            # Goal / No Goal
            if h > 0 and a > 0: prob_btts_y += p
            else: prob_btts_n += p
                
            # Risultato Esatto più probabile
            if p > max_p:
                max_p = p
                score_str = f"{h}-{a}"
                
    return {
        "dc_score": score_str,
        "total_goals_expected": round(lmbda + mu, 2),
        "supremacy_index": round(lmbda - mu, 2),
        "probabilities": {
            "1": round(prob_1 * 100, 2),
            "X": round(prob_x * 100, 2),
            "2": round(prob_2 * 100, 2),
            "1X": round((prob_1 + prob_x) * 100, 2),
            "X2": round((prob_2 + prob_x) * 100, 2),
            "12": round((prob_1 + prob_2) * 100, 2),
            "over25": round(prob_o25 * 100, 2),
            "under25": round(prob_u25 * 100, 2),
            "btts_yes": round(prob_btts_y * 100, 2),
            "btts_no": round(prob_btts_n * 100, 2)
        }
    }

@app.get("/api/scout/leaders")
async def get_scout_leaders():
    print("\n--- INIZIO CALCOLO LEADERS SCOUT ENGINE (STAGIONE 25/26) ---")
    try:
        async with local_engine.connect() as conn:
            
            # FILTRO DATA: Aggiornato all'inizio della stagione 25/26
            start_date = '2025-08-01'

            print("1. Eseguo query Top Scorers con filtro stagionale...")
            query_scorers = text(f"""
                SELECT 
                    r.player as name, 
                    SUM(r.goals) as goals_total, 
                    (SUM(r."xG") / NULLIF(SUM(r.time), 0)) * 90 as xg_90 
                FROM rosters r
                JOIN matchcalendar m ON r.match_id = m.id
                WHERE m.match_datetime >= '{start_date}'
                GROUP BY r.player
                HAVING SUM(r.time) > 200
                ORDER BY goals_total DESC 
                LIMIT 5;
            """)
            res_scorers = await conn.execute(query_scorers)
            scorers_raw = res_scorers.mappings().all()
            
            print("2. Eseguo query Top Architects con filtro stagionale...")
            query_architects = text(f"""
                SELECT 
                    r.player as name, 
                    SUM(r.assists) as assists_total, 
                    (SUM(r."xA") / NULLIF(SUM(r.time), 0)) * 90 as xa_90 
                FROM rosters r
                JOIN matchcalendar m ON r.match_id = m.id
                WHERE m.match_datetime >= '{start_date}'
                GROUP BY r.player
                HAVING SUM(r.time) > 200
                ORDER BY assists_total DESC 
                LIMIT 5;
            """)
            res_architects = await conn.execute(query_architects)
            architects_raw = res_architects.mappings().all()

        # Formattiamo i dati puliti per il frontend
        scorers = []
        for s in scorers_raw:
            scorers.append({
                "name": s["name"],
                "team": "Stagione 25/26", # Etichetta aggiornata
                "value": f"{s['goals_total']} Goal",
                "stat": f"{round(float(s['xg_90']), 2) if s['xg_90'] is not None else 0.00} xG/90"
            })

        architects = []
        for a in architects_raw:
            architects.append({
                "name": a["name"],
                "team": "Stagione 25/26", # Etichetta aggiornata
                "value": f"{a['assists_total']} Assist",
                "stat": f"{round(float(a['xa_90']), 2) if a['xa_90'] is not None else 0.00} xA/90"
            })

        print("--- FINE: Ritorno i dati stagionali al frontend ---")
        return {"scorers": scorers, "architects": architects}

    except Exception as e:
        print(f"!!! ERRORE CRITICO in get_scout_leaders: {e} !!!")
        return {"error": str(e), "scorers": [], "architects": []}
@app.get("/api/scout/search")
async def search_players(q: str):
    if len(q) < 2:
        return {"results": []}
    try:
        async with local_engine.connect() as conn:
            res = await conn.execute(text("""
                SELECT DISTINCT player
                FROM rosters
                WHERE player ILIKE :search_term
                ORDER BY player
                LIMIT 10
            """), {"search_term": f"%{q}%"})
            rows = res.mappings().all()
            return {"results": [{"name": r["player"], "team": ""} for r in rows]}
    except Exception as e:
        print(f"!!! ERRORE in search_players: {e} !!!")
        return {"results": []}
@app.get("/api/scout/player/{player_name}")
async def get_player_profile(player_name: str):
    print(f"\n--- CARICAMENTO PROFILO PRO: {player_name} ---")
    try:
        async with local_engine.connect() as conn:
            # 1. STATISTICHE TOTALI
            query_stats = text("""
                SELECT 
                    player as name,
                    MAX(team_type) as team, 
                    MAX(position) as pos,
                    SUM(time) as min,
                    SUM(goals) as g,
                    SUM(assists) as a,
                    SUM(shots) as shots,
                    SUM(key_passes) as key_passes,
                    SUM("xG") as xg,
                    SUM("xA") as xa,
                    SUM(yellow_card) as yellow_cards,
                    SUM(red_card) as red_cards,
                    SUM("xGBuildup") as xg_buildup,
                    SUM("xGChain") as xg_chain
                FROM rosters
                WHERE player ILIKE :name
                GROUP BY player
            """)
            res_stats = await conn.execute(query_stats, {"name": player_name})
            player_data = res_stats.mappings().fetchone()

            if not player_data:
                return {"error": "Giocatore non trovato nel database"}

            # 2. ESTRAZIONE DI TUTTI I TIRI (Per la Mappa Tattica Personale)
            query_shots = text("""
                SELECT minute, "xG", result, "X", "Y", situation, "shotType"
                FROM shots
                WHERE player ILIKE :name
            """)
            res_shots = await conn.execute(query_shots, {"name": player_name})
            shots_raw = res_shots.mappings().all()

            # Formattiamo i tiri in una lista pulita
            shots_list = []
            for s in shots_raw:
                shots_list.append({
                    "minute": s["minute"],
                    "xG": float(s["xG"]) if s["xG"] else 0.0,
                    "result": s["result"],
                    "X": float(s["X"]) if s["X"] else 0.0,
                    "Y": float(s["Y"]) if s["Y"] else 0.0,
                    "situation": s["situation"],
                    "shotType": s["shotType"]
                })

            mins = player_data["min"] if player_data["min"] else 1
            
            return {
                "info": {
                    "name": player_data["name"],
                    "pos": player_data["pos"] or "N/D",
                    # FIX TEMP: Se il DB passa 'h' o 'a', non lo stampiamo per evitare brutture
                    "team": "Dato Storico" if player_data["team"] in ['h', 'a'] else player_data["team"]
                },
                "totals": {
                    "min": player_data["min"] or 0,
                    "g": player_data["g"] or 0,
                    "a": player_data["a"] or 0,
                    "xg": float(player_data["xg"] or 0),
                    "xa": float(player_data["xa"] or 0),
                    "shots": player_data["shots"] or 0,
                    "key_passes": player_data["key_passes"] or 0,
                    "yellow_cards": player_data["yellow_cards"] or 0,
                    "red_cards": player_data["red_cards"] or 0,
                    "xGBuildup": float(player_data["xg_buildup"] or 0),
                    "xGChain": float(player_data["xg_chain"] or 0)
                },
                "stats90": {
                    "xg90": (float(player_data["xg"] or 0) / mins) * 90,
                    "xa90": (float(player_data["xa"] or 0) / mins) * 90
                },
                "shots_map": shots_list # ECCO IL NOSTRO TESORO AGGIUNTO!
            }
    except Exception as e:
        print(f"!!! ERRORE PROFILO {player_name}: {e} !!!")
        return {"error": str(e)}

# ─── 8. ANALISI TEAM PERFORMANCE E MOMENTUM ──────────────────────────
async def get_detailed_team_form(team_name: str, league_id: int):
    """
    Funzione di supporto per calcolare lo slancio di una squadra 
    analizzando le discrepanze tra xG fatti e gol reali nelle ultime 5.
    """
    try:
        async with local_engine.connect() as conn:
            query = text("""
                SELECT m.home_goals, m.away_goals, m."home_xG", m."away_xG", 
                       th.name as h_name, m.match_datetime
                FROM matchcalendar m
                JOIN team th ON m.home_team_id = th.id
                JOIN team ta ON m.away_team_id = ta.id
                WHERE (th.name = :t OR ta.name = :t) 
                  AND m.is_completed = True 
                  AND m.league_id = :lid
                ORDER BY m.match_datetime DESC LIMIT 5
            """)
            
            rows = (await conn.execute(query, {"t": team_name, "lid": league_id})).fetchall()
            
            if not rows:
                return {"momentum": 1.0, "status": "N/A", "desc": "Nessun dato storico"}
                
            performance_ratio = []
            for r in rows:
                is_home = r[4] == team_name
                real_goals = r[0] if is_home else r[1]
                expected_goals = float(r[2] if is_home else r[3])
                
                # Calcolo efficienza (gol fatti rispetto a xG creato)
                if expected_goals > 0:
                    performance_ratio.append(real_goals / expected_goals)
                else:
                    performance_ratio.append(1.0)
            
            avg_momentum = statistics.mean(performance_ratio)
            trend = "Overperforming" if avg_momentum > 1.2 else "Underperforming" if avg_momentum < 0.8 else "In Media"
            
            return {
                "momentum": round(avg_momentum, 2),
                "trend": trend,
                "matches_analyzed": len(rows)
            }
    except Exception as e:
        logger.warning(f"⚠️ Errore calcolo Momentum per {team_name}: {e}")
        return {"momentum": 1.0, "status": "Error"}

@app.get("/api/v1/team-metrics/{team_name}")
async def get_team_metrics_complete(team_name: str, league: str = "Serie A"):
    """
    Ritorna un profilo completo della squadra: attacco, difesa, pressing e slancio.
    """
    try:
        async with local_engine.connect() as conn:
            l_row = (await conn.execute(text("SELECT id FROM league WHERE name ILIKE :n"), {"n": f"%{league}%"})).fetchone()
            if not l_row: raise HTTPException(status_code=404, detail="Lega non trovata")
            lid = l_row[0]
            
            stats_query = text("""
                SELECT 
                    AVG(CASE WHEN th.name = :t THEN m."home_xG" ELSE m."away_xG" END) as xG_for,
                    AVG(CASE WHEN th.name = :t THEN m."away_xG" ELSE m."home_xG" END) as xG_against,
                    AVG(CASE WHEN th.name = :t THEN m.home_ppda ELSE m.away_ppda END) as ppda,
                    AVG(CASE WHEN th.name = :t THEN m.home_deep ELSE m.away_deep END) as deep_entries,
                    AVG(CASE WHEN th.name = :t THEN m.home_xpts ELSE m.away_xpts END) as expected_points
                FROM matchcalendar m
                JOIN team th ON m.home_team_id = th.id
                JOIN team ta ON m.away_team_id = ta.id
                WHERE (th.name = :t OR ta.name = :t) AND m.is_completed = True AND m.league_id = :lid
            """)
            
            res = (await conn.execute(stats_query, {"t": team_name, "lid": lid})).fetchone()
            momentum_data = await get_detailed_team_form(team_name, lid)
            
            if not res or res[0] is None:
                return {"error": "Dati insufficienti per questa squadra"}
                
            return {
                "team": team_name,
                "league": league,
                "attack": {
                    "avg_xg": round(float(res[0]), 2),
                    "deep_entries": round(float(res[3]), 1)
                },
                "defense": {
                    "avg_xga": round(float(res[1]), 2),
                    "pressing_ppda": round(float(res[2]), 2)
                },
                "merit": {
                    "avg_xpts": round(float(res[4]), 2),
                    "momentum_score": momentum_data["momentum"],
                    "form_trend": momentum_data["trend"]
                }
            }
    except Exception as e:
        logger.error(f"❌ Errore Team Metrics: {e}")
        return {"error": str(e)}

# ─── 9. INTEGRAZIONE BETTING AI E QUOTE REAL-TIME ────────────────────

async def get_multi_odds_with_links(home_team: str, away_team: str, league_name: str):
    """
    Recupera le quote reali da The-Odds-API per il match specificato.
    Se l'API fallisce, ritorna un set di quote fallback per non bloccare la UI.
    """
    api_league = ODDS_LEAGUE_MAP.get(league_name, "soccer_italy_serie_a")
    fallback_odds = [{
        "source": "1xBet (Copertura)", 
        "link": AFFILIATE_LINKS["1xBet"], 
        "h2h": {"1": 2.15, "X": 3.35, "2": 3.45},
        "total": {"line": "2.5", "over": 1.95, "under": 1.85}
    }]
    
    try:
        async with httpx.AsyncClient() as client:
            # Chiamata a The-Odds-API per mercati H2H e Totals
            url = f"https://api.the-odds-api.com/v4/sports/{api_league}/odds/"
            params = {
                "apiKey": ODDS_API_KEY,
                "regions": "eu",
                "markets": "h2h,totals",
                "oddsFormat": "decimal"
            }
            
            response = await client.get(url, params=params, timeout=6)
            if response.status_code != 200:
                logger.warning(f"⚠️ Quote API non raggiungibile (Status {response.status_code})")
                return fallback_odds
                
            data = response.json()
            if not isinstance(data, list) or len(data) == 0:
                return fallback_odds
                
            comparison = []
            # Cerchiamo il match specifico comparando le stringhe dei nomi team
            for match in data:
                h_api = match.get('home_team', '').lower()
                # Match "fuzzy": basta che le prime 4 lettere coincidano
                if home_team.lower()[:4] in h_api or away_team.lower()[:4] in h_api:
                    for bookmaker in match.get('bookmakers', [])[:4]:
                        bookie_name = bookmaker.get('title', 'Unknown')
                        bookie_data = {
                            "source": bookie_name,
                            "link": AFFILIATE_LINKS.get(bookie_name, AFFILIATE_LINKS["default"]),
                            "h2h": {"1": "-", "X": "-", "2": "-"},
                            "total": {"line": "2.5", "over": "-", "under": "-"}
                        }
                        
                        for market in bookmaker.get('markets', []):
                            outcomes = market.get('outcomes', [])
                            if market['key'] == 'h2h':
                                for o in outcomes:
                                    if o['name'] == match['home_team']: bookie_data["h2h"]["1"] = o['price']
                                    elif o['name'] == 'Draw': bookie_data["h2h"]["X"] = o['price']
                                    elif o['name'] == match['away_team']: bookie_data["h2h"]["2"] = o['price']
                            elif market['key'] == 'totals':
                                for o in outcomes:
                                    bookie_data["total"]["line"] = o.get('point', '2.5')
                                    if o['name'].lower() == 'over': bookie_data["total"]["over"] = o['price']
                                    else: bookie_data["total"]["under"] = o['price']
                        
                        comparison.append(bookie_data)
            
            return comparison if comparison else fallback_odds
            
    except Exception as e:
        logger.error(f"❌ Errore critico nel recupero quote: {e}")
        return fallback_odds


# ─── 9b. BATCH ODDS FETCHER FOR UPCOMING MATCHES ──────────────────────

async def fetch_all_league_odds() -> dict:
    """
    Fetch odds for ALL configured leagues from The-Odds-API in one batch.
    Returns a dict keyed by league name, each containing match tuples
    (home_team_lower, away_team_lower) -> {h2h, totals, btts}.
    Optimized to avoid per-match API calls and rate limits.
    """
    cache: dict = {}
    async with httpx.AsyncClient() as client:
        for league_name, api_sport_key in ODDS_LEAGUE_MAP.items():
            try:
                url = f"https://api.the-odds-api.com/v4/sports/{api_sport_key}/odds/"
                params = {
                    "apiKey": ODDS_API_KEY,
                    "regions": "eu",
                    "markets": "h2h,totals,spreads",
                    "oddsFormat": "decimal"
                }
                response = await client.get(url, params=params, timeout=8)
                if response.status_code != 200:
                    logger.warning(f"⚠️ Odds API unreachable for {league_name} (Status {response.status_code})")
                    continue

                data = response.json()
                if not isinstance(data, list):
                    continue

                league_matches: dict = {}
                for api_match in data:
                    h_team = api_match.get('home_team', '')
                    a_team = api_match.get('away_team', '')
                    key = (h_team.lower(), a_team.lower())

                    h2h = None
                    totals = None
                    spreads = None

                    # Take the first bookmaker's odds (best liquidity)
                    for bookmaker in api_match.get('bookmakers', [])[:1]:
                        for market in bookmaker.get('markets', []):
                            outcomes = market.get('outcomes', [])
                            if market['key'] == 'h2h' and h2h is None:
                                h2h = {}
                                for o in outcomes:
                                    if o['name'] == api_match['home_team']:
                                        h2h['1'] = float(o['price'])
                                    elif o['name'] == 'Draw':
                                        h2h['X'] = float(o['price'])
                                    elif o['name'] == api_match['away_team']:
                                        h2h['2'] = float(o['price'])
                            elif market['key'] == 'totals' and totals is None:
                                totals = {"line": "2.5", "over": 0.0, "under": 0.0}
                                for o in outcomes:
                                    totals['line'] = str(o.get('point', '2.5'))
                                    if o['name'].lower() == 'over':
                                        totals['over'] = float(o['price'])
                                    else:
                                        totals['under'] = float(o['price'])
                            elif market['key'] == 'spreads' and spreads is None:
                                spreads = []
                                for o in outcomes:
                                    spreads.append({
                                        "team": o['name'],
                                        "price": float(o['price']),
                                        "point": float(o.get('point', 0)),
                                    })

                    # BTTS is not a standard The-Odds-API market; set to None
                    league_matches[key] = {
                        "h2h": h2h,
                        "totals": totals,
                        "btts": None,
                        "spreads": spreads,
                    }

                cache[league_name] = league_matches
                logger.info(f"✅ Odds fetched for {league_name}: {len(league_matches)} matches")

            except Exception as e:
                logger.error(f"❌ Error fetching odds for {league_name}: {e}")

    return cache


# ── Team name mapping dictionary ──────────────────────────────────
# Maps common name variations to canonical forms used by The-Odds-API
TEAM_NAME_MAP = {
    # Serie A
    "ac milan": "milan",
    "milan": "milan",
    "inter": "inter",
    "inter milan": "inter",
    "fc inter": "inter",
    "internazionale": "inter",
    "hellas verona": "verona",
    "verona": "verona",
    "ssc napoli": "napoli",
    "napoli": "napoli",
    "as roma": "roma",
    "roma": "roma",
    "ss lazio": "lazio",
    "lazio": "lazio",
    "juventus": "juventus",
    "juve": "juventus",
    "atalanta": "atalanta",
    "atalanta bc": "atalanta",
    "fiorentina": "fiorentina",
    "acf fiorentina": "fiorentina",
    "torino": "torino",
    "torino fc": "torino",
    "udinese": "udinese",
    "udinese calcio": "udinese",
    "bologna": "bologna",
    "bologna fc": "bologna",
    "sassuolo": "sassuolo",
    "us sassuolo": "sassuolo",
    "empoli": "empoli",
    "empoli fc": "empoli",
    "genoa": "genoa",
    "genoa cfc": "genoa",
    "lecce": "lecce",
    "us lecce": "lecce",
    "monza": "monza",
    "ac monza": "monza",
    "frosinone": "frosinone",
    "frosinone calcio": "frosinone",
    "cagliari": "cagliari",
    "cagliari calcio": "cagliari",
    "salernitana": "salernitana",
    "us salernitana": "salernitana",
    "venezia": "venezia",
    "venezia fc": "venezia",
    "como": "como",
    "como 1907": "como",
    "parma": "parma",
    "parma calcio 1913": "parma",
    # Premier League
    "manchester united": "manchester utd",
    "man utd": "manchester utd",
    "man united": "manchester utd",
    "manchester city": "manchester city",
    "man city": "manchester city",
    "newcastle": "newcastle utd",
    "newcastle united": "newcastle utd",
    "tottenham": "tottenham",
    "tottenham hotspur": "tottenham",
    "west ham": "west ham",
    "west ham united": "west ham",
    "wolverhampton": "wolves",
    "wolves": "wolves",
    "brighton": "brighton",
    "brighton & hove albion": "brighton",
    "leicester": "leicester",
    "leicester city": "leicester",
    "nottingham forest": "nottingham forest",
    "nott'm forest": "nottingham forest",
    "notts forest": "nottingham forest",
    "ipswich": "ipswich",
    "ipswich town": "ipswich",
    "southampton": "southampton",
    "southampton fc": "southampton",
    "brentford": "brentford",
    "brentford fc": "brentford",
    "crystal palace": "crystal palace",
    "everton": "everton",
    "everton fc": "everton",
    "fulham": "fulham",
    "fulham fc": "fulham",
    "aston villa": "aston villa",
    "bournemouth": "bournemouth",
    "afc bournemouth": "bournemouth",
    # La Liga
    "real madrid": "real madrid",
    "fc barcelona": "barcelona",
    "barcelona": "barcelona",
    "atletico madrid": "atletico madrid",
    "atlético madrid": "atletico madrid",
    "real betis": "real betis",
    "betis": "real betis",
    "real sociedad": "real sociedad",
    "athletic bilbao": "athletic bilbao",
    "athletic club": "athletic bilbao",
    "valencia": "valencia",
    "valencia cf": "valencia",
    "villareal": "villareal",
    "villareal cf": "villareal",
    "sevilla": "sevilla",
    "fc sevilla": "sevilla",
    "osasuna": "osasuna",
    "ca osasuna": "osasuna",
    "getafe": "getafe",
    "getafe cf": "getafe",
    "rayo vallecano": "rayo vallecano",
    "girona": "girona",
    "girona fc": "girona",
    "alaves": "alaves",
    "deportivo alaves": "alaves",
    "celt de vigo": "celta vigo",
    "celta": "celta vigo",
    "celta vigo": "celta vigo",
    "mallorca": "mallorca",
    "rcd mallorca": "mallorca",
    "las palmas": "las palmas",
    "ud las palmas": "las palmas",
    # Bundesliga
    "bayern munich": "bayern munich",
    "fc bayern": "bayern munich",
    "bayern": "bayern munich",
    "borussia dortmund": "dortmund",
    "dortmund": "dortmund",
    "rb leipzig": "rb leipzig",
    "bayer leverkusen": "bayer leverkusen",
    "leverkusen": "bayer leverkusen",
    "eintracht frankfurt": "eintracht frankfurt",
    "frankfurt": "eintracht frankfurt",
    "borussia mönchengladbach": "borussia mg",
    "borussia monchengladbach": "borussia mg",
    "borussia mg": "borussia mg",
    "vfl wolfsburg": "wolfsburg",
    "wolfsburg": "wolfsburg",
    "sc freiburg": "freiburg",
    "freiburg": "freiburg",
    "1. fc heidenheim": "heidenheim",
    "heidenheim": "heidenheim",
    "fsv mainz 05": "mainz",
    "mainz": "mainz",
    "1. fc union berlin": "union berlin",
    "union berlin": "union berlin",
    "vfb stuttgart": "stuttgart",
    "stuttgart": "stuttgart",
    "sv werder bremen": "werder bremen",
    "werder bremen": "werder bremen",
    "fc augsburg": "augsburg",
    "augsburg": "augsburg",
    "1. fc koln": "koln",
    "koln": "koln",
    "1. fc köln": "koln",
    "fc koln": "koln",
    "tsg hoffenheim": "hoffenheim",
    "hoffenheim": "hoffenheim",
    "vfl bochum": "bochum",
    "bochum": "bochum",
    "sv darmstadt 98": "darmstadt",
    "darmstadt": "darmstadt",
    # Ligue 1
    "paris saint-germain": "psg",
    "psg": "psg",
    "paris sg": "psg",
    "olympique lyon": "lyon",
    "lyon": "lyon",
    "olympique lyonnais": "lyon",
    "olympique marseille": "marseille",
    "marseille": "marseille",
    "om": "marseille",
    "as monaco": "monaco",
    "monaco": "monaco",
    "lille": "lille",
    "losc lille": "lille",
    "nice": "nice",
    "ogc nice": "nice",
    "rennes": "rennes",
    "stade rennes": "rennes",
    "strasbourg": "strasbourg",
    "rc strasbourg": "strasbourg",
    "lens": "lens",
    "rc lens": "lens",
    "toulouse": "toulouse",
    "fc toulouse": "toulouse",
    "stade de reims": "reims",
    "reims": "reims",
    "stade reims": "reims",
    "montpellier": "montpellier",
    "montpellier hsc": "montpellier",
    "nantes": "nantes",
    "fc nantes": "nantes",
    "brest": "brest",
    "stade brestois": "brest",
    "stade brestois 29": "brest",
    "auxerre": "auxerre",
    "aj auxerre": "auxerre",
    "angers": "angers",
    "angers sco": "angers",
    "clermont": "clermont",
    "clermont foot": "clermont",
    "le havre": "le havre",
    "havre ac": "le havre",
    "metz": "metz",
    "fc metz": "metz",
    "saint-etienne": "saint-etienne",
    "as saint-etienne": "saint-etienne",
    "st etienne": "saint-etienne",
}


def _normalize_team_name(name: str) -> str:
    """Map common team name variations to canonical form using TEAM_NAME_MAP."""
    n = name.lower().strip()
    return TEAM_NAME_MAP.get(n, n)


def find_match_odds(odds_cache: dict, league_name: str, home_team: str, away_team: str) -> dict:
    """Find real odds for a specific match from the cached odds data using robust fuzzy matching.
    
    Strategy (in order):
      1. Exact match on normalized names (via TEAM_NAME_MAP)
      2. Reversed match (API has home/away swapped)
      3. Substring match (normalized name is found within API name)
      4. First-word fuzzy match (handles 'Milan' vs 'AC Milan')
    """
    league_odds = odds_cache.get(league_name, {})
    if not league_odds:
        return {"1X2": None, "overUnder": None, "btts": None, "spreads": None}

    h_key = home_team.lower()
    a_key = away_team.lower()
    h_norm = _normalize_team_name(home_team)
    a_norm = _normalize_team_name(away_team)

    def _build_result(raw: dict) -> dict:
        return {
            "1X2": raw.get("h2h"),
            "overUnder": raw.get("totals"),
            "btts": raw.get("btts"),
            "spreads": raw.get("spreads"),
        }

    # 1. Exact match on normalized names
    for (api_h, api_a), raw in league_odds.items():
        if _normalize_team_name(api_h) == h_norm and _normalize_team_name(api_a) == a_norm:
            return _build_result(raw)

    # 2. Reversed (home/away swapped in API response)
    for (api_h, api_a), raw in league_odds.items():
        if _normalize_team_name(api_h) == a_norm and _normalize_team_name(api_a) == h_norm:
            return _build_result(raw)

    # 3. Substring match (normalized name appears inside API name)
    for (api_h, api_a), raw in league_odds.items():
        api_h_lower = api_h.lower()
        api_a_lower = api_a.lower()
        if (h_norm in api_h_lower and a_norm in api_a_lower) or \
           (h_norm in api_a_lower and a_norm in api_h_lower):
            return _build_result(raw)

    # 4. First-word fuzzy match (handles 'Milan' vs 'AC Milan', 'Inter' vs 'Inter Milan')
    h_first = h_key.split()[0] if h_key.split() else h_key
    a_first = a_key.split()[0] if a_key.split() else a_key
    for (api_h, api_a), raw in league_odds.items():
        api_h_lower = api_h.lower()
        api_a_lower = api_a.lower()
        if (h_first in api_h_lower and a_first in api_a_lower) or \
           (h_first in api_a_lower and a_first in api_h_lower):
            return _build_result(raw)

    return {"1X2": None, "overUnder": None, "btts": None, "spreads": None}


@app.get("/api/betting/analyze-v2", tags=["betting"])
async def analyze_match_ai_v2(
    home: str = Query(..., description="Squadra in casa"), 
    away: str = Query(..., description="Squadra ospite"), 
    league: str = Query("Serie A", description="Campionato")
):
    """
    Genera un'analisi speculativa completa incrociando i dati matematici di Poisson
    con l'interpretazione tattica di DeepSeek AI.
    """
    try:
        logger.info(f"🤖 AI Analysis: Avvio elaborazione {home} vs {away} ({league})")
        
        # 1. Identificazione Lega ID per statistiche team
        async with local_engine.connect() as conn:
            l_row = (await conn.execute(text("SELECT id FROM league WHERE name ILIKE :n LIMIT 1"), {"n": f"%{league}%"})).fetchone()
            league_id = l_row[0] if l_row else 1

        # 2. Recupero Metriche Team (Usando il motore della Parte 2)
        h_profile = await get_team_metrics_complete(home, league)
        a_profile = await get_team_metrics_complete(away, league)
        
        # Se i dati sono insufficienti, usiamo valori di default
        def safe_get(profile, *keys, default=0.0):
            val = profile
            for k in keys:
                if isinstance(val, dict) and k in val:
                    val = val[k]
                else:
                    return default
            return val
        
        h_xg = safe_get(h_profile, "attack", "avg_xg", default=1.2)
        h_xga = safe_get(h_profile, "defense", "avg_xga", default=1.2)
        a_xg = safe_get(a_profile, "attack", "avg_xg", default=1.2)
        a_xga = safe_get(a_profile, "defense", "avg_xga", default=1.2)
        h_ppda = safe_get(h_profile, "defense", "pressing_ppda", default=1.0)
        h_momentum = safe_get(h_profile, "merit", "momentum_score", default=1.0)
        a_ppda = safe_get(a_profile, "defense", "pressing_ppda", default=1.0)
        a_momentum = safe_get(a_profile, "merit", "momentum_score", default=1.0)
        
        # 3. Calcolo Probabilità (Poisson Engine)
        math_core = calculate_true_expectancy(h_xg, h_xga, a_xg, a_xga)
        
        # 4. Recupero Quote Reali
        live_odds = await get_multi_odds_with_links(home, away, league)
        
        # 5. Elaborazione Prompt per DeepSeek
        prompt = f"""
        Sei l'analista esperto di 'Barsport Club'. Analizza tecnicamente il match: {home} vs {away} ({league}).
        DATI SQUADRA CASA ({home}): xG {h_xg}, PPDA {h_ppda}, Momentum {h_momentum}.
        DATI SQUADRA TRASFERTA ({away}): xG {a_xg}, PPDA {a_ppda}, Momentum {a_momentum}.
        
        MATEMATICA (Poisson): Probabilità vittoria casa: {math_core['probabilities']['1']}%, Pareggio: {math_core['probabilities']['X']}%, Trasferta: {math_core['probabilities']['2']}%.
        Over 2.5: {math_core['probabilities']['over25']}%.
        
        Rispondi ESCLUSIVAMENTE in formato JSON con questi campi:
        {{
          "analysis": "Testo approfondito sulle dinamiche tattiche attese",
          "verdict": "Consiglio scommessa secco basato sul valore (es. 1X + Over 1.5)",
          "score_prediction": "Risultato esatto consigliato",
          "risk_level": "Alto/Medio/Basso"
        }}
        """
        
        # Chiamata all'AI
        try:
            ai_response = await ai_client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                response_format={ "type": "json_object" },
                temperature=0.4
            )
            ai_data = json.loads(ai_response.choices[0].message.content)
        except Exception as ai_err:
            logger.warning(f"AI call failed, using mock: {ai_err}")
            ai_data = {
                "analysis": "Analisi tattica basata sui dati di Poisson.",
                "verdict": "1X + Over 1.5",
                "score_prediction": "2-1",
                "risk_level": "Medio"
            }
        
        return {
            "match_info": {"home": home, "away": away, "league": league},
            "mathematical_model": math_core,
            "ai_interpretation": ai_data,
            "market_odds": live_odds
        }
        
    except Exception as e:
        logger.error(f"❌ Fallimento AI Analysis: {e}")
        logger.error(traceback.format_exc())
        return {"error": "L'analista AI è momentaneamente offline."}


# ─── 12b. UPCOMING MATCHES FOR VALUE BROKER DASHBOARD ────────────────

# ─── 10b. SHARED ELO WARM-UP ENGINE ──────────────────────────────────────

async def run_elo_warmup(conn) -> Dict[str, float]:
    """
    Run the full Elo warm-up on historical completed matches using xG differentials.
    
    Initializes every team at 1500.0 Elo, then iterates all completed matches
    chronologically, updating ratings via:
        expected_diff = (home_elo - away_elo) / 100.0
        actual_diff   = home_xG - away_xG
        delta         = K * (actual_diff - expected_diff)
    
    Returns:
        Dict[str, float]: team_name -> current Elo rating after warm-up
    """
    K = 20
    from collections import defaultdict
    ratings: Dict[str, float] = defaultdict(lambda: 1500.0)

    hist_query = text("""
        SELECT th.name AS home_team, ta.name AS away_team,
               m."home_xG", m."away_xG"
        FROM matchcalendar m
        JOIN team th ON m.home_team_id = th.id
        JOIN team ta ON m.away_team_id = ta.id
        WHERE m.is_completed = True
          AND m."home_xG" IS NOT NULL
          AND m."away_xG" IS NOT NULL
        ORDER BY m.match_datetime ASC, m.id ASC
    """)
    hist_rows = (await conn.execute(hist_query)).fetchall()

    # Seed every team so defaultdict populates
    for r in hist_rows:
        _ = ratings[r[0]], ratings[r[1]]

    # Warm-up loop
    for r in hist_rows:
        home = r[0]
        away = r[1]
        home_xg = float(r[2]) if r[2] is not None else 0.0
        away_xg = float(r[3]) if r[3] is not None else 0.0

        home_elo_before = ratings[home]
        away_elo_before = ratings[away]

        expected_diff = (home_elo_before - away_elo_before) / 100.0
        actual_diff = home_xg - away_xg
        delta = K * (actual_diff - expected_diff)

        ratings[home] += delta
        ratings[away] -= delta

    return ratings


def elo_diff_to_probs(elo_diff: float) -> Dict[str, float]:
    """
    Convert an Elo differential (home - away) into 3-way probabilities (1, X, 2).
    
    Uses the logistic expected-score function and a Gaussian draw peak:
        E_home = 1 / (1 + 10^(-elo_diff/400))
        draw   = 0.25 * exp(-(elo_diff/400)^2)
        prob_1 = (1 - draw) * E_home
        prob_2 = (1 - draw) * (1 - E_home)
        prob_X = draw
    """
    expected_home = 1.0 / (1.0 + 10.0 ** (-elo_diff / 400.0))
    draw_prob = 0.25 * (2.71828 ** (-((elo_diff / 400.0) ** 2)))
    prob_home = (1.0 - draw_prob) * expected_home
    prob_away = (1.0 - draw_prob) * (1.0 - expected_home)
    prob_draw = draw_prob

    return {
        "home": round(prob_home, 4),
        "draw": round(prob_draw, 4),
        "away": round(prob_away, 4),
    }


@app.get("/api/v1/betting/upcoming-matches")
async def get_upcoming_matches_betting():
    """
    Returns upcoming matches with real team statistics (xG, xGA, PPDA, deep passes),
    REAL market odds from The-Odds-API, AND Elo-xG implied probabilities.
    Each match is shaped as MatchAdvanced + market_odds + elo_probs so the frontend
    can compute true edges using the hardened 5-year Elo-xG model.
    """
    async with local_engine.connect() as conn:
        # 1. Fetch upcoming matches
        query = text("""
            SELECT m.id, th.name AS home_team, ta.name AS away_team,
                   l.name AS league_name, m.match_datetime
            FROM matchcalendar m
            JOIN team th ON m.home_team_id = th.id
            JOIN team ta ON m.away_team_id = ta.id
            JOIN league l ON m.league_id = l.id
            WHERE m.is_completed = False
              AND m.match_datetime > NOW() - INTERVAL '2 hours'
            ORDER BY m.match_datetime ASC
            LIMIT 50
        """)
        rows = (await conn.execute(query)).fetchall()

        if not rows:
            return []

        # 2. Fetch real odds for ALL leagues in one batch (optimized, avoids rate limits)
        odds_cache = await fetch_all_league_odds()

        # 3. Run the shared Elo warm-up once for all matches
        elo_ratings = await run_elo_warmup(conn)

        results = []
        # 4. For each match, compute per-team season averages from completed matches
        for r in rows:
            match_id = r[0]
            home_team = r[1]
            away_team = r[2]
            league_name = r[3]
            match_dt = r[4]

            # Resolve league id for stats queries
            l_row = (await conn.execute(
                text("SELECT id FROM league WHERE name ILIKE :n LIMIT 1"),
                {"n": f"%{league_name}%"}
            )).fetchone()
            lid = l_row[0] if l_row else 1

            async def _team_stats(team: str) -> dict:
                """Compute per-team season averages from completed matches."""
                row = (await conn.execute(text("""
                    SELECT
                        AVG(CASE WHEN th.name = :t THEN m."home_xG" ELSE m."away_xG" END) AS xG_for,
                        AVG(CASE WHEN th.name = :t THEN m."away_xG" ELSE m."home_xG" END) AS xG_against,
                        AVG(CASE WHEN th.name = :t THEN m.home_ppda ELSE m.away_ppda END) AS ppda,
                        AVG(CASE WHEN th.name = :t THEN m.home_deep ELSE m.away_deep END) AS deep_for,
                        AVG(CASE WHEN th.name = :t THEN m.away_deep ELSE m.home_deep END) AS deep_against
                    FROM matchcalendar m
                    JOIN team th ON m.home_team_id = th.id
                    JOIN team ta ON m.away_team_id = ta.id
                    WHERE (th.name = :t OR ta.name = :t)
                      AND m.is_completed = True
                      AND m.league_id = :lid
                """), {"t": team, "lid": lid})).fetchone()

                if not row or all(v is None for v in row):
                    return {"xG": 0.0, "xGA": 0.0, "xA": 0.0, "ppda": 0.0,
                            "deepPassesConceded": 0, "deepPassesMade": 0,
                            "shotsFaced": 0, "shotsMade": 0}

                def sf(v, default=0.0):
                    return float(v) if v is not None else default

                return {
                    "xG":                round(sf(row[0]), 2),
                    "xGA":               round(sf(row[1]), 2),
                    "xA":                0.0,
                    "ppda":              round(sf(row[2]), 2),
                    "deepPassesConceded": int(round(sf(row[4]))),
                    "deepPassesMade":     int(round(sf(row[3]))),
                    "shotsFaced":        0,
                    "shotsMade":         0,
                }

            home_stats = await _team_stats(home_team)
            away_stats = await _team_stats(away_team)

            # 5. Get real odds from the batch cache
            match_odds = find_match_odds(odds_cache, league_name, home_team, away_team)

            # 6. Compute Elo-xG implied probabilities for this match
            #    Apply 85-point Home Field Advantage (HFA) to home Elo
            #    before calculating the differential. This fixes the
            #    ridiculous +260% edges on away underdogs.
            home_elo = elo_ratings.get(home_team, 1500.0)
            away_elo = elo_ratings.get(away_team, 1500.0)
            elo_diff = (home_elo + 85.0) - away_elo  # ← 85-pt HFA
            elo_probs = elo_diff_to_probs(elo_diff)

            # 7. Extract AH spreads and OU lines for tactical signal evaluation
            spreads_raw = match_odds.get("spreads") or []
            totals_raw = match_odds.get("overUnder")

            ah_lines = []
            if spreads_raw:
                for s in spreads_raw:
                    is_home_norm = _normalize_team_name(s["team"]) == _normalize_team_name(home_team)
                    ah_lines.append({
                        "home_side": is_home_norm,
                        "team": s["team"],
                        "point": s["point"],
                        "price": s["price"],
                    })

            ou_lines = None
            if totals_raw:
                ou_lines = {
                    "line": totals_raw.get("line", "2.5"),
                    "over": totals_raw.get("over", 0.0),
                    "under": totals_raw.get("under", 0.0),
                }

            # 8. Evaluate tactical signals (Pressing Trap, Shootout, Sterile)
            #    using same strict PPDA and Deep Completions rules as Lab 2.
            def _eval_signals(
                he: dict, ae: dict,
                ah: list, ou: dict | None
            ) -> list:
                sigs = []

                # Resolve AH points for home/away orientation
                home_ah_pt = None
                away_ah_pt = None
                for s in (ah or []):
                    if s["home_side"]:
                        home_ah_pt = s["point"]
                    else:
                        away_ah_pt = s["point"]

                # ── RULE 1: PRESSING TRAP (Home) ────────────────
                if (he["ppda"] > 0 and he["ppda"] < 11.0
                    and ae["ppda"] > 14.0
                    and ae["deepPassesMade"] <= 5
                    and home_ah_pt is not None
                    and home_ah_pt >= -1.0):
                    sigs.append({
                        "type": "AH_HOME",
                        "name": "🛑 PRESSING TRAP",
                        "desc": "Home press will suffocate passive away team."
                    })

                # ── RULE 1 (REVERSE): PRESSING TRAP (Away) ─────
                if (ae["ppda"] > 0 and ae["ppda"] < 11.0
                    and he["ppda"] > 14.0
                    and he["deepPassesMade"] <= 5
                    and away_ah_pt is not None
                    and away_ah_pt >= -1.0):
                    sigs.append({
                        "type": "AH_AWAY",
                        "name": "🛑 PRESSING TRAP (A)",
                        "desc": "Away press will suffocate passive home team."
                    })

                ou_val = float(ou["line"]) if ou and ou.get("line") else None

                # ── RULE 2: SHOOTOUT (Over) ────────────────────
                if (he["xGA"] > 1.30
                    and ae["xGA"] > 1.30
                    and he["deepPassesMade"] > 6
                    and ae["deepPassesMade"] > 6
                    and ou_val is not None
                    and ou_val in (2.5, 2.75)):
                    sigs.append({
                        "type": "OVER",
                        "name": "🔥 SHOOTOUT",
                        "desc": "High box penetration vs leaky defenses."
                    })

                # ── RULE 3: STERILE MATCH (Under) ──────────────
                if (he["deepPassesMade"] <= 5
                    and ae["deepPassesMade"] <= 5
                    and he["xG"] < 1.10
                    and ae["xG"] < 1.10
                    and ou_val is not None
                    and ou_val >= 2.5):
                    sigs.append({
                        "type": "UNDER",
                        "name": "🧱 STERILE MATCH",
                        "desc": "Lack of box penetration from both sides."
                    })

                return sigs

            tactical_signals = _eval_signals(
                home_stats, away_stats, ah_lines, ou_lines
            )

            results.append({
                "id": str(match_id),
                "home": home_team,
                "away": away_team,
                "league": league_name,
                "date": match_dt.strftime("%Y-%m-%d"),
                "match_datetime": match_dt.isoformat(),
                "homeStats": home_stats,
                "awayStats": away_stats,
                "homePlayers": [],
                "awayPlayers": [],
                "market_odds": match_odds,  # REAL odds from The-Odds-API
                "elo_probs": elo_probs,     # Elo-xG implied probabilities (with 85-pt HFA)
                "tactical_signals": tactical_signals,  # Lab 2 tactical triggers
            })

        return results


# ─── 12c. ELO-xG LAB: R&D WARM-UP ENGINE ──────────────────────────────

@app.get("/api/v1/betting/lab/elo-xg")
async def elo_xg_laboratory():
    """
    Phase 2 R&D: Elo rating system based purely on Expected Goals (xG).

    Warm-up Engine:
        1. Fetch ALL completed matches ordered chronologically.
        2. Initialize Elo at 1500.0 for every team.
        3. For each historical match:
            expected_diff = (ratings[home] - ratings[away]) / 100.0
            actual_diff   = home_xG - away_xG
            ratings[home] += K * (actual_diff - expected_diff)
            ratings[away] -= K * (actual_diff - expected_diff)
        4. Project onto upcoming matches with Elo → 3-way probabilities.

    Returns:
        - warmup: list of every processed match with Elo deltas
        - projections: upcoming matches with Elo ratings and implied 1X2 probs
        - finals: final Elo table after warm-up (sorted by rating)
    """
    K = 20
    from collections import defaultdict
    ratings: Dict[str, float] = defaultdict(lambda: 1500.0)

    warmup_log = []
    projections = []
    final_table = []

    try:
        async with local_engine.connect() as conn:
            # ── 1. Fetch all completed matches chronologically ──────────
            hist_query = text("""
                SELECT m.id, th.name AS home_team, ta.name AS away_team,
                       m."home_xG", m."away_xG", m.match_datetime
                FROM matchcalendar m
                JOIN team th ON m.home_team_id = th.id
                JOIN team ta ON m.away_team_id = ta.id
                WHERE m.is_completed = True
                  AND m."home_xG" IS NOT NULL
                  AND m."away_xG" IS NOT NULL
                ORDER BY m.match_datetime ASC, m.id ASC
            """)
            hist_rows = (await conn.execute(hist_query)).fetchall()

            # Ensure every team name is seeded
            for r in hist_rows:
                _ = ratings[r[1]], ratings[r[2]]  # seed via defaultdict

            # ── 2. Warm-up loop ────────────────────────────────────────
            for r in hist_rows:
                match_id = r[0]
                home = r[1]
                away = r[2]
                home_xg = float(r[3]) if r[3] is not None else 0.0
                away_xg = float(r[4]) if r[4] is not None else 0.0
                dt = r[5]

                home_elo_before = ratings[home]
                away_elo_before = ratings[away]

                expected_diff = (home_elo_before - away_elo_before) / 100.0
                actual_diff = home_xg - away_xg
                delta = K * (actual_diff - expected_diff)

                ratings[home] += delta
                ratings[away] -= delta

                warmup_log.append({
                    "match_id": str(match_id),
                    "date": dt.strftime("%Y-%m-%d") if dt else "N/A",
                    "home_team": home,
                    "away_team": away,
                    "home_xG": round(home_xg, 2),
                    "away_xG": round(away_xg, 2),
                    "home_elo_before": round(home_elo_before, 1),
                    "away_elo_before": round(away_elo_before, 1),
                    "elo_diff_expected": round(expected_diff, 3),
                    "xg_diff_actual": round(actual_diff, 3),
                    "elo_delta": round(delta, 1),
                    "home_elo_after": round(ratings[home], 1),
                    "away_elo_after": round(ratings[away], 1),
                })

            # ── 3. Final Elo table ─────────────────────────────────────
            final_table = sorted(
                [{"team": team, "elo": round(rating, 1)} for team, rating in ratings.items()],
                key=lambda x: x["elo"],
                reverse=True,
            )

            # ── 4. Fetch upcoming matches ──────────────────────────────
            upc_query = text("""
                SELECT m.id, th.name AS home_team, ta.name AS away_team,
                       l.name AS league_name, m.match_datetime
                FROM matchcalendar m
                JOIN team th ON m.home_team_id = th.id
                JOIN team ta ON m.away_team_id = ta.id
                JOIN league l ON m.league_id = l.id
                WHERE m.is_completed = False
                  AND m.match_datetime > NOW() - INTERVAL '2 hours'
                ORDER BY m.match_datetime ASC
                LIMIT 50
            """)
            upc_rows = (await conn.execute(upc_query)).fetchall()

            for r in upc_rows:
                home = r[1]
                away = r[2]
                league_name = r[3]
                dt = r[4]

                home_elo = ratings.get(home, 1500.0)
                away_elo = ratings.get(away, 1500.0)
                elo_diff = home_elo - away_elo

                # ── Elo → 3-way probabilities (shared utility) ─────────
                elo_probs = elo_diff_to_probs(elo_diff)

                projections.append({
                    "match_id": str(r[0]),
                    "date": dt.strftime("%Y-%m-%d") if dt else "N/A",
                    "league": league_name,
                    "home_team": home,
                    "away_team": away,
                    "home_elo": round(home_elo, 1),
                    "away_elo": round(away_elo, 1),
                    "elo_diff": round(elo_diff, 1),
                    "probabilities": {
                        "1": round(elo_probs["home"] * 100, 2),
                        "X": round(elo_probs["draw"] * 100, 2),
                        "2": round(elo_probs["away"] * 100, 2),
                    },
                })

    except Exception as e:
        logger.error(f"❌ Elo-xG Lab error: {e}")
        logger.error(traceback.format_exc())
        return {
            "error": str(e),
            "warmup": [],
            "projections": [],
            "finals": [],
        }

    return {
        "meta": {
            "k_factor": K,
            "initial_elo": 1500.0,
            "matches_processed": len(warmup_log),
            "teams_tracked": len(final_table),
            "upcoming_matches": len(projections),
        },
        "warmup": warmup_log,
        "projections": projections,
        "finals": final_table,
    }


@app.get("/api/betting/calendar/grouped", tags=["betting"])
async def get_calendar_grouped_v2():
    """Raggruppa i prossimi match per lega per la dashboard."""
    async with local_engine.connect() as conn:
        query = text("""
            SELECT m.id, th.name, ta.name, m.match_datetime, l.name
            FROM matchcalendar m 
            JOIN team th ON m.home_team_id = th.id 
            JOIN team ta ON m.away_team_id = ta.id 
            JOIN league l ON m.league_id = l.id
            WHERE m.is_completed = False 
              AND m.match_datetime > NOW() - INTERVAL '2 hours'
            ORDER BY m.match_datetime ASC LIMIT 150
        """)
        rows = (await conn.execute(query)).fetchall()
        calendar = {}
        for r in rows:
            league_name = r[4]
            if league_name not in calendar: calendar[league_name] = []
            calendar[league_name].append({
                "id": r[0], "home": r[1], "away": r[2], 
                "date": r[3].strftime("%d/%m %H:%M")
            })
        return calendar

# ─── ENDPOINT MANCANTI PER FINDER.HTML ──────────────────────────────

@app.get("/api/shots/{player_name}", tags=["scout"])
async def get_shots_by_player(player_name: str):
    """Tiri del giocatore per la Shot Map (coordinate X/Y, xG, result)."""
    try:
        async with local_engine.connect() as conn:
            res = await conn.execute(text("""
                SELECT minute, "xG", result, "X", "Y", situation,
                       COALESCE("shotType", shot_type) AS shot_type
                FROM shots
                WHERE player ILIKE :n
                ORDER BY minute ASC
            """), {"n": player_name})
            return [
                {
                    "minute":    r[0],
                    "xG":        sanitize_metric(r[1]),
                    "result":    r[2] or "",
                    "X":         sanitize_metric(r[3]),
                    "Y":         sanitize_metric(r[4]),
                    "situation": r[5] or "Open Play",
                    "shotType":  r[6] or "",
                }
                for r in res.fetchall()
            ]
    except Exception as e:
        logger.error(f"shots error '{player_name}': {e}")
        return []


@app.get("/api/undervalued", tags=["scout"])
async def get_undervalued(
    category: str = Query("generale"),
    league_id: int = Query(0),
    size: int = Query(50),
):
    """Analisi sottovalutati per categoria. Filtro opzionale per lega."""
    try:
        join_clause  = "JOIN matchcalendar mc ON rosters.match_id = mc.id" if league_id > 0 else ""
        where_clause = "WHERE mc.league_id = :lid" if league_id > 0 else ""
        params: dict = {"size": size}
        if league_id > 0:
            params["lid"] = league_id

        queries = {
            "generale": f"""
                SELECT rosters.player, MAX(rosters.position) AS position,
                       SUM(rosters.time) AS time, SUM(rosters.goals) AS goals,
                       SUM(rosters."xG") AS xG,
                       SUM(rosters."xG") - SUM(rosters.goals) AS xg_debt
                FROM rosters {join_clause} {where_clause}
                GROUP BY rosters.player
                HAVING SUM(rosters.time) > 500
                   AND SUM(rosters."xG") > SUM(rosters.goals)
                   AND SUM(rosters."xG") > 0.5
                ORDER BY xg_debt DESC LIMIT :size
            """,
            "bomber": f"""
                SELECT rosters.player, MAX(rosters.position) AS position,
                       SUM(rosters.time) AS time, SUM(rosters.goals) AS goals,
                       SUM(rosters."xG") AS xG,
                       SUM(rosters."xG") - SUM(rosters.goals) AS xg_debt
                FROM rosters {join_clause} {where_clause}
                GROUP BY rosters.player
                HAVING SUM(rosters.time) > 500
                   AND SUM(rosters."xG") - SUM(rosters.goals) > 2.0
                ORDER BY xg_debt DESC LIMIT :size
            """,
            "registi": f"""
                SELECT rosters.player, MAX(rosters.position) AS position,
                       SUM(rosters.time) AS time, SUM(rosters.goals) AS goals,
                       SUM(rosters."xG") AS xG,
                       SUM(rosters."xA") - SUM(rosters.assists) AS xg_debt
                FROM rosters {join_clause} {where_clause}
                GROUP BY rosters.player
                HAVING SUM(rosters.time) > 500
                   AND SUM(rosters."xA") - SUM(rosters.assists) > 1.5
                ORDER BY xg_debt DESC LIMIT :size
            """,
            "motori": f"""
                SELECT rosters.player, MAX(rosters.position) AS position,
                       SUM(rosters.time) AS time, SUM(rosters.goals) AS goals,
                       SUM(rosters."xG") AS xG,
                       SUM(rosters."xGChain") / NULLIF(SUM(rosters.time), 0) * 90 AS xg_debt
                FROM rosters {join_clause} {where_clause}
                GROUP BY rosters.player
                HAVING SUM(rosters.time) > 500
                   AND SUM(rosters."xGChain") / NULLIF(SUM(rosters.time), 0) * 90 > 0.4
                ORDER BY xg_debt DESC LIMIT :size
            """,
            "costruttori": f"""
                SELECT rosters.player, MAX(rosters.position) AS position,
                       SUM(rosters.time) AS time, SUM(rosters.goals) AS goals,
                       SUM(rosters."xG") AS xG,
                       SUM(rosters."xGBuildup") / NULLIF(SUM(rosters.time), 0) * 90 AS xg_debt
                FROM rosters {join_clause} {where_clause}
                GROUP BY rosters.player
                HAVING SUM(rosters.time) > 500
                   AND SUM(rosters."xGBuildup") / NULLIF(SUM(rosters.time), 0) * 90 > 0.3
                ORDER BY xg_debt DESC LIMIT :size
            """,
            "sprecatori": f"""
                SELECT rosters.player, MAX(rosters.position) AS position,
                       SUM(rosters.time) AS time, SUM(rosters.goals) AS goals,
                       SUM(rosters."xG") AS xG,
                       SUM(rosters."xG") - SUM(rosters.goals) AS xg_debt
                FROM rosters {join_clause} {where_clause}
                GROUP BY rosters.player
                HAVING SUM(rosters.time) > 500
                   AND SUM(rosters."xG") > 3
                   AND SUM(rosters.goals)::float / NULLIF(SUM(rosters."xG"), 0) < 0.5
                ORDER BY xg_debt DESC LIMIT :size
            """,
            "trap_over": f"""
                SELECT rosters.player, MAX(rosters.position) AS position,
                       SUM(rosters.time) AS time, SUM(rosters.goals) AS goals,
                       SUM(rosters."xG") AS xG,
                       SUM(rosters.goals) - SUM(rosters."xG") AS xg_debt
                FROM rosters {join_clause} {where_clause}
                GROUP BY rosters.player
                HAVING SUM(rosters.time) > 500
                   AND SUM(rosters.goals) > SUM(rosters."xG") * 1.5
                   AND SUM(rosters."xG") > 1.0
                ORDER BY xg_debt DESC LIMIT :size
            """,
        }

        sql = queries.get(category, queries["generale"])
        async with local_engine.connect() as conn:
            res = await conn.execute(text(sql), params)
            rows = res.mappings().all()

        return [
            {
                "player":   row["player"],
                "position": row.get("position") or "N/A",
                "time":     int(row["time"] or 0),
                "goals":    int(row["goals"] or 0),
                "xG":       round(sanitize_metric(row["xG"]), 2),
                "xg_debt":  round(sanitize_metric(row["xg_debt"]), 2),
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"undervalued error (category={category}): {e}")
        return {"error": str(e)}


@app.get("/api/h2h", tags=["scout"])
async def head_to_head(p1: str = Query(...), p2: str = Query(...)):
    """Confronto diretto tra due giocatori con radar percentili."""
    async def get_stats(conn, name: str) -> dict:
        r = (await conn.execute(text("""
            SELECT SUM("xG"), SUM("xA"), SUM("xGChain"), SUM("xGBuildup"),
                   SUM(shots), SUM(time)
            FROM rosters WHERE player ILIKE :n
        """), {"n": f"%{name}%"})).fetchone()

        if not r or not r[5]:
            return {"xg": 0.0, "xa": 0.0, "radar": [0, 0, 0, 0, 0, 0]}

        xg, xa, chain, build, sh, mins = [sanitize_metric(x) for x in r]
        mins = max(mins, 1.0)

        distrib = (await conn.execute(text("""
            SELECT SUM("xG"), SUM("xA"), SUM("xGChain"), SUM("xGBuildup"), SUM(shots), SUM(time)
            FROM rosters GROUP BY player HAVING SUM(time) > 500
        """))).fetchall()

        def pct(my_val, col):
            dist = [(sanitize_metric(row[col]) / max(sanitize_metric(row[5]), 1)) * 90 for row in distrib]
            if not dist: return 0.0
            rank = sum(v < (my_val / mins * 90) for v in dist)
            return round(rank / len(dist) * 100, 1)

        return {
            "xg":   round(sanitize_metric(xg) / mins * 90, 3),
            "xa":   round(sanitize_metric(xa) / mins * 90, 3),
            "radar": [pct(xg, 0), pct(xa, 1), pct(sh, 4), pct(chain, 2), pct(build, 3), 0.0],
        }

    try:
        async with local_engine.connect() as conn:
            d1 = await get_stats(conn, p1)
            d2 = await get_stats(conn, p2)
        return {"p1": d1, "p2": d2}
    except Exception as e:
        logger.error(f"h2h error: {e}")
        return {"error": str(e)}
    
# ─── 14. RIPRISTINO MATCH DETAIL (FIX DATI AVANZATI) ──────────────────

@app.get("/api/match/{match_id}")
async def get_match_detail(match_id: int):
    """Recupera il dettaglio completo di un match con TUTTE le metriche avanzate."""
    try:
        async with local_engine.connect() as conn:
            query = text("""
                SELECT 
                    m.id, m.match_datetime, l.name as league,
                    th.name as home_team, ta.name as away_team,
                    m.home_goals, m.away_goals,
                    m."home_xG", m."away_xG",
                    m.home_ppda, m.away_ppda,
                    m.home_deep, m.away_deep,
                    m.home_xpts, m.away_xpts,
                    m.is_completed,
                    m.ai_verdict
                FROM matchcalendar m
                JOIN team th ON m.home_team_id = th.id
                JOIN team ta ON m.away_team_id = ta.id
                JOIN league l ON m.league_id = l.id
                WHERE m.id = :id
            """)
            res = await conn.execute(query, {"id": match_id})
            r = res.fetchone()
            
            if not r:
                raise HTTPException(status_code=404, detail="Match non trovato")
            
            # Mappatura precisa per il frontend
            return {
                "id": r[0],
                "date": r[1].strftime("%d/%m/%Y %H:%M") if r[1] else "N/D",
                "league": r[2],
                "home": r[3],
                "away": r[4],
                "goals": {"h": r[5], "a": r[6]},
                "xg": {"h": sanitize_metric(r[7]), "a": sanitize_metric(r[8])},
                "ppda": {"h": sanitize_metric(r[9]), "a": sanitize_metric(r[10])},
                "deep": {"h": sanitize_metric(r[11]), "a": sanitize_metric(r[12])},
                "xpts": {"h": sanitize_metric(r[13]), "a": sanitize_metric(r[14])},
                "completed": r[15],
                "ai_verdict": r[16] or "Analisi non disponibile"
            }
    except Exception as e:
        logger.error(f"❌ Errore critico nel recupero match {match_id}: {e}")
        return {"error": str(e)}


# ─── 13. ADVANCED METRICS MATRIX (LAB 2) ──────────────────────────────

@app.get("/api/v1/betting/lab/matrix")
async def betting_lab_matrix():
    """
    ADVANCED METRICS MATRIX (LAB 2)
    ===============================
    Returns upcoming matches with REAL Asian Handicap (spreads) and Over/Under (totals)
    market lines from The-Odds-API, combined with each team's season-average advanced
    metrics (xG, xGA, PPDA, Deep).

    The frontend uses this raw data to visually compare market pricing vs. playstyle
    mismatches without any 1X2 noise or fake probabilities.
    """
    async with local_engine.connect() as conn:
        # 1. Fetch upcoming matches
        query = text("""
            SELECT m.id, th.name AS home_team, ta.name AS away_team,
                   l.name AS league_name, m.match_datetime
            FROM matchcalendar m
            JOIN team th ON m.home_team_id = th.id
            JOIN team ta ON m.away_team_id = ta.id
            JOIN league l ON m.league_id = l.id
            WHERE m.is_completed = False
              AND m.match_datetime > NOW() - INTERVAL '2 hours'
            ORDER BY m.match_datetime ASC
            LIMIT 50
        """)
        rows = (await conn.execute(query)).fetchall()

        if not rows:
            return {"matches": [], "meta": {"total": 0}}

        # 2. Fetch real odds for ALL leagues in one batch
        odds_cache = await fetch_all_league_odds()

        results = []
        for r in rows:
            match_id = r[0]
            home_team = r[1]
            away_team = r[2]
            league_name = r[3]
            match_dt = r[4]

            # Resolve league id for stats queries
            l_row = (await conn.execute(
                text("SELECT id FROM league WHERE name ILIKE :n LIMIT 1"),
                {"n": f"%{league_name}%"}
            )).fetchone()
            lid = l_row[0] if l_row else 1

            async def _team_advanced_stats(team: str) -> dict:
                """Compute per-team advanced season averages from completed matches."""
                row = (await conn.execute(text("""
                    SELECT
                        AVG(CASE WHEN th.name = :t THEN m."home_xG" ELSE m."away_xG" END) AS xG_for,
                        AVG(CASE WHEN th.name = :t THEN m."away_xG" ELSE m."home_xG" END) AS xG_against,
                        AVG(CASE WHEN th.name = :t THEN m.home_ppda ELSE m.away_ppda END) AS ppda,
                        AVG(CASE WHEN th.name = :t THEN m.home_deep ELSE m.away_deep END) AS deep_for,
                        AVG(CASE WHEN th.name = :t THEN m.away_deep ELSE m.home_deep END) AS deep_against
                    FROM matchcalendar m
                    JOIN team th ON m.home_team_id = th.id
                    JOIN team ta ON m.away_team_id = ta.id
                    WHERE (th.name = :t OR ta.name = :t)
                      AND m.is_completed = True
                      AND m.league_id = :lid
                """), {"t": team, "lid": lid})).fetchone()

                if not row or all(v is None for v in row):
                    return {"xG": 0.0, "xGA": 0.0, "ppda": 0.0, "deep": 0}

                def sf(v, default=0.0):
                    return float(v) if v is not None else default

                return {
                    "xG":   round(sf(row[0]), 2),
                    "xGA":  round(sf(row[1]), 2),
                    "ppda": round(sf(row[2]), 2),
                    "deep": int(round(sf(row[3]))),
                }

            home_stats = await _team_advanced_stats(home_team)
            away_stats = await _team_advanced_stats(away_team)

            # 3. Get real odds from batch cache — extract spreads and totals only
            raw_odds = find_match_odds(odds_cache, league_name, home_team, away_team)

            # Extract Asian Handicap (spreads) and Over/Under (totals)
            spreads_raw = raw_odds.get("spreads") or []
            totals_raw = raw_odds.get("overUnder")

            # Format spreads into AH lines with home/away orientation
            ah_lines = []
            if spreads_raw:
                for s in spreads_raw:
                    # The-Odds-API returns team name in the spread outcome
                    is_home_norm = _normalize_team_name(s["team"]) == _normalize_team_name(home_team)
                    ah_lines.append({
                        "home_side": is_home_norm,
                        "team": s["team"],
                        "point": s["point"],
                        "price": s["price"],
                    })

            # Format Over/Under
            ou_lines = None
            if totals_raw:
                ou_lines = {
                    "line": totals_raw.get("line", "2.5"),
                    "over": totals_raw.get("over", 0.0),
                    "under": totals_raw.get("under", 0.0),
                }

            # 4. Compute mismatch deltas (PPDA diff, Deep diff)
            ppda_delta = home_stats["ppda"] - away_stats["ppda"]  # lower PPDA = more aggressive press
            deep_delta = home_stats["deep"] - away_stats["deep"]    # higher deep = more penetration

            # 5. Evaluate tactical signals for this match
            def _tactical_signals(
                he: dict, ae: dict,
                ah: list, ou: dict | None
            ) -> list:
                sigs = []

                # Resolve AH points for home/away orientation
                home_ah_pt = None
                away_ah_pt = None
                for s in (ah or []):
                    if s["home_side"]:
                        home_ah_pt = s["point"]
                    else:
                        away_ah_pt = s["point"]

                # ── RULE 1: PRESSING TRAP (Home) ──────────────────────
                if (he["ppda"] > 0 and he["ppda"] < 11.0       # Home aggressively presses
                    and ae["ppda"] > 14.0                       # Away is passive
                    and ae["deep"] <= 5                         # Away can't enter box
                    and home_ah_pt is not None
                    and home_ah_pt >= -1.0):                    # AH line ≤ -1.0 (favourable for home)
                    sigs.append({
                        "type": "AH_HOME",
                        "name": "🛑 PRESSING TRAP",
                        "desc": "Home press will suffocate passive away team."
                    })

                # ── RULE 1 (REVERSE): PRESSING TRAP (Away) ────────────
                if (ae["ppda"] > 0 and ae["ppda"] < 11.0       # Away aggressively presses
                    and he["ppda"] > 14.0                       # Home is passive
                    and he["deep"] <= 5                         # Home can't enter box
                    and away_ah_pt is not None
                    and away_ah_pt >= -1.0):                    # AH line favourable for away
                    sigs.append({
                        "type": "AH_AWAY",
                        "name": "🛑 PRESSING TRAP (A)",
                        "desc": "Away press will suffocate passive home team."
                    })

                ou_val = float(ou["line"]) if ou and ou.get("line") else None

                # ── RULE 2: SHOOTOUT (Over) ───────────────────────────
                if (he["xGA"] > 1.30
                    and ae["xGA"] > 1.30
                    and he["deep"] > 6
                    and ae["deep"] > 6
                    and ou_val is not None
                    and ou_val in (2.5, 2.75)):
                    sigs.append({
                        "type": "OVER",
                        "name": "🔥 SHOOTOUT",
                        "desc": "High box penetration vs leaky defenses."
                    })

                # ── RULE 3: STERILE MATCH (Under) ─────────────────────
                if (he["deep"] <= 5
                    and ae["deep"] <= 5
                    and he["xG"] < 1.10
                    and ae["xG"] < 1.10
                    and ou_val is not None
                    and ou_val >= 2.5):
                    sigs.append({
                        "type": "UNDER",
                        "name": "🧱 STERILE MATCH",
                        "desc": "Lack of box penetration from both sides."
                    })

                return sigs

            tactical_signals = _tactical_signals(
                home_stats, away_stats, ah_lines, ou_lines
            )

            results.append({
                "match": {
                    "id": str(match_id),
                    "home": home_team,
                    "away": away_team,
                    "league": league_name,
                    "date": match_dt.strftime("%Y-%m-%d") if match_dt else "",
                    "match_datetime": match_dt.isoformat() if match_dt else "",
                },
                "market_lines": {
                    "asian_handicap": ah_lines if ah_lines else None,
                    "over_under": ou_lines,
                },
                "home_engine": home_stats,
                "away_engine": away_stats,
                "mismatch_delta": {
                    "ppda": round(ppda_delta, 2),
                    "deep": deep_delta,
                },
                "tactical_signals": tactical_signals,
            })

        return {
            "matches": results,
            "meta": {
                "total": len(results),
                "generated_at": datetime.now().isoformat(),
            },
        }


# INCLUSIONE DI TUTTI I ROUTER ESTERNI
app.include_router(scraper_router)
app.include_router(meritometro_router, prefix="/api", tags=["meritometro"])
app.include_router(scout_router)
app.include_router(fanta_router)
app.include_router(team_metrics_router, prefix="/api/v1")
app.include_router(team_performance_router, prefix="/api/v1")
app.include_router(replacement_router)
app.include_router(nerdzone_router)
app.include_router(matches_preview_router, prefix="/api/v1")
app.include_router(betting_router, prefix="/api/v1")

@app.get("/health")
async def engine_health():
    return {
        "status": "Barsport Engine Online",
        "version": "35.5.12",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/admin/sync-goals")
async def sync_goals_from_understat(db: AsyncSession = Depends(get_db)):
    """Fetches goals from individual Understat match pages for all completed matches missing goals."""
    import aiohttp, json, re
    from sqlalchemy import text as sql_text

    SCRAPERAPI_KEY = "431f2fa400ff089e9941c13c7d275c42"

    # Get all completed matches without goals
    rows = (await db.execute(sql_text("""
        SELECT mc.id, l.name as league
        FROM matchcalendar mc
        JOIN league l ON mc.league_id = l.id
        WHERE mc.is_completed = TRUE AND mc.home_goals IS NULL
        ORDER BY mc.id
    """))).fetchall()

    if not rows:
        return {"status": "nothing_to_update", "count": 0}

    match_ids = [(r[0], r[1]) for r in rows]
    updated = 0
    errors = []

    async def fetch_match_goals(session: aiohttp.ClientSession, match_id: int):
        target = f"https://understat.com/match/{match_id}"
        url = f"http://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url={target}"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                html = await resp.text()
        except Exception as e:
            return None, str(e)
        # Try single-quote pattern
        m = re.search(r"var match_info\s*=\s*JSON\.parse\('(.+?)'\)", html, re.DOTALL)
        if not m:
            m = re.search(r'var match_info\s*=\s*JSON\.parse\("(.+?)"\)', html, re.DOTALL)
        if not m:
            return None, f"match_info not found (html_len={len(html)})"
        try:
            raw = m.group(1).encode().decode("unicode_escape")
            info = json.loads(raw)
            return info, None
        except Exception as e:
            return None, f"parse error: {e}"

    async with aiohttp.ClientSession() as http:
        # Process in batches of 5 to avoid overloading ScraperAPI
        batch_size = 5
        for i in range(0, len(match_ids), batch_size):
            batch = match_ids[i:i + batch_size]
            tasks = [fetch_match_goals(http, mid) for mid, _ in batch]
            results = await asyncio.gather(*tasks)

            for (mid, league), (info, err) in zip(batch, results):
                if err or not info:
                    errors.append({"id": mid, "error": err or "no data"})
                    continue
                try:
                    hg = int(info["h_goals"])
                    ag = int(info["a_goals"])
                    hxg = float(info.get("h_xg", 0))
                    axg = float(info.get("a_xg", 0))
                    await db.execute(sql_text("""
                        UPDATE matchcalendar
                        SET home_goals=:hg, away_goals=:ag,
                            "home_xG"=:hxg, "away_xG"=:axg, is_completed=true
                        WHERE id=:id
                    """), {"hg": hg, "ag": ag, "hxg": hxg, "axg": axg, "id": mid})
                    updated += 1
                except Exception as e:
                    errors.append({"id": mid, "error": str(e)})

            await db.commit()
            # Small delay between batches
            if i + batch_size < len(match_ids):
                await asyncio.sleep(1)

    return {
        "status": "done",
        "total": len(match_ids),
        "updated": updated,
        "errors": errors[:20],
    }

print("-> Barsport STATS V35.5: THE GREAT RECONSTRUCTION - COMPLETE - [EOF]")