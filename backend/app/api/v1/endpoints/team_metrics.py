from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import math

from app.db.database import get_db
from app.services.metrics_engine import calculate_ae, calculate_pdi, calculate_fli, calculate_dli

router = APIRouter()

def safe_float(val):
    if val is None: return 0.0
    try:
        f = float(val)
        return 0.0 if math.isnan(f) else f
    except:
        return 0.0

def safe_int(val):
    if val is None: return 0
    try:
        return int(val)
    except:
        return 0

@router.get("/advanced")
@router.get("/team-metrics/form-xg")
@router.get("/form-xg")
async def get_advanced_team_metrics(league: str = Query(None, description="Filtro Lega"), db: AsyncSession = Depends(get_db)):
    try:
        team_data = {}
        league_condition = ""
        params = {}
        if league:
            league_condition = "AND l.name ILIKE :lname"
            params["lname"] = f"%{league}%"

        query_matches = text(f"""
            SELECT th.name as home_team, ta.name as away_team, m.home_goals, m.away_goals, m."home_xG", m."away_xG"
            FROM matchcalendar m
            JOIN team th ON m.home_team_id = th.id
            JOIN team ta ON m.away_team_id = ta.id
            JOIN league l ON m.league_id = l.id
            WHERE m.is_completed = True {league_condition}
        """)
        
        res_matches = await db.execute(query_matches, params)
        matches = res_matches.fetchall()

        for m in matches:
            h_team, a_team = str(m[0]), str(m[1])
            h_goals, a_goals = safe_int(m[2]), safe_int(m[3])
            h_xg, a_xg = safe_float(m[4]), safe_float(m[5])

            if h_team not in team_data: team_data[h_team] = {'goals':0, 'xg':0.0, 'goals_conceded':0, 'xga':0.0, 'shots':0, 'key_passes':0}
            if a_team not in team_data: team_data[a_team] = {'goals':0, 'xg':0.0, 'goals_conceded':0, 'xga':0.0, 'shots':0, 'key_passes':0}

            team_data[h_team]['goals'] += h_goals
            team_data[h_team]['xg'] += h_xg
            team_data[h_team]['goals_conceded'] += a_goals
            team_data[h_team]['xga'] += a_xg

            team_data[a_team]['goals'] += a_goals
            team_data[a_team]['xg'] += a_xg
            team_data[a_team]['goals_conceded'] += h_goals
            team_data[a_team]['xga'] += h_xg

        query_players = text(f"""
            SELECT ps.team_name, SUM(ps.shots), SUM(ps.key_passes)
            FROM player_stats ps
            JOIN matchcalendar m ON ps.match_id = m.id
            JOIN league l ON m.league_id = l.id
            WHERE 1=1 {league_condition}
            GROUP BY ps.team_name
        """)
        res_players = await db.execute(query_players, params)
        
        for row in res_players.fetchall():
            team = str(row[0])
            if team in team_data:
                team_data[team]['shots'] += safe_int(row[1])
                team_data[team]['key_passes'] += safe_int(row[2])

        response = []
        for team, data in team_data.items():
            if team in ["Sconosciuta", "Home", "Away"]:
                continue

            # Matematica protetta contro la divisione per zero
            ae = calculate_ae(goals=data['goals'], xg=data['xg']) if data['xg'] > 0 else 0.0
            pdi = calculate_pdi(shots=data['shots'], xg=data['xg'], key_passes=data['key_passes']) if data['xg'] > 0 else 0.0
            fli = calculate_fli(goals=data['goals'], xg=data['xg']) if data['xg'] > 0 else 0.0
            dli = calculate_dli(xga=data['xga'], goals_conceded=data['goals_conceded']) if data['xga'] > 0 else 0.0

            response.append({
                "team": team,
                "team_performance": {"attacking_efficiency": ae, "possession_danger_index": round(pdi, 2)},
                "betting_analytics": {"finishing_luck_index": fli, "defensive_luck_index": dli},
                "raw_data": {
                    "goals": data['goals'], "xg": round(data['xg'], 2),
                    "goals_conceded": data['goals_conceded'], "xga": round(data['xga'], 2),
                    "shots": data['shots'], "key_passes": data['key_passes']
                }
            })

        response.sort(key=lambda x: x["betting_analytics"]["finishing_luck_index"], reverse=True)
        return response

    except Exception as e:
        print(f"[ERRORE GRAVE TEAM METRICS] {e}")
        return []