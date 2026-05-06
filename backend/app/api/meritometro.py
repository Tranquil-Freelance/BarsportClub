from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, text
import math
from datetime import datetime, timezone
from typing import Dict, List

from app.db.database import get_db
from app.db.models import Match, Shot, PlayerStat 

router = APIRouter()

def sanitize_metric(value):
    if value is None: 
        return 0.0
    try:
        f_val = float(value)
        if math.isnan(f_val) or math.isinf(f_val): 
            return 0.0
        return f_val
    except (ValueError, TypeError): 
        return 0.0

# ==========================================
# ENDPOINT 1: STAGIONE COMPLETA CON IMR 2.0 (PYTHON BULLETPROOF)
# ==========================================
@router.get("/meritometro/season")
async def get_season_meritometro(league: str = Query(..., description="Filtro Lega"), db: AsyncSession = Depends(get_db)):
    try:
        league_query = text("SELECT id FROM league WHERE name ILIKE :lname LIMIT 1")
        league_res = await db.execute(league_query, {"lname": f"%{league}%"})
        league_row = league_res.fetchone()
        
        if not league_row:
            return []
            
        league_id = league_row[0]

        # 1. Recupero Dati Base Matches
        matches = (await db.execute(text("""
            SELECT m.id, th.name, ta.name, m.home_goals, m.away_goals, 
                   m."home_xG", m."away_xG", m.matchday, m.home_deep, m.away_deep
            FROM matchcalendar m
            JOIN team th ON m.home_team_id = th.id 
            JOIN team ta ON m.away_team_id = ta.id 
            WHERE m.league_id = :lid 
              AND m.match_datetime >= '2025-07-01' 
              AND m.home_goals IS NOT NULL
            ORDER BY m.match_datetime DESC
            LIMIT 380
        """), {"lid": league_id})).fetchall()
        
        if not matches: return []
        match_ids = [int(m[0]) for m in matches]
        
        # 2. Recupero Micro-Dati (Tiri e Assist)
        shots = (await db.execute(text('SELECT match_id, team_type, situation, result, "xG", "X" FROM shots WHERE match_id = ANY(:ids)'), {"ids": match_ids})).fetchall()
        
        # Fallback intelligente per gli assist
        try: 
            kps = (await db.execute(text('SELECT match_id, team_type, "xA", "xGChain" FROM player_stats WHERE match_id = ANY(:ids)'), {"ids": match_ids})).fetchall()
        except: 
            try: kps = (await db.execute(text('SELECT match_id, team_type, "xA", "xGChain" FROM rosters WHERE match_id = ANY(:ids)'), {"ids": match_ids})).fetchall()
            except: kps = []

        # 3. Motore di Calcolo Sicuro in Python
        imr_map = {m_id: {'h': 0.0, 'a': 0.0} for m_id in match_ids}

        for s in shots:
            m_id = int(s[0])
            t_type = 'h' if str(s[1]).lower().startswith('h') else 'a'
            sit = str(s[2]).lower() if s[2] else ''
            res = str(s[3]).lower() if s[3] else ''
            xg_val = sanitize_metric(s[4])
            x_val = sanitize_metric(s[5])
            
            pts = 0.0
            if 'penalty' in sit:
                pts = 1.5
            else:
                pts = (xg_val * 3.0)
                if xg_val >= 0.30:
                    pts += 1.0
                if x_val > 0.85:
                    if 'post' in res:
                        pts += 0.8
                    elif 'goal' in res or 'saved' in res:
                        pts += 0.5
            imr_map[m_id][t_type] += pts

        for k in kps:
            m_id = int(k[0])
            t_type = 'h' if str(k[1]).lower().startswith('h') else 'a'
            xa = sanitize_metric(k[2])
            xgc = sanitize_metric(k[3])
            imr_map[m_id][t_type] += (xa * 0.8) + (xgc * 0.2)

        # 4. Assemblaggio Risultato per il Frontend
        response_data = []
        for m in matches:
            m_id = int(m[0])
            home_name = str(m[1])
            away_name = str(m[2])
            
            h_deep = sanitize_metric(m[8])
            a_deep = sanitize_metric(m[9])
            
            imr_h = round(imr_map[m_id]['h'] + (h_deep * 0.05), 1)
            imr_a = round(imr_map[m_id]['a'] + (a_deep * 0.05), 1)
            
         # Calcoliamo PRIMA le percentuali per la barra
            tot_imr = imr_h + imr_a
            if tot_imr > 0:
                perc_h = round((imr_h / tot_imr) * 100, 1)
                perc_a = round((imr_a / tot_imr) * 100, 1)
            else:
                perc_h = 50.0
                perc_a = 50.0

            # Il verdetto ora segue la barra con toni più cauti e analitici
            max_perc = max(perc_h, perc_a)
            
            if max_perc <= 55.0:
                verdetto = "EQUILIBRIO"
            else:
                if max_perc >= 72.0:
                    pref = "NETTA SUPERIORITÀ"
                elif max_perc >= 62.0:
                    pref = "MERITO"
                else:
                    pref = "LIEVE PREVALENZA"
                    
                vincente = home_name if imr_h > imr_a else away_name
                verdetto = f"{pref} {vincente}".upper()

            response_data.append({
                "id": str(m_id),
                "home": home_name,
                "away": away_name,
                "scoreH": int(m[3]),
                "scoreA": int(m[4]),
                "xGH": sanitize_metric(m[5]),
                "xGA": sanitize_metric(m[6]),
                "round": int(m[7]) if m[7] else 0,
                "imrH": imr_h,
                "imrA": imr_a,
                "verdetto": verdetto,
                "perc_H": perc_h,
                "perc_A": perc_a,
                "status": "FT"
            })
            
        return response_data
    except Exception as e:
        print(f"[ERRORE CRITICO MERITOMETRO SEASON] {e}")
        return []

# ==========================================
# ENDPOINT 1.5: CLASSIFICA IMR ASSOLUTA
# ==========================================
@router.get("/meritometro/imr_standings")
async def get_imr_standings(league: str = Query(..., description="Filtro Lega"), db: AsyncSession = Depends(get_db)):
    try:
        league_query = text("SELECT id FROM league WHERE name ILIKE :lname LIMIT 1")
        league_res = await db.execute(league_query, {"lname": f"%{league}%"})
        league_row = league_res.fetchone()
        
        if not league_row:
            return []
            
        league_id = league_row[0]

        matches = (await db.execute(text("""
            SELECT m.id, th.name as home_name, ta.name as away_name, m.home_deep, m.away_deep
            FROM (
                SELECT DISTINCT ON (home_team_id, away_team_id) *
                FROM matchcalendar
                WHERE league_id = :league_id AND match_datetime >= '2025-07-01' AND home_goals IS NOT NULL
                ORDER BY home_team_id, away_team_id, match_datetime DESC
            ) AS m
            JOIN team th ON m.home_team_id = th.id
            JOIN team ta ON m.away_team_id = ta.id
        """), {"league_id": league_id})).fetchall()
        
        if not matches: return []
        match_ids = [int(m[0]) for m in matches]
        
        shots = (await db.execute(text('SELECT match_id, team_type, situation, result, "xG", "X" FROM shots WHERE match_id = ANY(:ids)'), {"ids": match_ids})).fetchall()
        
        try: kps = (await db.execute(text('SELECT match_id, team_type, "xA", "xGChain" FROM player_stats WHERE match_id = ANY(:ids)'), {"ids": match_ids})).fetchall()
        except: 
            try: kps = (await db.execute(text('SELECT match_id, team_type, "xA", "xGChain" FROM rosters WHERE match_id = ANY(:ids)'), {"ids": match_ids})).fetchall()
            except: kps = []

        imr_map = {m_id: {'h': 0.0, 'a': 0.0} for m_id in match_ids}

        for s in shots:
            m_id = int(s[0])
            t_type = 'h' if str(s[1]).lower().startswith('h') else 'a'
            sit = str(s[2]).lower() if s[2] else ''
            res = str(s[3]).lower() if s[3] else ''
            xg_val = sanitize_metric(s[4])
            x_val = sanitize_metric(s[5])
            
            pts = 0.0
            if 'penalty' in sit:
                pts = 1.5
            else:
                pts = (xg_val * 3.0)
                if xg_val >= 0.30: pts += 1.0
                if x_val > 0.85:
                    if 'post' in res: pts += 0.8
                    elif 'goal' in res or 'saved' in res: pts += 0.5
            imr_map[m_id][t_type] += pts

        for k in kps:
            m_id = int(k[0])
            t_type = 'h' if str(k[1]).lower().startswith('h') else 'a'
            xa = sanitize_metric(k[2])
            xgc = sanitize_metric(k[3])
            imr_map[m_id][t_type] += (xa * 0.8) + (xgc * 0.2)

        standings_dict = {}
        for m in matches:
            m_id, home_name, away_name = int(m[0]), str(m[1]), str(m[2])
            
            h_deep = sanitize_metric(m[3])
            a_deep = sanitize_metric(m[4])
            
            final_h = imr_map[m_id]['h'] + (h_deep * 0.05)
            final_a = imr_map[m_id]['a'] + (a_deep * 0.05)
            
            if home_name not in standings_dict: standings_dict[home_name] = 0.0
            if away_name not in standings_dict: standings_dict[away_name] = 0.0
            
            standings_dict[home_name] += final_h
            standings_dict[away_name] += final_a

        standings_list = [{"name": team, "total_imr": round(total, 1)} for team, total in standings_dict.items()]
        standings_list.sort(key=lambda x: x["total_imr"], reverse=True)

        return standings_list
        
    except Exception as e:
        print(f"[ERRORE IMR STANDINGS] {e}")
        return []

# ==========================================
# ENDPOINT 2: CLASSIFICA SICURA (FILTRATA PER DATA)
# ==========================================
@router.get("/meritometro/standings")
async def get_standings_secure(league: str = Query("Serie A", description="Filtro Lega"), db: AsyncSession = Depends(get_db)):
    try:
        league_query = text("SELECT id FROM league WHERE name ILIKE :lname LIMIT 1")
        league_res = await db.execute(league_query, {"lname": f"%{league}%"})
        league_row = league_res.fetchone()
        
        if not league_row:
            return []
            
        league_id = league_row[0]

        teams_dict = {}
        try:
            teams_result = await db.execute(text("SELECT id, name FROM team"))
            for row in teams_result.fetchall():
                teams_dict[row[0]] = str(row[1])
        except:
            pass

        query = text("""
            SELECT home_team_id, away_team_id, home_goals, away_goals 
            FROM matchcalendar 
            WHERE league_id = :league_id 
              AND match_datetime >= '2025-07-01' 
              AND is_scraped = True
              AND home_goals IS NOT NULL
        """)
        result = await db.execute(query, {"league_id": league_id})
        
        standings_map = {}
        for m in result.fetchall():
            hid, aid, hg, ag = m[0], m[1], m[2], m[3]

            if hid not in standings_map:
                standings_map[hid] = {"name": teams_dict.get(hid, f"Squadra {hid}"), "played": 0, "points": 0}
            if aid not in standings_map:
                standings_map[aid] = {"name": teams_dict.get(aid, f"Squadra {aid}"), "played": 0, "points": 0}

            standings_map[hid]["played"] += 1
            standings_map[aid]["played"] += 1

            if hg > ag:
                standings_map[hid]["points"] += 3
            elif hg < ag:
                standings_map[aid]["points"] += 3
            else:
                standings_map[hid]["points"] += 1
                standings_map[aid]["points"] += 1

        standings_list = list(standings_map.values())
        standings_list.sort(key=lambda x: x["points"], reverse=True)

        return standings_list
    except Exception as e:
        print(f"[ERRORE CLASSIFICA] {e}")
        return []

# ==========================================
# ENDPOINT 3: DETTAGLIO MATCH (RAW SQL + CALCOLO TIRI INTEGRATO)
# ==========================================
@router.get("/matches/{match_id}/details")
async def get_match_details(match_id: int, db: AsyncSession = Depends(get_db)):
    try:
        # 1. Recupero dati macro
        query_match = text("SELECT * FROM matchcalendar WHERE id = :id")
        res_match = await db.execute(query_match, {"id": match_id})
        match_row = res_match.fetchone()
        
        if not match_row:
            raise HTTPException(status_code=404, detail="Partita non trovata")
            
        m = match_row._mapping

        # 2. Recupero nomi squadre
        teams_result = await db.execute(text("SELECT id, name FROM team"))
        teams_dict = {row[0]: row[1] for row in teams_result.fetchall()}
            
        home_name = teams_dict.get(m['home_team_id'], "Home")
        away_name = teams_dict.get(m['away_team_id'], "Away")

        # 3. Recupero Micro-Dati (Tiri) e Calcolo Aggregati
        shots_stmt = text('SELECT minute, "xG", team_type, player, result, "X", "Y", situation, "shotType", assist FROM shots WHERE match_id = :id')
        shots_result = await db.execute(shots_stmt, {"id": match_id})
        raw_shots = shots_result.fetchall()
        
        home_shots = 0
        away_shots = 0
        home_sot = 0  
        away_sot = 0
        
        shots_data = []
        for s in raw_shots:
            is_home = str(s[2]).lower().startswith('h')
            team_label = "home" if is_home else "away"
            res = str(s[4]).lower() if s[4] else ''
            
            if is_home:
                home_shots += 1
                if 'goal' in res or 'saved' in res:
                    home_sot += 1
            else:
                away_shots += 1
                if 'goal' in res or 'saved' in res:
                    away_sot += 1
                    
            shots_data.append({
                "minute": s[0], 
                "xG": sanitize_metric(s[1]), 
                "team": team_label,
                "player": s[3], 
                "result": s[4],
                "X": sanitize_metric(s[5]),
                "Y": sanitize_metric(s[6]),
                "situation": s[7] if s[7] else 'Open play',
                "shotType": s[8] if s[8] else 'N/A',  
                "assist": s[9] if s[9] else '-'       
            })

        # 4. Costruzione del pacchetto per il Frontend
        match_data = {
            "id": m['id'],
            "home_team": home_name,
            "away_team": away_name,
            "home_score": m['home_goals'] if m['home_goals'] is not None else 0,
            "away_score": m['away_goals'] if m['away_goals'] is not None else 0,
            "home_xG": sanitize_metric(m['home_xG']),
            "away_xG": sanitize_metric(m['away_xG']),
            "round": m['matchday'] if m['matchday'] is not None else 0,
            "status": "FT" if m['home_goals'] is not None else "Pre",
            "stats": {
                "home_shots": home_shots,
                "away_shots": away_shots,
                "home_sot": home_sot,
                "away_sot": away_sot,
                "home_deep": int(sanitize_metric(m['home_deep'])),
                "away_deep": int(sanitize_metric(m['away_deep'])),
                "home_ppda": sanitize_metric(m['home_ppda']),
                "away_ppda": sanitize_metric(m['away_ppda']),
                "home_xpts": sanitize_metric(m['home_xpts']),
                "away_xpts": sanitize_metric(m['away_xpts']),
            }
        }

        return {"match": match_data, "shots": shots_data}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERRORE DETTAGLIO MATCH] {e}")
        raise HTTPException(status_code=500, detail="Errore interno al server")

# ==========================================
# ENDPOINT 3b: LINEUP + SOSTITUZIONI
# ==========================================

_POS_LINE = {
    'GK': 0,
    'DC': 1, 'DL': 1, 'DR': 1, 'DML': 1, 'DMR': 1, 'WBL': 1, 'WBR': 1, 'D': 1,
    'DM': 2, 'DMC': 2,
    'MC': 3, 'ML': 3, 'MR': 3, 'M': 3,
    'AMC': 4, 'AML': 4, 'AMR': 4, 'SS': 4,
    'FW': 5, 'CF': 5, 'ST': 5,
}

@router.get("/matches/{match_id}/lineup")
async def get_match_lineup(match_id: int, db: AsyncSession = Depends(get_db)):
    """
    Legge ESCLUSIVAMENTE dalla tabella rosters.
    - Titolari:   position != 'Sub'
    - Panchina:   position == 'Sub'
    - Entrato:    roster_in  > 0  (minuto di ingresso)
    - Uscito:     roster_out > 0  (minuto di uscita)
    - Squadra:    team_type  = 'h' | 'a'  oppure ricavata da team_id
    """
    try:
        res = await db.execute(text("""
            SELECT
                r.player,
                r.position,
                r.team_type,
                r.goals,
                r.yellow_card,
                r.red_card,
                r.roster_in,
                r.roster_out
            FROM rosters r
            WHERE r.match_id = :mid
            ORDER BY r.team_type, r.position
        """), {"mid": match_id})
        rows = [dict(r) for r in res.mappings().all()]

        if not rows:
            return {"home": None, "away": None}

        # ── Ricava nomi squadre ──────────────────────────────────────
        mc = await db.execute(
            text("SELECT home_team_id, away_team_id FROM matchcalendar WHERE id = :id"),
            {"id": match_id}
        )
        match_row = mc.fetchone()

        teams_res = await db.execute(text("SELECT id, name FROM team"))
        teams_dict = {r[0]: r[1] for r in teams_res.fetchall()}

        home_name = teams_dict.get(match_row[0], "Home") if match_row else "Home"
        away_name = teams_dict.get(match_row[1], "Away") if match_row else "Away"

        def resolve_side(row: dict) -> str:
            tt = (row.get("team_type") or "").lower().strip()
            return "a" if tt in ("a", "away") else "h"

        def build_team(side: str, tname: str) -> dict:
            tp = [r for r in rows if resolve_side(r) == side]
            starters = [r for r in tp if (r.get("position") or "").upper() != "SUB"]
            bench    = [r for r in tp if (r.get("position") or "").upper() == "SUB"]

            # Formazione: conta per linea i titolari non GK
            line_counts: dict = {}
            for r in starters:
                pos = (r.get("position") or "").upper()
                if pos != "GK":
                    ln = _POS_LINE.get(pos, 3)
                    line_counts[ln] = line_counts.get(ln, 0) + 1
            formation = "-".join(str(line_counts[k]) for k in sorted(line_counts)) if line_counts else ""

            # Titolari
            starters_out = []
            for r in starters:
                pos = (r.get("position") or "").upper()
                rout = int(r.get("roster_out") or 0)
                starters_out.append({
                    "name":           r["player"],
                    "position":       pos,
                    "position_line":  _POS_LINE.get(pos, 3),
                    "goals":          int(r.get("goals") or 0),
                    "yellow_cards":   int(r.get("yellow_card") or 0),
                    "red_cards":      int(r.get("red_card") or 0),
                    "subbed_off":     rout > 0,
                    "sub_minute":     rout if rout > 0 else None,
                })

            # Panchina
            bench_out = []
            for r in bench:
                rin = int(r.get("roster_in") or 0)
                bench_out.append({
                    "name":           r["player"],
                    "goals":          int(r.get("goals") or 0),
                    "yellow_cards":   int(r.get("yellow_card") or 0),
                    "red_cards":      int(r.get("red_card") or 0),
                    "came_on":        rin > 0,
                    "came_on_minute": rin if rin > 0 else None,
                })
            # Chi è entrato viene mostrato prima, poi il resto in ordine alfabetico
            bench_out.sort(key=lambda x: (not x["came_on"], x["name"]))

            return {
                "team_name":  tname,
                "formation":  formation,
                "starters":   starters_out,
                "substitutes": bench_out,
            }

        return {
            "home": build_team("h", home_name),
            "away": build_team("a", away_name),
        }

    except Exception as e:
        print(f"[ERRORE LINEUP] {e}")
        import traceback; traceback.print_exc()
        return {"home": None, "away": None, "error": str(e)}

# ==========================================
# ENDPOINT 4: MOTORE DEL MERITOMETRO (IMR SINGOLO MATCH)
# ==========================================
@router.get("/matches/{match_id}/imr", response_model=Dict)
async def get_indice_merito_reale(match_id: int, db: AsyncSession = Depends(get_db)):
    try:
        match = await db.get(Match, match_id)
        if not match:
            return {"error": "Match non trovato nel database"}

        teams_map = {}
        try:
            teams_res = await db.execute(text("SELECT id, name FROM team WHERE id IN (:h, :a)"), 
                                         {"h": match.home_team_id, "a": match.away_team_id})
            teams_map = {row[0]: row[1] for row in teams_res.fetchall()}
        except Exception as e:
            print(f"[ATTENZIONE IMR] Errore recupero nomi: {e}")
            
        home_name = teams_map.get(match.home_team_id, "Home")
        away_name = teams_map.get(match.away_team_id, "Away")
        
        home_score = getattr(match, 'home_goals', 0)
        away_score = getattr(match, 'away_goals', 0)
        home_xg = sanitize_metric(getattr(match, 'home_xG', 0.0))
        away_xg = sanitize_metric(getattr(match, 'away_xG', 0.0))
        home_deep = sanitize_metric(getattr(match, 'home_deep', 0.0))
        away_deep = sanitize_metric(getattr(match, 'away_deep', 0.0))

        query_tiri = text("""
            SELECT minute, team_type, situation, "result", xg_val, coord_x
            FROM (
                SELECT DISTINCT minute, player, team_type, situation, "result", "xG" as xg_val, "X" as coord_x
                FROM shots WHERE match_id = :match_id
            ) as distinct_shots
            ORDER BY minute ASC
        """)
        
        query_kp = text("""
            SELECT team_type, SUM("xA") as total_xa, SUM("xGChain") as total_xgchain
            FROM (
                SELECT DISTINCT player_name, team_type, "xA", "xGChain"
                FROM player_stats WHERE match_id = :match_id
            ) as distinct_kp
            GROUP BY team_type
        """)
        
        res_tiri = await db.execute(query_tiri, {"match_id": match_id})
        tiri = res_tiri.fetchall()
        
        res_kp = await db.execute(query_kp, {"match_id": match_id})
        key_passes = res_kp.fetchall()
        
        xa_dict = {'h': 0.0, 'a': 0.0}
        xgchain_dict = {'h': 0.0, 'a': 0.0}
        for row in key_passes:
            t_type = 'h' if str(row[0]).lower().startswith('h') else 'a'
            xa_dict[t_type] += sanitize_metric(row[1])
            xgchain_dict[t_type] += sanitize_metric(row[2])

        stats = {
            'h': {'occasioni': 0, 'tiri_in_area': 0, 'tiri_fuori_area': 0, 'rigori': 0},
            'a': {'occasioni': 0, 'tiri_in_area': 0, 'tiri_fuori_area': 0, 'rigori': 0}
        }
        
        timeline = [{"minute": 0, "home_imr": 0.0, "away_imr": 0.0}]
        goals_events = [] 
        
        current_imr_h = 0.0
        current_imr_a = 0.0

        for row in tiri:
            minute = row[0]
            team_type = 'h' if str(row[1]).lower().startswith('h') else 'a'
            sit = str(row[2]).lower() if row[2] else ''
            res = str(row[3]).lower() if row[3] else ''
            xg_clean = sanitize_metric(row[4])
            cx_clean = sanitize_metric(row[5])
            
            if 'goal' in res:
                goals_events.append({"minute": minute, "team": team_type})
                
            punti_tiro = 0.0
            if 'penalty' in sit:
                stats[team_type]['rigori'] += 1
                punti_tiro = 1.5
            else:
                punti_tiro = xg_clean * 3.0
                if xg_clean >= 0.30:
                    punti_tiro += 1.0
                    
                if cx_clean > 0.85:
                    if 'post' in res:
                        punti_tiro += 0.8
                    elif 'goal' in res or 'saved' in res:
                        punti_tiro += 0.5

            if xg_clean >= 0.30:
                stats[team_type]['occasioni'] += 1
            elif cx_clean > 0.85:
                stats[team_type]['tiri_in_area'] += 1
            else:
                stats[team_type]['tiri_fuori_area'] += 1

            if team_type == 'h':
                current_imr_h += punti_tiro
            else:
                current_imr_a += punti_tiro
                
            timeline.append({
                "minute": minute,
                "home_imr": round(current_imr_h, 1),
                "away_imr": round(current_imr_a, 1)
            })

        if timeline and timeline[-1]["minute"] < 90:
            timeline.append({"minute": 90, "home_imr": round(current_imr_h, 1), "away_imr": round(current_imr_a, 1)})

        imr_home_final = round(current_imr_h + (xa_dict['h'] * 0.8) + (xgchain_dict['h'] * 0.2) + (home_deep * 0.05), 1)
        imr_away_final = round(current_imr_a + (xa_dict['a'] * 0.8) + (xgchain_dict['a'] * 0.2) + (away_deep * 0.05), 1)

        diff = abs(imr_home_final - imr_away_final)
        if diff <= 2.5:
            verdetto = "SOSTANZIALE EQUILIBRIO"
        else:
            if diff >= 10.0:
                pref = "DOMINIO"
            elif diff >= 5.0:
                pref = "MERITO"
            else:
                pref = "LIEVE VANTAGGIO"
            vincente = home_name if imr_home_final > imr_away_final else away_name
            verdetto = f"{pref} {vincente}".upper()

        tot_imr = imr_home_final + imr_away_final
        perc_h = round((imr_home_final / tot_imr) * 100, 1) if tot_imr > 0 else 50.0
        perc_a = round((imr_away_final / tot_imr) * 100, 1) if tot_imr > 0 else 50.0

        return {
            "match_id": match_id,
            "home_name": home_name,
            "away_name": away_name,
            "home_score": home_score,
            "away_score": away_score,
            "home_xG": home_xg,
            "away_xG": away_xg,
            "imr_score": {"home": imr_home_final, "away": imr_away_final},
            "verdetto": verdetto,
            "perc_H": perc_h,
            "perc_A": perc_a,
            "timeline": timeline,
            "goals_timeline": goals_events, 
            "dettagli_home": {
                "occasioni_nitide": stats['h']['occasioni'],
                "tiri_in_area": stats['h']['tiri_in_area'],
                "tiri_fuori_area": stats['h']['tiri_fuori_area'],
                "azioni_promettenti": round(xa_dict['h'], 2),
                "rigori": stats['h']['rigori']
            },
            "dettagli_away": {
                "occasioni_nitide": stats['a']['occasioni'],
                "tiri_in_area": stats['a']['tiri_in_area'],
                "tiri_fuori_area": stats['a']['tiri_fuori_area'],
                "azioni_promettenti": round(xa_dict['a'], 2),
                "rigori": stats['a']['rigori']
            }
        }
    except Exception as e:
        print(f"[ERRORE IMR] {e}")
        return {"error": "Errore interno calcolo IMR"}

# ==========================================
# ENDPOINT 5: PDI RANKING
# ==========================================
@router.get("/meritometro/pdi-ranking")
async def get_pdi_ranking(league: str = Query("Serie A", description="Filtro Lega"), db: AsyncSession = Depends(get_db)):
    try:
        league_query = text("SELECT id FROM league WHERE name ILIKE :lname LIMIT 1")
        league_res = await db.execute(league_query, {"lname": f"%{league}%"})
        league_row = league_res.fetchone()
        
        if not league_row:
            return []
            
        league_id = league_row[0]

        query = text("""
            WITH UniqueShots AS (
                SELECT DISTINCT match_id, player, minute, team_type
                FROM shots
            ),
            TeamMatchStats AS (
                SELECT 
                    s.match_id,
                    m.league_id,
                    t.name as team_name,
                    COUNT(s.match_id) as total_shots
                FROM UniqueShots s
                JOIN matchcalendar m ON s.match_id = m.id
                JOIN team t ON (CASE WHEN LOWER(s.team_type) LIKE 'h%' THEN m.home_team_id ELSE m.away_team_id END) = t.id
                WHERE m.league_id = :league_id 
                  AND m.match_datetime >= '2025-07-01' 
                  AND m.is_scraped = True 
                  AND m.home_goals IS NOT NULL
                GROUP BY s.match_id, m.league_id, t.name
            ),
            UniquePlayerStats AS (
                SELECT DISTINCT match_id, player_name, team_name, "xG", "xA"
                FROM player_stats
            ),
            TeamPlayerStats AS (
                SELECT 
                    ps.match_id,
                    ps.team_name,
                    SUM(COALESCE(ps."xG", 0)) as total_xg,
                    SUM(COALESCE(ps."xA", 0)) as total_xa
                FROM UniquePlayerStats ps
                JOIN matchcalendar m ON ps.match_id = m.id
                WHERE m.league_id = :league_id 
                  AND m.match_datetime >= '2025-07-01' 
                  AND m.is_scraped = True 
                  AND m.home_goals IS NOT NULL
                GROUP BY ps.match_id, ps.team_name
            ),
            CombinedStats AS (
                SELECT 
                    tms.team_name,
                    tms.match_id,
                    tms.total_shots,
                    COALESCE(tps.total_xg, 0) as total_xg,
                    COALESCE(tps.total_xa, 0) as total_xa
                FROM TeamMatchStats tms
                LEFT JOIN TeamPlayerStats tps ON tms.match_id = tps.match_id AND tms.team_name = tps.team_name
            )
            SELECT 
                team_name,
                ROUND(AVG(total_shots)::numeric, 2) as avg_shots,
                ROUND(AVG(total_xg)::numeric, 2) as avg_xg,
                ROUND(AVG(total_xa)::numeric, 2) as avg_passes,
                ROUND(
                    ((0.4 * AVG(total_shots)) + 
                     (0.4 * AVG(total_xg)) + 
                     (0.2 * AVG(total_xa)))::numeric, 
                    2
                ) as pdi_index
            FROM CombinedStats
            GROUP BY team_name
            ORDER BY pdi_index DESC;
        """)
        
        result = await db.execute(query, {"league_id": league_id})
        
        dati_puliti = []
        for row in result:
            dati_puliti.append({
                "squadra": row[0],
                "media_tiri": float(row[1]),
                "media_xg": float(row[2]),
                "media_passaggi": float(row[3]),
                "pdi_index": float(row[4])
            })
        return dati_puliti
        
    except Exception as e:
        print(f"[ERRORE PDI RANKING] {e}")
        raise HTTPException(status_code=500, detail="Errore interno PDI Ranking")