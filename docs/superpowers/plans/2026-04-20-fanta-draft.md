# Fanta Draft Engine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Completare il Fanta Draft Engine — backend con 3 endpoint reali + frontend Next.js coerente con barsport.club.

**Architecture:** Backend FastAPI in `fanta_routes.py` con query async su PostgreSQL via SQLAlchemy engine. Frontend Next.js con Tailwind, Framer Motion, Recharts. Nessuna nuova dipendenza richiesta.

**Tech Stack:** Python/FastAPI, SQLAlchemy async, PostgreSQL, Next.js 14, TypeScript, Tailwind CSS, Recharts, Framer Motion, Lucide React.

---

## File Map

| File | Azione |
|---|---|
| `backend/app/api/fanta_routes.py` | Modifica — aggiungere search, completare dashboard, auction-strategy, TAI reale |
| `frontend/app/fanta-draft/page.tsx` | Crea — pagina completa |

---

## Task 1 — Backend: Search endpoint + TAI reale

**Files:**
- Modify: `backend/app/api/fanta_routes.py`

- [ ] **Step 1: Aggiungere `get_team_attack_index()` async e search endpoint**

Sostituire la funzione `classify_team_attack` e aggiungere il search endpoint. Aprire `backend/app/api/fanta_routes.py` e applicare queste modifiche:

**Sostituire** la funzione `classify_team_attack` (righe 66-70) con:

```python
async def get_team_attack_index(conn, team_name: str) -> float:
    """TAI reale: media xG/partita della squadra. 1.2 top, 1.0 medio, 0.8 basso."""
    if not team_name:
        return 1.0
    result = await conn.execute(text("""
        SELECT AVG(CASE WHEN th.name = :t THEN mc."home_xG" ELSE mc."away_xG" END) as avg_xg
        FROM matchcalendar mc
        JOIN team th ON mc.home_team_id = th.id
        JOIN team ta ON mc.away_team_id = ta.id
        WHERE (th.name = :t OR ta.name = :t)
          AND mc.is_completed = true
          AND mc."home_xG" IS NOT NULL
    """), {"t": team_name})
    row = result.fetchone()
    avg_xg = float(row[0]) if row and row[0] else 1.0
    if avg_xg >= 1.5:
        return 1.2
    elif avg_xg >= 1.0:
        return 1.0
    else:
        return 0.8
```

**Aggiungere** nuovo endpoint dopo la definizione del router (dopo la riga `router = APIRouter(...)`):

```python
@router.get("/search")
async def search_fanta_players(q: str = Query(..., min_length=2)):
    """Cerca giocatori per nome, ritorna nome + player_id + posizione."""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT player, MIN(player_id) as player_id, MAX(position) as position
                FROM rosters
                WHERE player ILIKE :q
                GROUP BY player
                ORDER BY player
                LIMIT 10
            """), {"q": f"%{q}%"})
            rows = result.mappings().all()
            return [{"player": r["player"], "player_id": str(r["player_id"]), "position": r["position"] or "N/D"} for r in rows]
    except Exception as e:
        logger.error(f"Fanta search error: {e}")
        return []
```

- [ ] **Step 2: Verificare avvio backend**

```bash
cd "C:\Users\euron\Desktop\claude of control\backend"
python -c "from app.api.fanta_routes import router; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Testare manualmente search**

Con il backend avviato su porta 8000:
```
GET http://localhost:8000/api/fanta/search?q=Lautaro
```
Expected: lista JSON `[{"player": "Lautaro Martinez", "player_id": "...", "position": "FW"}, ...]`

---

## Task 2 — Backend: Dashboard con dati reali

**Files:**
- Modify: `backend/app/api/fanta_routes.py`

- [ ] **Step 1: Aggiungere helper `compute_max_bid_percentage` con max_value dinamico**

**Sostituire** la funzione `compute_max_bid_percentage` (righe 81-91) con:

```python
def compute_max_bid_percentage(value_score: float, max_value: float = 100.0, total_budget: float = 500) -> float:
    """Calcola % max budget. max_value è il massimo dinamico della lega."""
    if max_value == 0:
        return 0.0
    proportion = value_score / max_value
    return min(proportion * 20, 20.0)
```

- [ ] **Step 2: Implementare `/api/fanta/dashboard`**

**Sostituire** l'endpoint `get_fanta_dashboard` (righe 120-136) con:

```python
@router.get("/dashboard")
async def get_fanta_dashboard():
    """4 widget: Best Value, Breakout Candidates, Toxic Assets, Safe Picks."""
    try:
        async with engine.connect() as conn:
            # Aggregazione per (player, season) — ultimi 3 anni, min 200 min
            result = await conn.execute(text("""
                SELECT
                    r.player,
                    MIN(r.player_id)::text AS player_id,
                    MAX(r.position) AS position,
                    EXTRACT(YEAR FROM mc.match_datetime)::int AS season,
                    SUM(r.goals)   AS goals,
                    SUM(r.assists) AS assists,
                    SUM(r."xG")    AS xg,
                    SUM(r."xA")    AS xa,
                    SUM(r.shots)   AS shots,
                    SUM(r.time)    AS minutes,
                    MAX(t.name)    AS team_name
                FROM rosters r
                JOIN matchcalendar mc ON mc.id = r.match_id
                JOIN team t ON (
                    CASE WHEN r.team_type = 'h' THEN mc.home_team_id ELSE mc.away_team_id END
                ) = t.id
                WHERE EXTRACT(YEAR FROM mc.match_datetime) >= EXTRACT(YEAR FROM NOW()) - 3
                GROUP BY r.player, EXTRACT(YEAR FROM mc.match_datetime)
                HAVING SUM(r.time) > 200
                ORDER BY r.player, season DESC
            """))
            rows = result.mappings().all()

        # Raggruppa per giocatore
        players_map: dict = {}
        for row in rows:
            name = row["player"]
            if name not in players_map:
                players_map[name] = {
                    "player_id": row["player_id"],
                    "position": row["position"] or "N/D",
                    "seasons": []
                }
            players_map[name]["seasons"].append({
                "season": row["season"],
                "goals":   int(row["goals"] or 0),
                "assists": int(row["assists"] or 0),
                "xg":      float(row["xg"] or 0),
                "xa":      float(row["xa"] or 0),
                "shots":   int(row["shots"] or 0),
                "minutes": int(row["minutes"] or 0),
                "team_name": row["team_name"] or "",
            })

        # Calcola metriche per ogni giocatore
        all_profiles = []
        for name, data in players_map.items():
            seasons = data["seasons"]
            weighted = compute_weighted_xg_xa(seasons)
            breakout = compute_breakout_score(seasons)
            value = compute_value_score(weighted["weighted_xg"], weighted["weighted_xa"], data["position"])
            labels = generate_labels(seasons)
            all_profiles.append({
                "player":             name,
                "player_id":          data["player_id"],
                "position":           data["position"],
                "team":               seasons[0]["team_name"] if seasons else "",
                "weighted_xg":        round(weighted["weighted_xg"], 2),
                "weighted_xa":        round(weighted["weighted_xa"], 2),
                "breakout_multiplier":round(breakout, 2),
                "value_score":        round(value, 1),
                "labels":             labels,
                "latest_xg":          seasons[0]["xg"] if seasons else 0,
                "latest_goals":       seasons[0]["goals"] if seasons else 0,
            })

        if not all_profiles:
            return {"best_value_picks": [], "breakout_candidates": [], "toxic_assets": [], "safe_picks": []}

        max_vs = max(p["value_score"] for p in all_profiles) or 1.0
        for p in all_profiles:
            p["max_bid_pct"] = round(compute_max_bid_percentage(p["value_score"], max_vs), 1)

        # Categorizzazione
        best_value = sorted(
            [p for p in all_profiles if "Undervalued Finisher" in p["labels"]],
            key=lambda x: x["value_score"], reverse=True
        )[:8]

        breakout = sorted(
            [p for p in all_profiles if p["breakout_multiplier"] > 1.15],
            key=lambda x: x["breakout_multiplier"], reverse=True
        )[:8]

        toxic = sorted(
            [p for p in all_profiles if "Overperformer - Risky" in p["labels"]],
            key=lambda x: (x["latest_goals"] - x["latest_xg"]), reverse=True
        )[:8]

        safe = sorted(
            [p for p in all_profiles if "Safe Pick" in p["labels"]],
            key=lambda x: x["value_score"], reverse=True
        )[:8]

        return {
            "best_value_picks":    best_value,
            "breakout_candidates": breakout,
            "toxic_assets":        toxic,
            "safe_picks":          safe,
        }

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 3: Testare dashboard**

```
GET http://localhost:8000/api/fanta/dashboard
```
Expected: JSON con 4 liste non vuote (se il DB ha dati rosters).

---

## Task 3 — Backend: Auction Strategy reale

**Files:**
- Modify: `backend/app/api/fanta_routes.py`

- [ ] **Step 1: Implementare `/api/fanta/auction-strategy`**

**Sostituire** l'endpoint `get_auction_strategy` (righe 195-207) con:

```python
ROLE_BUDGET_SPLIT = {"GK": 0.05, "DF": 0.25, "MF": 0.35, "FW": 0.35}
POSITION_MAP = {"GK": "GK", "DF": "DF", "MF": "MF", "FW": "FW", "AM": "MF", "SS": "FW"}

@router.get("/auction-strategy")
async def get_auction_strategy(
    budget: float = Query(500, description="Budget totale in crediti"),
    participants: int = Query(8, description="Numero partecipanti all'asta")
):
    """Top target per l'asta con prezzo max calcolato su TAI reale."""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT
                    r.player,
                    MIN(r.player_id)::text AS player_id,
                    MAX(r.position) AS position,
                    EXTRACT(YEAR FROM mc.match_datetime)::int AS season,
                    SUM(r.goals)   AS goals,
                    SUM(r.assists) AS assists,
                    SUM(r."xG")    AS xg,
                    SUM(r."xA")    AS xa,
                    SUM(r.shots)   AS shots,
                    SUM(r.time)    AS minutes,
                    MAX(t.name)    AS team_name
                FROM rosters r
                JOIN matchcalendar mc ON mc.id = r.match_id
                JOIN team t ON (
                    CASE WHEN r.team_type = 'h' THEN mc.home_team_id ELSE mc.away_team_id END
                ) = t.id
                WHERE EXTRACT(YEAR FROM mc.match_datetime) >= EXTRACT(YEAR FROM NOW()) - 3
                GROUP BY r.player, EXTRACT(YEAR FROM mc.match_datetime)
                HAVING SUM(r.time) > 300
                ORDER BY r.player, season DESC
            """))
            rows = result.mappings().all()

            # TAI per ogni team (fetch una volta sola)
            tai_result = await conn.execute(text("""
                SELECT t.name,
                    AVG(CASE WHEN mc.home_team_id = t.id THEN mc."home_xG" ELSE mc."away_xG" END) as avg_xg
                FROM team t
                JOIN matchcalendar mc ON (mc.home_team_id = t.id OR mc.away_team_id = t.id)
                WHERE mc.is_completed = true AND mc."home_xG" IS NOT NULL
                GROUP BY t.name
            """))
            tai_map = {}
            for r in tai_result.fetchall():
                avg = float(r[1]) if r[1] else 1.0
                tai_map[r[0]] = 1.2 if avg >= 1.5 else (0.8 if avg < 1.0 else 1.0)

        # Raggruppa per giocatore
        players_map: dict = {}
        for row in rows:
            name = row["player"]
            if name not in players_map:
                players_map[name] = {
                    "player_id": row["player_id"],
                    "position": row["position"] or "N/D",
                    "seasons": []
                }
            players_map[name]["seasons"].append({
                "season": row["season"],
                "goals":   int(row["goals"] or 0),
                "assists": int(row["assists"] or 0),
                "xg":      float(row["xg"] or 0),
                "xa":      float(row["xa"] or 0),
                "shots":   int(row["shots"] or 0),
                "minutes": int(row["minutes"] or 0),
                "team_name": row["team_name"] or "",
            })

        all_profiles = []
        for name, data in players_map.items():
            seasons = data["seasons"]
            weighted = compute_weighted_xg_xa(seasons)
            team = seasons[0]["team_name"] if seasons else ""
            tai = tai_map.get(team, 1.0)
            value = compute_value_score(weighted["weighted_xg"], weighted["weighted_xa"], data["position"]) * tai
            all_profiles.append({
                "player":   name,
                "player_id": data["player_id"],
                "position": POSITION_MAP.get(data["position"], data["position"]),
                "team":     team,
                "tai":      tai,
                "value_score": round(value, 1),
            })

        if not all_profiles:
            return {"budget": budget, "participants": participants, "targets": []}

        max_vs = max(p["value_score"] for p in all_profiles) or 1.0

        # Seleziona top per ruolo
        targets = []
        counts = {"GK": 1, "DF": 3, "MF": 4, "FW": 3}
        for role, n in counts.items():
            role_players = sorted(
                [p for p in all_profiles if POSITION_MAP.get(p["position"], p["position"]) == role],
                key=lambda x: x["value_score"], reverse=True
            )[:n]
            role_budget = budget * ROLE_BUDGET_SPLIT.get(role, 0.25)
            for i, p in enumerate(role_players):
                pct = compute_max_bid_percentage(p["value_score"], max_vs)
                max_price = round(budget * (pct / 100), 0)
                targets.append({
                    "name":             p["player"],
                    "player_id":        p["player_id"],
                    "position":         p["position"],
                    "team":             p["team"],
                    "tai":              p["tai"],
                    "value_score":      p["value_score"],
                    "max_price":        max_price,
                    "budget_percentage": round(pct, 1),
                })

        targets.sort(key=lambda x: x["value_score"], reverse=True)
        return {"budget": budget, "participants": participants, "targets": targets}

    except Exception as e:
        logger.error(f"Auction strategy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 2: Aggiornare `get_fanta_player_profile` per usare TAI reale**

Nel metodo `get_fanta_player_profile`, **sostituire** la riga:
```python
tai = classify_team_attack(season_stats[0].get("team_name", ""), season_stats[0]["season"])
```
con:
```python
tai = await get_team_attack_index(conn, season_stats[0].get("team_name", ""))
```

E aggiornare `compute_max_bid_percentage` nell'endpoint per passare max dinamico:
```python
max_bid_pct = compute_max_bid_percentage(value_score, max_value=100.0)
```
(invariato — per il profilo singolo 100 è accettabile come riferimento)

- [ ] **Step 3: Commit backend**

```bash
cd "C:\Users\euron\Desktop\claude of control"
git add backend/app/api/fanta_routes.py
git commit -m "feat(fanta): complete dashboard, search, auction-strategy, real TAI"
```

---

## Task 4 — Frontend: `fanta-draft/page.tsx`

**Files:**
- Create: `frontend/app/fanta-draft/page.tsx`

- [ ] **Step 1: Creare il file con tipi e costanti**

Creare `frontend/app/fanta-draft/page.tsx` con il seguente contenuto completo:

```tsx
"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  TrendingUp, TrendingDown, Shield, Zap, Search, Target,
  DollarSign, Users, ChevronRight, Loader2, AlertTriangle, Star
} from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer
} from "recharts";

const API = "http://localhost:8000/api/fanta";

// ─── TYPES ───────────────────────────────────────────────────────────────────

type DashboardPlayer = {
  player: string;
  player_id: string;
  position: string;
  team: string;
  weighted_xg: number;
  weighted_xa: number;
  breakout_multiplier: number;
  value_score: number;
  max_bid_pct: number;
  labels: string[];
  latest_xg: number;
  latest_goals: number;
};

type DashboardData = {
  best_value_picks: DashboardPlayer[];
  breakout_candidates: DashboardPlayer[];
  toxic_assets: DashboardPlayer[];
  safe_picks: DashboardPlayer[];
};

type SearchResult = {
  player: string;
  player_id: string;
  position: string;
};

type SeasonStat = {
  season: number;
  goals: number;
  assists: number;
  xg: number;
  xa: number;
  shots: number;
  minutes: number;
  team_name: string;
};

type PlayerProfile = {
  player_id: string;
  season_stats: SeasonStat[];
  weighted_xg: number;
  weighted_xa: number;
  breakout_multiplier: number;
  team_attack_index: number;
  value_score: number;
  max_bid_percentage: number;
  labels: string[];
};

type AuctionTarget = {
  name: string;
  player_id: string;
  position: string;
  team: string;
  tai: number;
  value_score: number;
  max_price: number;
  budget_percentage: number;
};

// ─── HELPERS ─────────────────────────────────────────────────────────────────

const LABEL_COLORS: Record<string, string> = {
  "Undervalued Finisher": "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  "Overperformer - Risky": "bg-red-500/20 text-red-400 border-red-500/30",
  "Volume Striker": "bg-amber-500/20 text-amber-400 border-amber-500/30",
  "Safe Pick": "bg-sky-500/20 text-sky-400 border-sky-500/30",
};

function LabelBadge({ label }: { label: string }) {
  const cls = LABEL_COLORS[label] ?? "bg-slate-500/20 text-slate-400 border-slate-500/30";
  return (
    <span className={`text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded border ${cls}`}>
      {label}
    </span>
  );
}

function MetricPill({ label, value, accent = false }: { label: string; value: string | number; accent?: boolean }) {
  return (
    <div className="flex flex-col items-center bg-slate-800/50 rounded-xl p-3 border border-slate-700/50">
      <span className={`text-xl font-black ${accent ? "text-[#FF2A6D]" : "text-white"}`}>{value}</span>
      <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest mt-0.5">{label}</span>
    </div>
  );
}

// ─── WIDGET CARD ─────────────────────────────────────────────────────────────

type WidgetConfig = {
  title: string;
  badge: string;
  badgeColor: string;
  icon: React.ReactNode;
  emptyText: string;
  players: DashboardPlayer[];
  onSelect: (p: DashboardPlayer) => void;
};

function WidgetCard({ title, badge, badgeColor, icon, emptyText, players, onSelect }: WidgetConfig) {
  return (
    <div className="bg-white rounded-[28px] shadow-sm border border-slate-100 overflow-hidden hover:-translate-y-1 transition-transform duration-300">
      <div className="bg-[#0A192F] px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-[#FF2A6D]">{icon}</span>
          <span className="text-xs font-black text-white uppercase tracking-widest">{title}</span>
        </div>
        <span className={`text-[9px] font-black uppercase tracking-widest px-3 py-1 rounded-full border ${badgeColor}`}>
          {badge}
        </span>
      </div>
      <div className="p-4">
        {players.length === 0 ? (
          <p className="text-xs text-slate-400 text-center py-6 font-bold uppercase tracking-widest">{emptyText}</p>
        ) : (
          <ul className="space-y-1">
            {players.map((p) => (
              <li
                key={p.player}
                onClick={() => onSelect(p)}
                className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-50 cursor-pointer transition-colors group"
              >
                <div className="flex-1 min-w-0">
                  <p className="font-black text-sm text-[#0A192F] truncate group-hover:text-[#FF2A6D] transition-colors">
                    {p.player}
                  </p>
                  <p className="text-[9px] text-slate-400 font-bold uppercase tracking-widest">
                    {p.position} · {p.team}
                  </p>
                </div>
                <div className="flex items-center gap-3 ml-2 flex-shrink-0">
                  <div className="text-right">
                    <div className="text-sm font-black text-[#FF2A6D]">{p.value_score}</div>
                    <div className="text-[8px] text-slate-400 uppercase tracking-widest">pts</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-black text-[#0A192F]">{p.max_bid_pct}%</div>
                    <div className="text-[8px] text-slate-400 uppercase tracking-widest">bid</div>
                  </div>
                  <ChevronRight size={12} className="text-slate-300 group-hover:text-[#FF2A6D] transition-colors" />
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

// ─── PLAYER PROFILE PANEL ────────────────────────────────────────────────────

function PlayerProfilePanel({ profile, playerName, onClose }: {
  profile: PlayerProfile;
  playerName: string;
  onClose: () => void;
}) {
  const chartData = [...profile.season_stats]
    .sort((a, b) => a.season - b.season)
    .map((s) => ({
      season: String(s.season),
      xG: parseFloat(s.xg.toFixed(2)),
      Gol: s.goals,
      xA: parseFloat(s.xa.toFixed(2)),
    }));

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="bg-white rounded-[28px] shadow-sm border border-slate-100 overflow-hidden"
    >
      <div className="bg-[#0A192F] px-6 py-4 flex items-center justify-between">
        <div>
          <h2 className="font-black text-xl text-white uppercase tracking-tight">{playerName}</h2>
          <div className="flex items-center gap-2 mt-1">
            {profile.labels.map((l) => <LabelBadge key={l} label={l} />)}
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white text-xs font-black uppercase tracking-widest transition-colors"
        >
          Chiudi ×
        </button>
      </div>

      <div className="p-6">
        {/* Metriche principali */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <MetricPill label="xG Pesato" value={profile.weighted_xg.toFixed(2)} accent />
          <MetricPill label="xA Pesato" value={profile.weighted_xa.toFixed(2)} />
          <MetricPill label="Breakout ×" value={profile.breakout_multiplier.toFixed(2)} accent={profile.breakout_multiplier > 1.1} />
          <MetricPill label="Max Bid %" value={`${profile.max_bid_percentage.toFixed(1)}%`} accent />
        </div>

        {/* TAI */}
        <div className="flex items-center gap-2 mb-6">
          <div className="bg-slate-50 rounded-xl px-4 py-2 border border-slate-100">
            <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Team Attack Index: </span>
            <span className={`text-sm font-black ${profile.team_attack_index >= 1.2 ? "text-emerald-600" : profile.team_attack_index <= 0.8 ? "text-red-500" : "text-slate-700"}`}>
              {profile.team_attack_index.toFixed(1)}
              {profile.team_attack_index >= 1.2 ? " 🔥 Top Attack" : profile.team_attack_index <= 0.8 ? " ⚠️ Weak Attack" : " — Medio"}
            </span>
          </div>
          <div className="bg-slate-50 rounded-xl px-4 py-2 border border-slate-100">
            <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Value Score: </span>
            <span className="text-sm font-black text-[#FF2A6D]">{profile.value_score.toFixed(1)} pts</span>
          </div>
        </div>

        {/* Chart xG vs Gol */}
        {chartData.length > 0 && (
          <div>
            <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-3">
              Trend xG vs Gol per Stagione
            </p>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={chartData} margin={{ top: 4, right: 16, left: -16, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="season" tick={{ fontSize: 10, fontWeight: 700 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 11, fontWeight: 700 }}
                />
                <Legend wrapperStyle={{ fontSize: 10, fontWeight: 700 }} />
                <Line type="monotone" dataKey="xG" stroke="#FF2A6D" strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                <Line type="monotone" dataKey="Gol" stroke="#0ea5e9" strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                <Line type="monotone" dataKey="xA" stroke="#a855f7" strokeWidth={1.5} strokeDasharray="4 2" dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </motion.div>
  );
}

// ─── PAGE ─────────────────────────────────────────────────────────────────────

type Tab = "dashboard" | "search" | "auction";

export default function FantaDraftPage() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [dashLoading, setDashLoading] = useState(true);
  const [dashError, setDashError] = useState<string | null>(null);

  // Search
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<SearchResult[]>([]);
  const [profile, setProfile] = useState<PlayerProfile | null>(null);
  const [profileName, setProfileName] = useState("");
  const [profileLoading, setProfileLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Auction
  const [auctionBudget, setAuctionBudget] = useState(500);
  const [auctionParticipants, setAuctionParticipants] = useState(8);
  const [auctionTargets, setAuctionTargets] = useState<AuctionTarget[]>([]);
  const [auctionLoading, setAuctionLoading] = useState(false);

  // Load dashboard on mount
  useEffect(() => {
    fetch(`${API}/dashboard`)
      .then((r) => r.json())
      .then((data) => { setDashboard(data); setDashLoading(false); })
      .catch(() => { setDashError("Backend non raggiungibile (porta 8000)."); setDashLoading(false); });
  }, []);

  // Debounced search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (query.length < 2) { setSuggestions([]); return; }
    debounceRef.current = setTimeout(() => {
      fetch(`${API}/search?q=${encodeURIComponent(query)}`)
        .then((r) => r.json())
        .then((data) => setSuggestions(Array.isArray(data) ? data : []))
        .catch(() => setSuggestions([]));
    }, 300);
  }, [query]);

  const loadProfile = async (result: SearchResult) => {
    setSuggestions([]);
    setQuery(result.player);
    setProfileLoading(true);
    setProfile(null);
    try {
      const r = await fetch(`${API}/player/${result.player_id}`);
      const data = await r.json();
      setProfile(data);
      setProfileName(result.player);
    } catch {
      setProfile(null);
    } finally {
      setProfileLoading(false);
    }
  };

  const loadFromDashboard = async (p: DashboardPlayer) => {
    setTab("search");
    setQuery(p.player);
    setProfileLoading(true);
    setProfile(null);
    setProfileName(p.player);
    setSuggestions([]);
    try {
      const r = await fetch(`${API}/player/${p.player_id}`);
      const data = await r.json();
      setProfile(data);
    } catch {
      setProfile(null);
    } finally {
      setProfileLoading(false);
    }
  };

  const calcAuction = async () => {
    setAuctionLoading(true);
    try {
      const r = await fetch(`${API}/auction-strategy?budget=${auctionBudget}&participants=${auctionParticipants}`);
      const data = await r.json();
      setAuctionTargets(data.targets ?? []);
    } catch {
      setAuctionTargets([]);
    } finally {
      setAuctionLoading(false);
    }
  };

  const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "dashboard", label: "Dashboard", icon: <TrendingUp size={14} /> },
    { id: "search",    label: "Cerca Giocatore", icon: <Search size={14} /> },
    { id: "auction",   label: "Auction Strategy", icon: <DollarSign size={14} /> },
  ];

  const TAI_COLOR = (tai: number) =>
    tai >= 1.2 ? "text-emerald-600" : tai <= 0.8 ? "text-red-500" : "text-slate-500";

  return (
    <div className="min-h-screen bg-[#F1F5F9] font-sans pb-20">

      {/* HERO */}
      <div className="bg-[#0A192F] pt-12 pb-20 px-6 border-b-4 border-[#FF2A6D]">
        <div className="max-w-5xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-[#FF2A6D]/10 border border-[#FF2A6D]/30 text-[#FF2A6D] text-[10px] font-black uppercase tracking-widest px-4 py-2 rounded-full mb-5">
            <Zap size={11} /> Arbitraggio Statistico
          </div>
          <h1 className="text-5xl font-black text-white uppercase tracking-tighter italic">
            FANTA<span className="text-[#FF2A6D]">DRAFT</span> ENGINE
          </h1>
          <p className="text-slate-400 font-bold uppercase text-xs tracking-widest mt-3 max-w-xl">
            Risposte brutali per fantallenatori · Chi compro? Chi evito? A quanto lo prendo?
          </p>
        </div>
      </div>

      <div className="max-w-[1400px] mx-auto -mt-6 px-6">

        {/* TABS */}
        <div className="flex gap-2 mb-8">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-5 py-3 rounded-2xl text-xs font-black uppercase tracking-widest transition-all shadow-sm
                ${tab === t.id
                  ? "bg-[#FF2A6D] text-white shadow-[0_0_12px_rgba(255,42,109,0.4)]"
                  : "bg-white text-slate-400 hover:text-[#0A192F] border border-slate-200"
                }`}
            >
              {t.icon} {t.label}
            </button>
          ))}
        </div>

        {/* ── DASHBOARD TAB ── */}
        {tab === "dashboard" && (
          <AnimatePresence mode="wait">
            {dashLoading ? (
              <motion.div key="load" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="flex flex-col items-center justify-center py-32">
                <Loader2 size={40} className="animate-spin text-slate-300 mb-4" />
                <p className="font-black uppercase text-slate-400 text-xs tracking-widest">Caricamento dati dal database...</p>
              </motion.div>
            ) : dashError ? (
              <motion.div key="err" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="bg-red-50 border-2 border-red-200 rounded-3xl p-8 text-center">
                <AlertTriangle className="mx-auto text-red-400 mb-3" size={32} />
                <p className="font-black text-red-600 uppercase text-sm">{dashError}</p>
              </motion.div>
            ) : dashboard ? (
              <motion.div key="data" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <WidgetCard
                  title="Best Value Picks"
                  badge="Sottovalutati"
                  badgeColor="bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                  icon={<TrendingUp size={14} />}
                  emptyText="Nessun sottovalutato trovato"
                  players={dashboard.best_value_picks}
                  onSelect={loadFromDashboard}
                />
                <WidgetCard
                  title="Breakout Candidates"
                  badge="Esplosivi"
                  badgeColor="bg-amber-500/20 text-amber-400 border-amber-500/40"
                  icon={<Zap size={14} />}
                  emptyText="Nessun breakout candidate"
                  players={dashboard.breakout_candidates}
                  onSelect={loadFromDashboard}
                />
                <WidgetCard
                  title="Toxic Assets / Avoid"
                  badge="Pericolosi"
                  badgeColor="bg-red-500/20 text-red-400 border-red-500/40"
                  icon={<TrendingDown size={14} />}
                  emptyText="Nessun toxic asset trovato"
                  players={dashboard.toxic_assets}
                  onSelect={loadFromDashboard}
                />
                <WidgetCard
                  title="Safe Picks"
                  badge="Affidabili"
                  badgeColor="bg-sky-500/20 text-sky-400 border-sky-500/40"
                  icon={<Shield size={14} />}
                  emptyText="Nessun safe pick trovato"
                  players={dashboard.safe_picks}
                  onSelect={loadFromDashboard}
                />
              </motion.div>
            ) : null}
          </AnimatePresence>
        )}

        {/* ── SEARCH TAB ── */}
        {tab === "search" && (
          <div className="space-y-6">
            {/* Search input */}
            <div className="relative">
              <div className="flex items-center gap-3 bg-white rounded-2xl border border-slate-200 px-5 py-4 shadow-sm">
                <Search size={18} className="text-slate-400 flex-shrink-0" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Cerca un giocatore… (es. Lautaro, Vlahovic)"
                  className="flex-1 bg-transparent text-[#0A192F] font-bold placeholder:text-slate-300 placeholder:font-normal outline-none text-sm"
                />
                {query && (
                  <button onClick={() => { setQuery(""); setSuggestions([]); setProfile(null); }}
                    className="text-slate-400 hover:text-[#FF2A6D] text-xs font-black transition-colors">✕</button>
                )}
              </div>

              {/* Autocomplete dropdown */}
              <AnimatePresence>
                {suggestions.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    className="absolute top-full left-0 right-0 mt-2 bg-white rounded-2xl border border-slate-200 shadow-xl z-50 overflow-hidden"
                  >
                    {suggestions.map((s) => (
                      <button
                        key={s.player_id}
                        onClick={() => loadProfile(s)}
                        className="w-full flex items-center justify-between px-5 py-3 hover:bg-slate-50 transition-colors text-left"
                      >
                        <span className="font-black text-sm text-[#0A192F]">{s.player}</span>
                        <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest bg-slate-100 px-2 py-0.5 rounded">
                          {s.position}
                        </span>
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Profile */}
            {profileLoading && (
              <div className="flex justify-center py-16">
                <Loader2 size={32} className="animate-spin text-[#FF2A6D]" />
              </div>
            )}
            <AnimatePresence>
              {profile && !profileLoading && (
                <PlayerProfilePanel
                  key={profileName}
                  profile={profile}
                  playerName={profileName}
                  onClose={() => { setProfile(null); setQuery(""); }}
                />
              )}
            </AnimatePresence>

            {!profile && !profileLoading && !query && (
              <div className="text-center py-20">
                <Search size={40} className="mx-auto text-slate-200 mb-4" />
                <p className="font-black uppercase text-slate-300 text-xs tracking-widest">
                  Digita almeno 2 caratteri per cercare un giocatore
                </p>
              </div>
            )}
          </div>
        )}

        {/* ── AUCTION TAB ── */}
        {tab === "auction" && (
          <div className="space-y-6">
            <div className="bg-white rounded-[28px] border border-slate-100 shadow-sm overflow-hidden">
              <div className="bg-[#0A192F] px-6 py-4 flex items-center gap-3">
                <DollarSign size={16} className="text-[#FF2A6D]" />
                <span className="text-xs font-black text-white uppercase tracking-widest">Auction Strategy Mode</span>
              </div>
              <div className="p-6">
                <div className="flex flex-wrap gap-4 mb-6">
                  <div>
                    <label className="block text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">
                      Budget totale (crediti)
                    </label>
                    <input
                      type="number"
                      value={auctionBudget}
                      onChange={(e) => setAuctionBudget(Number(e.target.value))}
                      min={1}
                      className="bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-black text-[#0A192F] w-40 outline-none focus:border-[#FF2A6D]"
                    />
                  </div>
                  <div>
                    <label className="block text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">
                      N° partecipanti
                    </label>
                    <input
                      type="number"
                      value={auctionParticipants}
                      onChange={(e) => setAuctionParticipants(Number(e.target.value))}
                      min={1}
                      className="bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-black text-[#0A192F] w-40 outline-none focus:border-[#FF2A6D]"
                    />
                  </div>
                  <div className="flex items-end">
                    <button
                      onClick={calcAuction}
                      disabled={auctionLoading}
                      className="flex items-center gap-2 bg-[#FF2A6D] hover:bg-[#e0245f] disabled:opacity-50 text-white font-black uppercase text-xs tracking-widest px-6 py-3 rounded-xl transition-all shadow-md"
                    >
                      {auctionLoading ? <Loader2 size={14} className="animate-spin" /> : <Target size={14} />}
                      Calcola Target
                    </button>
                  </div>
                </div>

                {auctionTargets.length > 0 && (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b-2 border-slate-100">
                          {["Giocatore", "Ruolo", "Squadra", "TAI", "Value Score", "Prezzo Max", "% Budget"].map((h) => (
                            <th key={h} className="text-left text-[9px] font-black text-slate-400 uppercase tracking-widest pb-3 pr-4">
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {auctionTargets.map((t, i) => (
                          <tr key={t.name} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
                            <td className="py-3 pr-4">
                              <span className="font-black text-sm text-[#0A192F]">{t.name}</span>
                            </td>
                            <td className="py-3 pr-4">
                              <span className="text-[9px] font-black uppercase tracking-widest bg-slate-100 px-2 py-1 rounded">
                                {t.position}
                              </span>
                            </td>
                            <td className="py-3 pr-4 text-xs font-bold text-slate-500">{t.team}</td>
                            <td className={`py-3 pr-4 text-xs font-black ${TAI_COLOR(t.tai)}`}>
                              {t.tai.toFixed(1)}
                            </td>
                            <td className="py-3 pr-4">
                              <span className="font-black text-[#FF2A6D]">{t.value_score}</span>
                            </td>
                            <td className="py-3 pr-4">
                              <span className="font-black text-[#0A192F] text-base">{t.max_price}</span>
                              <span className="text-slate-400 text-xs ml-1">cr</span>
                            </td>
                            <td className="py-3">
                              <div className="flex items-center gap-2">
                                <div className="w-16 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                                  <div
                                    className="h-full bg-[#FF2A6D] rounded-full"
                                    style={{ width: `${Math.min(t.budget_percentage * 5, 100)}%` }}
                                  />
                                </div>
                                <span className="text-xs font-black text-slate-600">{t.budget_percentage}%</span>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {!auctionLoading && auctionTargets.length === 0 && (
                  <div className="text-center py-12">
                    <Users size={32} className="mx-auto text-slate-200 mb-3" />
                    <p className="font-black uppercase text-slate-300 text-xs tracking-widest">
                      Inserisci il budget e calcola i target ottimali
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verificare che non ci siano import mancanti**

Recharts è in `package.json` (`"recharts": "^3.7.0"`). Framer Motion e Lucide sono già usati nel progetto. Nessuna installazione necessaria.

- [ ] **Step 3: Verificare la pagina nel browser**

Con frontend su porta 3000:
```
http://localhost:3000/fanta-draft
```
Expected:
- Hero dark + tab bar visibile
- Dashboard carica 4 widget (se backend up)
- Search debounce funziona a 300ms
- Player profile mostra grafico Recharts
- Auction Strategy calcola e mostra tabella

- [ ] **Step 4: Commit frontend**

```bash
cd "C:\Users\euron\Desktop\claude of control"
git add frontend/app/fanta-draft/page.tsx
git commit -m "feat(fanta): add /fanta-draft Next.js page with dashboard, search, auction, trend chart"
```

---

## Checklist Finale

- [ ] `GET /api/fanta/search?q=xxx` ritorna `[{player, player_id, position}]`
- [ ] `GET /api/fanta/dashboard` ritorna 4 liste non vuote con dati reali
- [ ] `GET /api/fanta/auction-strategy?budget=500&participants=8` ritorna targets con max_price
- [ ] TAI viene calcolato da matchcalendar (non più placeholder 1.0)
- [ ] `/fanta-draft` visibile in browser con hero, tab, widget, search, chart
- [ ] Click su giocatore nel dashboard porta alla sua scheda profilo
- [ ] Grafico xG vs Gol vs xA visibile nel profilo giocatore
- [ ] Barra progress budget nella tabella auction
