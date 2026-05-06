"""
Quantitative Betting Evaluator — Orchestration Service
======================================================
Phase 5 final integration. Wires the value_engine mathematical core into
production by:

  1. Fetching match context from the DB (team IDs, names).
  2. Running the full Poisson λ → Score Matrix → Market Evaluation pipeline.
  3. Cost‑optimised AI risk assessment (only for markets with ev_base > 2 %).
  4. Strict filtering + ranking via filter_and_rank_picks.
  5. Data Tracking Loop — persists features + bets to PostgreSQL.
  6. Returning institution‑grade Top Picks.

All AI calls are dispatched asynchronously via asyncio.gather, respecting
the same DeepSeek → OpenAI fallback chain as the preview system.
"""

import asyncio
import json
import logging
import os
import difflib
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx
from openai import AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv

from app.core.config import settings
from app.services.ai_service import predict_ev_final
from app.services.tracking_service import log_bet, log_features
from app.services.value_engine import (
    build_ai_features,
    calculate_stability,
    compute_match_lambdas,
    derive_asian_handicap_prob,
    derive_standard_markets,
    evaluate_all_markets,
    filter_and_rank_picks,
    generate_ai_risk_prompt,
    generate_score_matrix,
)

load_dotenv()
logger = logging.getLogger(__name__)
# ---------------------------------------------------------------------------
# API Key Rotator Setup
# ---------------------------------------------------------------------------
RAW_KEYS = os.getenv("ODDS_API_KEYS", "").split(",")
ODDS_KEYS = [k.strip() for k in RAW_KEYS if k.strip()]
if not ODDS_KEYS:
    legacy_key = getattr(settings, "ODDS_API_KEY", None)
    if legacy_key:
        ODDS_KEYS = [legacy_key]

CURRENT_KEY_INDEX = 0

# ---------------------------------------------------------------------------
# API Key Rotator Setup
# ---------------------------------------------------------------------------
RAW_KEYS = os.getenv("ODDS_API_KEYS", "").split(",")
ODDS_KEYS = [k.strip() for k in RAW_KEYS if k.strip()]
if not ODDS_KEYS:
    legacy_key = getattr(settings, "ODDS_API_KEY", None)
    if legacy_key:
        ODDS_KEYS = [legacy_key]

CURRENT_KEY_INDEX = 0

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COST_OPTIMISATION_EV_THRESHOLD: float = 0.02
"""Only markets with ev_base > 2 % proceed to the AI risk model."""

AI_TIMEOUT_SECONDS: int = 30
"""Per‑market AI call timeout."""

MAX_CONCURRENT_AI_CALLS: int = 10
"""Semaphore limit to avoid flooding the AI provider."""

ODDS_LEAGUE_MAP: Dict[str, str] = {
    "Serie A":       "soccer_italy_serie_a",
    "Premier League":"soccer_epl",
    "La Liga":       "soccer_spain_la_liga",
    "Ligue 1":       "soccer_france_ligue_one",
    "Bundesliga":    "soccer_germany_bundesliga",
}
"""Maps internal league names to The-Odds-API sport keys."""


# ---------------------------------------------------------------------------
# Team name normalisation for fuzzy matching
# ---------------------------------------------------------------------------


def normalize_team_name(name: str) -> str:
    """Normalise a team name for fuzzy matching."""
    name = name.lower().strip()
    name = re.sub(r"[^\w\s]", " ", name)
    tokens = re.split(r"\s+", name)
    noise = {
        "fc", "ac", "as", "ss", "us", "ssc", "sc", "cf", "afc",
        "sv", "bayer", "borussia", "united", "wanderers",
        "city", "utd", "town", "county", "rover", "rovers",
    }
    filtered = [
        t for t in tokens
        if t and t not in noise and not t.isdigit()
    ]
    return "".join(filtered)


# ---------------------------------------------------------------------------
# Fetch match info from DB
# ---------------------------------------------------------------------------


async def _fetch_match_context(
    session: AsyncSession,
    match_id: int,
) -> Optional[Dict[str, Any]]:
    """Retrieve match header info (team ids, names, league) from matchcalendar."""
    query = text("""
        SELECT
            m.id,
            m.home_team_id,
            m.away_team_id,
            m.league_id,
            th.name AS home_team,
            ta.name AS away_team,
            l.name  AS league_name,
            m.match_datetime
        FROM matchcalendar m
        JOIN team  th ON m.home_team_id = th.id
        JOIN team  ta ON m.away_team_id = ta.id
        JOIN league l  ON m.league_id    = l.id
        WHERE m.id = :match_id
    """)
    row = (await session.execute(query, {"match_id": match_id})).fetchone()
    if not row:
        logger.warning("Match %s not found in DB", match_id)
        return None

    return {
        "match_id":      row[0],
        "home_team_id":  row[1],
        "away_team_id":  row[2],
        "league_id":     row[3],
        "home_team":     row[4],
        "away_team":     row[5],
        "league_name":   row[6],
        "match_datetime": row[7].isoformat() if row[7] else None,
    }


async def _fetch_real_odds_for_match(
    session: AsyncSession,
    match_ctx: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    global CURRENT_KEY_INDEX
    
    league_name = match_ctx.get("league_name", "")
    home_team   = match_ctx.get("home_team", "")
    away_team   = match_ctx.get("away_team", "")
    api_sport   = ODDS_LEAGUE_MAP.get(league_name)

    if not api_sport or not ODDS_KEYS:
        logger.error(f"CRITICAL FETCH FAILURE: api_sport={api_sport}, api_keys_present={bool(ODDS_KEYS)}")
        return None

    for _ in range(len(ODDS_KEYS)):
        api_key = ODDS_KEYS[CURRENT_KEY_INDEX]
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://api.the-odds-api.com/v4/sports/{api_sport}/odds/"
                params = {
                    "apiKey":     api_key,
                    "regions":    "eu",
                    "markets":    "h2h,totals",
                    "oddsFormat": "decimal",
                }
                resp = await client.get(url, params=params, timeout=8)
                
                # ROTATOR LOGIC
                if resp.status_code == 401 and "OUT_OF_USAGE_CREDITS" in resp.text:
                    logger.error(f"Key ending in ...{api_key[-4:]} exhausted. Rotating to next key.")
                    CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(ODDS_KEYS)
                    continue

                if resp.status_code != 200:
                    logger.error(f"CRITICAL FETCH FAILURE: Odds API returned {resp.status_code}. Response: {resp.text}")
                    return None

                data = resp.json()
                if not isinstance(data, list):
                    return None

                norm_db_home = normalize_team_name(home_team)
                norm_db_away = normalize_team_name(away_team)
                THRESHOLD = 0.4  # Abbassato brutalmente per evitare miss

                best_match_data = None
                for match in data:
                    api_home = match.get("home_team") or ""
                    api_away = match.get("away_team") or ""
                    norm_api_home = normalize_team_name(api_home)
                    norm_api_away = normalize_team_name(api_away)

                    # Substring check (molto più tollerante)
                    if (norm_db_home in norm_api_home or norm_api_home in norm_db_home) and \
                       (norm_db_away in norm_api_away or norm_api_away in norm_db_away):
                        best_match_data = match
                        break

                    # Swapped substring check
                    if (norm_db_home in norm_api_away or norm_api_away in norm_db_home) and \
                       (norm_db_away in norm_api_home or norm_api_home in norm_db_away):
                        best_match_data = match
                        break

                    # Difflib
                    sim_hh = difflib.SequenceMatcher(None, norm_db_home, norm_api_home).ratio()
                    sim_aa = difflib.SequenceMatcher(None, norm_db_away, norm_api_away).ratio()
                    sim_ha = difflib.SequenceMatcher(None, norm_db_home, norm_api_away).ratio()
                    sim_ah = difflib.SequenceMatcher(None, norm_db_away, norm_api_home).ratio()

                    if sim_hh > THRESHOLD and sim_aa > THRESHOLD:
                        best_match_data = match
                        break
                    if sim_ha > THRESHOLD and sim_ah > THRESHOLD:
                        best_match_data = match
                        break

                if best_match_data is None:
                    logger.error(f"CRITICAL FETCH FAILURE: Fuzzy match exhausted. Looked for '{home_team}' vs '{away_team}'.")
                    return None

                match = best_match_data

                for bookmaker in match.get("bookmakers", [])[:3]:
                    h2h_odds = None
                    ou_odds  = None
                    ou_line  = 2.5

                    for market in bookmaker.get("markets", []):
                        outcomes = market.get("outcomes", [])
                        if market["key"] == "h2h":
                            h2h_map: Dict[str, float] = {}
                            for o in outcomes:
                                name = o.get("name", "")
                                price = o.get("price", 2.0)
                                if name == match.get("home_team"):
                                    h2h_map["home"] = price
                                elif name == "Draw":
                                    h2h_map["draw"] = price
                                elif name == match.get("away_team"):
                                    h2h_map["away"] = price
                            if len(h2h_map) == 3:
                                h2h_odds = h2h_map
                        elif market["key"] == "totals":
                            for o in outcomes:
                                o_name = (o.get("name") or "").lower()
                                price  = o.get("price", 2.0)
                                point  = o.get("point", 2.5)
                                ou_line = float(point)
                                if "over" in o_name:
                                    ou_odds = {"line": ou_line, "over": price, "under": 2.0}
                                elif "under" in o_name and ou_odds:
                                    ou_odds["under"] = price

                    if not h2h_odds:
                        continue

                    real_odds: Dict[str, Any] = {
                        "1x2": h2h_odds,
                    }
                    if ou_odds:
                        real_odds["over_under"] = ou_odds

                    real_odds["btts"] = {"yes": 2.0, "no": 2.0}
                    return real_odds

                return None

        except Exception as e:
            logger.exception("Failed to fetch real odds for %s vs %s: %s", home_team, away_team, e)
            return None
            
    logger.error("ALL ODDS API KEYS EXHAUSTED OR FAILED.")
    return None


# ---------------------------------------------------------------------------
# AI call — messages format (reuses provider API keys from settings)
# ---------------------------------------------------------------------------


async def _call_ai_with_messages(
    messages: List[Dict[str, str]],
    timeout: int = AI_TIMEOUT_SECONDS,
) -> Optional[str]:
    deepseek_key = getattr(settings, "DEEPSEEK_API_KEY", None) or ""
    openai_key   = getattr(settings, "OPENAI_API_KEY", None) or ""

    if not deepseek_key and not openai_key:
        logger.error("AI call skipped: no API keys configured")
        return None

    if deepseek_key:
        try:
            client = AsyncOpenAI(
                api_key=deepseek_key,
                base_url="https://api.deepseek.com",
            )
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    temperature=0.3,
                    max_tokens=600,
                ),
                timeout=timeout,
            )
            content = response.choices[0].message.content.strip()
            if content:
                logger.debug("DeepSeek returned %d chars", len(content))
                return content
        except asyncio.TimeoutError:
            logger.warning("DeepSeek timed out after %ds", timeout)
        except Exception as exc:
            logger.warning("DeepSeek call failed: %s", exc)

    if openai_key:
        try:
            client = AsyncOpenAI(api_key=openai_key)
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.3,
                    max_tokens=600,
                ),
                timeout=timeout,
            )
            content = response.choices[0].message.content.strip()
            if content:
                logger.debug("OpenAI returned %d chars", len(content))
                return content
        except asyncio.TimeoutError:
            logger.warning("OpenAI timed out after %ds", timeout)
        except Exception as exc:
            logger.warning("OpenAI call failed: %s", exc)

    return None


# ---------------------------------------------------------------------------
# Parse AI JSON response
# ---------------------------------------------------------------------------


def _parse_ai_risk_response(raw: str) -> Optional[Dict[str, Any]]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        cleaned = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(cleaned).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if not match:
            logger.warning("No JSON block found in AI response")
            return None
        try:
            data = json.loads(match.group())
        except json.JSONDecodeError:
            logger.warning("Failed to parse extracted JSON block")
            return None

    ev_final = data.get("ev_final")
    confidence_score = data.get("confidence_score")
    reasoning = (data.get("reasoning") or "").strip()

    if ev_final is not None:
        ev_final = float(ev_final)
    if confidence_score is not None:
        confidence_score = int(max(1, min(100, float(confidence_score))))

    if ev_final is None or not reasoning:
        logger.warning("AI response missing required fields: ev_final=%s, reasoning=%s", ev_final, reasoning)
        return None

    return {
        "ev_final": round(ev_final, 6),
        "confidence_score": confidence_score or 50,
        "reasoning": reasoning[:400],
    }


# ---------------------------------------------------------------------------
# Per‑match pipeline
# ---------------------------------------------------------------------------


async def _evaluate_single_match(
    session: AsyncSession,
    match_ctx: Dict[str, Any],
    real_odds: Dict[str, Any],
    ai_semaphore: asyncio.Semaphore,
) -> List[Dict[str, Any]]:
    match_id     = match_ctx["match_id"]
    home_team    = match_ctx["home_team"]
    away_team    = match_ctx["away_team"]
    league_name  = match_ctx["league_name"]
    home_team_id = match_ctx["home_team_id"]
    away_team_id = match_ctx["away_team_id"]
    league_id    = match_ctx["league_id"]

    lambdas = await compute_match_lambdas(session, home_team_id, away_team_id, league_id)

    if lambdas.get("lambda_home") is None or lambdas.get("lambda_away") is None:
        logger.warning("Match %s: λ computation returned None — skipping", match_id)
        return []

    score_matrix = generate_score_matrix(
        lambdas["lambda_home"],
        lambdas["lambda_away"],
    )
    model_probs = derive_standard_markets(score_matrix)
    model_probs["_score_matrix"] = score_matrix

    all_evaluated = evaluate_all_markets(model_probs, real_odds)
    if not all_evaluated:
        logger.info("Match %s: no markets evaluated", match_id)
        return []

    survivors = []
    for market_key, market_data in all_evaluated.items():
        ev_base = market_data.get("ev_base")
        if ev_base is not None and ev_base > COST_OPTIMISATION_EV_THRESHOLD:
            market_data["market_key"] = market_key
            survivors.append(market_data)

    if not survivors:
        logger.info("Match %s: no markets above ev_base=%.4f", match_id, COST_OPTIMISATION_EV_THRESHOLD)
        return []

    home_rolling = lambdas.get("home_rolling", {})
    away_rolling = lambdas.get("away_rolling", {})

    home_xg_diff = home_rolling.get("xG_for", 0.0) - home_rolling.get("xG_against", 0.0)
    away_xg_diff = away_rolling.get("xG_for", 0.0) - away_rolling.get("xG_against", 0.0)

    xg_diff_array_home = [home_xg_diff]
    xg_diff_array_away = [away_xg_diff]

    matches_h = home_rolling.get("matches_used", 0)
    matches_a = away_rolling.get("matches_used", 0)
    if matches_h >= 2:
        xg_diff_array_home = [home_xg_diff * 0.8, home_xg_diff * 1.2]
    if matches_a >= 2:
        xg_diff_array_away = [away_xg_diff * 0.8, away_xg_diff * 1.2]

    stab_h = calculate_stability(xg_diff_array_home)
    stab_a = calculate_stability(xg_diff_array_away)

    match_lambda_ctx = {
        "lambda_home": lambdas.get("lambda_home", 0.0),
        "lambda_away": lambdas.get("lambda_away", 0.0),
    }

    ai_ready_markets = []
    for market_data in survivors:
        mk = market_data["market_key"]
        if "over" in mk or "under" in mk:
            market_data["_market_type"] = "over_under"
        elif "btts" in mk:
            market_data["_market_type"] = "btts"
        elif "ah_" in mk:
            market_data["_market_type"] = "asian_handicap"
        elif "1x2" in mk or "home" in mk or "draw" in mk or "away" in mk:
            market_data["_market_type"] = "1x2"
        else:
            market_data["_market_type"] = "unknown"

        features = build_ai_features(match_lambda_ctx, market_data, stab_h, stab_a)

        home_xg_diff = lambdas.get("home_strength", {}).get("xG_diff", 0.0)
        away_xg_diff = lambdas.get("away_strength", {}).get("xG_diff", 0.0)
        features["team_strength_home"] = round(home_xg_diff, 4)
        features["team_strength_away"] = round(away_xg_diff, 4)

        prompt_messages = generate_ai_risk_prompt(features)

        market_data["features"] = features
        market_data["prompt_messages"] = prompt_messages
        market_data["match_id"] = match_id
        market_data["home_team"] = home_team
        market_data["away_team"] = away_team
        market_data["league_name"] = league_name
        market_data["match_datetime"] = match_ctx["match_datetime"]

        ai_ready_markets.append(market_data)

    async def _call_ai(market: Dict[str, Any]) -> Dict[str, Any]:
        async with ai_semaphore:
            features = market.get("features", {})
            features_dict = {
                "lambda_home":        features.get("lam_home"),
                "lambda_away":        features.get("lam_away"),
                "p_model":            features.get("p_model"),
                "p_book":             features.get("p_book"),
                "ev_base":            features.get("ev_base"),
                "team_strength_home": features.get("team_strength_home"),
                "team_strength_away": features.get("team_strength_away"),
                "stability_home":     features.get("stability_home"),
                "stability_away":     features.get("stability_away"),
                "odds":               features.get("odds"),
            }

            ev_final = predict_ev_final(features_dict)

            market["ev_final"] = ev_final
            market["confidence_score"] = 50
            market["ai_reasoning"] = (
                "ML model prediction (Phase 8)."
            )

            market.pop("prompt_messages", None)
            return market

    results = await asyncio.gather(*[_call_ai(m) for m in ai_ready_markets])

    MAX_INSTITUTIONAL_EV: float = 0.35
    filtered: List[Dict[str, Any]] = []
    for market in results:
        ev = market.get("ev_final")
        if ev is not None and ev > MAX_INSTITUTIONAL_EV:
            logger.warning(
                "EV sanity clamp: dropping %s (ev_final=%.4f exceeds %.2f)",
                market.get("market_key", "unknown"), ev, MAX_INSTITUTIONAL_EV,
            )
            continue
        filtered.append(market)

    return filtered


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def evaluate_picks_batch(
    session: AsyncSession,
    matches_data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    ai_semaphore = asyncio.Semaphore(MAX_CONCURRENT_AI_CALLS)

    all_ai_markets: List[Dict[str, Any]] = []
    matches_processed = 0

    for entry in matches_data:
        match_id   = entry["match_id"]
        real_odds  = entry.get("real_odds", {})

        match_ctx = await _fetch_match_context(session, match_id)
        if not match_ctx:
            logger.warning("Skipping match_id=%s: not found in DB", match_id)
            continue

        if not real_odds:
            logger.info("Skipping match_id=%s: no real_odds provided", match_id)
            continue

        try:
            match_results = await _evaluate_single_match(
                session, match_ctx, real_odds, ai_semaphore,
            )
            all_ai_markets.extend(match_results)
            matches_processed += 1
        except Exception:
            logger.exception("Failed to evaluate match_id=%s", match_id)

    top_picks = filter_and_rank_picks(all_ai_markets, max_results=5)

    for pick in top_picks:
        mk = pick.get("market_key", "")
        pick["market_label"] = _infer_market_label(mk)

    for pick in top_picks:
        pick_features = pick.get("features", {})
        match_id   = pick.get("match_id", 0)
        market_key = pick.get("market_key", "")
        odds       = pick.get("odds", 0.0) or 0.0
        p_model    = pick.get("p_model", 0.0) or 0.0
        ev_final   = pick.get("ev_final", 0.0) or 0.0
        stake_frac = pick.get("recommended_stake_fraction", 0.0) or 0.0

        try:
            tracking_features = {
                "lambda_home":        pick_features.get("lam_home"),
                "lambda_away":        pick_features.get("lam_away"),
                "p_model":            pick_features.get("p_model"),
                "p_book":             pick_features.get("p_book"),
                "ev_base":            pick_features.get("ev_base"),
                "team_strength_home": pick_features.get("team_strength_home"),
                "team_strength_away": pick_features.get("team_strength_away"),
                "stability_home":     pick_features.get("stability_home"),
                "stability_away":     pick_features.get("stability_away"),
                "odds":               pick_features.get("odds"),
            }
            await log_features(
                session=session,
                match_id=match_id,
                market_key=market_key,
                features=tracking_features,
            )
        except Exception:
            logger.exception(
                "DataTracking: log_features failed for match_id=%s market=%s — pipeline continues",
                match_id, market_key,
            )

        try:
            await log_bet(
                session=session,
                match_id=match_id,
                market_key=market_key,
                odds=odds,
                p_model=p_model,
                ev_final=ev_final,
                recommended_stake_fraction=stake_frac,
            )
        except Exception:
            logger.exception(
                "DataTracking: log_bet failed for match_id=%s market=%s — pipeline continues",
                match_id, market_key,
            )

    return {
        "top_picks": top_picks,
        "total_evaluated": len(all_ai_markets),
        "matches_processed": matches_processed,
    }


# ---------------------------------------------------------------------------
# Convenience — GET endpoint helper
# ---------------------------------------------------------------------------


async def evaluate_value_bets(
    session: AsyncSession,
    match_ids: List[int],
) -> Dict[str, Any]:
    matches_data: List[Dict[str, Any]] = []
    for mid in match_ids:
        match_ctx = await _fetch_match_context(session, mid)
        if match_ctx:
            real_odds = await _fetch_real_odds_for_match(session, match_ctx)
            
            logger.error(f"🚨 VALORE REAL_ODDS RICEVUTO PER {match_ctx.get('home_team')}: {real_odds}")

            if not real_odds:
                logger.warning(f"Nessuna quota abbinata per il match {mid}. Match ignorato per evitare dati fittizi.")
                continue # SALTA IL MATCH, NIENTE QUOTE FINTE

            matches_data.append({
                "match_id": mid,
                "real_odds": real_odds,
            })

    if not matches_data:
        logger.warning("evaluate_value_bets: no valid match_ids provided")
        return {"top_picks": [], "total_evaluated": 0, "matches_processed": 0}

    return await evaluate_picks_batch(session=session, matches_data=matches_data)


# ---------------------------------------------------------------------------
# Lab 1 — Raw Analytics (no filters, no AI, full market delta)
# ---------------------------------------------------------------------------


async def evaluate_lab1_analytics(
    session: AsyncSession,
    match_ids: List[int],
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    for mid in match_ids:
        match_ctx = await _fetch_match_context(session, mid)
        if not match_ctx:
            logger.warning("evaluate_lab1_analytics: match_id=%s not found", mid)
            continue

        match_id     = match_ctx["match_id"]
        home_team    = match_ctx["home_team"]
        away_team    = match_ctx["away_team"]
        match_name   = f"{home_team} vs {away_team}"
        home_team_id = match_ctx["home_team_id"]
        away_team_id = match_ctx["away_team_id"]
        league_id    = match_ctx["league_id"]

        lambdas = await compute_match_lambdas(session, home_team_id, away_team_id, league_id)
        if lambdas.get("lambda_home") is None or lambdas.get("lambda_away") is None:
            logger.warning("Lab1 match %s: λ computation returned None — skipping", match_id)
            continue

        score_matrix = generate_score_matrix(
            lambdas["lambda_home"],
            lambdas["lambda_away"],
        )
        model_probs = derive_standard_markets(score_matrix)
        model_probs["_score_matrix"] = score_matrix

        real_odds = await _fetch_real_odds_for_match(session, match_ctx)
        if not real_odds:
            logger.info(
                "Lab1 match %s: no real odds found — returning model-only data with null bookmaker fields",
                match_id,
            )
            model_only: List[Dict[str, Any]] = [
                {"match_name": match_name, "match_id": match_id, "market_key": "1x2_home",  "market_label": "1X2 Home Win",     "odds": None, "p_book": None, "p_model": model_probs.get("home_win"),  "diff": None, "ev_base": None},
                {"match_name": match_name, "match_id": match_id, "market_key": "1x2_draw",  "market_label": "1X2 Draw",         "odds": None, "p_book": None, "p_model": model_probs.get("draw"),      "diff": None, "ev_base": None},
                {"match_name": match_name, "match_id": match_id, "market_key": "1x2_away",  "market_label": "1X2 Away Win",     "odds": None, "p_book": None, "p_model": model_probs.get("away_win"),  "diff": None, "ev_base": None},
                {"match_name": match_name, "match_id": match_id, "market_key": "over_2.5",  "market_label": "Over 2.5 Goals",   "odds": None, "p_book": None, "p_model": model_probs.get("over_2_5"),  "diff": None, "ev_base": None},
                {"match_name": match_name, "match_id": match_id, "market_key": "under_2.5", "market_label": "Under 2.5 Goals",  "odds": None, "p_book": None, "p_model": model_probs.get("under_2_5"), "diff": None, "ev_base": None},
                {"match_name": match_name, "match_id": match_id, "market_key": "btts_yes",  "market_label": "Both Teams to Score (Yes)", "odds": None, "p_book": None, "p_model": model_probs.get("btts_yes"), "diff": None, "ev_base": None},
                {"match_name": match_name, "match_id": match_id, "market_key": "btts_no",   "market_label": "Both Teams to Score (No)",  "odds": None, "p_book": None, "p_model": model_probs.get("btts_no"),  "diff": None, "ev_base": None},
            ]
            results.extend(model_only)
            continue

        all_evaluated = evaluate_all_markets(model_probs, real_odds)
        if not all_evaluated:
            continue

        for market_key, market_data in all_evaluated.items():
            if market_key == "_score_matrix":
                continue

            results.append({
                "match_name":   match_name,
                "match_id":     match_id,
                "market_key":   market_key,
                "market_label": _infer_market_label(market_key),
                "odds":         market_data.get("odds"),
                "p_book":       market_data.get("p_book"),
                "p_model":      market_data.get("p_model"),
                "diff":         market_data.get("diff"),
                "ev_base":      market_data.get("ev_base"),
            })

    return results


# ---------------------------------------------------------------------------
# Market label helper
# ---------------------------------------------------------------------------


def _infer_market_label(market_key: str) -> str:
    """Map a market_key to a human‑readable label."""
    mk = market_key.lower()
    if mk.startswith("over_"):
        try:
            line = mk.replace("over_", "")
            return f"Over {line} Goals"
        except (ValueError, TypeError):
            return "Over"
    if mk.startswith("under_"):
        try:
            line = mk.replace("under_", "")
            return f"Under {line} Goals"
        except (ValueError, TypeError):
            return "Under"
    if mk == "btts_yes":
        return "Both Teams to Score (Yes)"
    if mk == "btts_no":
        return "Both Teams to Score (No)"
    if mk.startswith("ah_"):
        parts = mk.replace("ah_", "").rsplit("_", 1)
        if len(parts) == 2:
            return f"Asian Handicap {parts[0]} ({parts[1].upper()})"
        return f"Asian Handicap ({mk})"
    if mk == "1x2_home":
        return "1X2 Home Win"
    if mk == "1x2_draw":
        return "1X2 Draw"
    if mk == "1x2_away":
        return "1X2 Away Win"
    return market_key


# ---------------------------------------------------------------------------
# Lab 2 — Single-match Matrix (λ, score grid, Asian Handicap split)
# ---------------------------------------------------------------------------


async def compute_lab2_matrix(
    session: AsyncSession,
    match_id: int,
) -> Optional[Dict[str, Any]]:
    match_ctx = await _fetch_match_context(session, match_id)
    if not match_ctx:
        logger.warning("compute_lab2_matrix: match_id=%s not found", match_id)
        return None

    home_team    = match_ctx["home_team"]
    away_team    = match_ctx["away_team"]
    home_team_id = match_ctx["home_team_id"]
    away_team_id = match_ctx["away_team_id"]
    league_id    = match_ctx["league_id"]

    lambdas = await compute_match_lambdas(session, home_team_id, away_team_id, league_id)
    if lambdas.get("lambda_home") is None or lambdas.get("lambda_away") is None:
        logger.warning("compute_lab2_matrix: λ computation returned None for match_id=%s", match_id)
        return None

    lambda_home: float = lambdas["lambda_home"]
    lambda_away: float = lambdas["lambda_away"]

    score_dict = generate_score_matrix(lambda_home, lambda_away, max_goals=5)

    matrix_raw: Dict[Tuple[int, int], float] = score_dict["matrix"]
    P_diff: Dict[int, float] = score_dict["P_diff"]

    score_grid: List[List[float]] = []
    for h in range(6):
        row: List[float] = []
        for a in range(6):
            row.append(matrix_raw.get((h, a), 0.0))
        score_grid.append(row)

    line_quarter = -0.75
    line_full    = -0.5   
    line_half    = -1.0   

    def _resolve_single_line(line: float) -> Dict[str, Any]:
        eps = 1e-9
        P_win = P_push = P_loss = 0.0
        for d, prob in P_diff.items():
            adj = d + line
            if adj > eps:
                P_win += prob
            elif abs(adj) <= eps:
                P_push += prob
            else:
                P_loss += prob
        return {
            "line":   line,
            "P_win":  round(P_win, 6),
            "P_push": round(P_push, 6),
            "P_loss": round(P_loss, 6),
        }

    full_comp = _resolve_single_line(line_full)
    half_comp = _resolve_single_line(line_half)

    combined_ev = round(0.5 * full_comp["P_win"] + 0.5 * half_comp["P_win"], 6)

    return {
        "home_team":                home_team,
        "away_team":                away_team,
        "lambda_home":              lambda_home,
        "lambda_away":              lambda_away,
        "score_matrix":             score_grid,
        "asian_handicap_breakdown": {
            "line":               line_quarter,
            "full_win_component": full_comp,
            "half_component":     half_comp,
            "combined_ev":        combined_ev,
        },
    }