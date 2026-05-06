from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import math

from app.db.database import get_db
from app.db.models import Match, Shot, PlayerStat

router = APIRouter()

# Funzione di pulizia numeri (sostituisce quella che importava da crud)
def clean_float(val):
    if val is None: return 0.0
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f): return 0.0
        return f
    except:
        return 0.0

@router.get("/matches/{match_id}/shots")
async def get_match_shots_rest(match_id: int, db: AsyncSession = Depends(get_db)):
    """Restituisce tutti i tiri di una partita specifica."""
    stmt = select(Shot).where(Shot.match_id == match_id)
    result = await db.execute(stmt)
    shots = result.scalars().all()
    
    if not shots:
        match_exists = await db.get(Match, match_id)
        if not match_exists:
            raise HTTPException(status_code=404, detail="Partita non trovata")
        return []

    return [
        {
            "id": s.id,
            "minute": s.minute,
            "player": s.player,
            "xG": clean_float(s.xG),
            "result": s.result,
            "team": s.team_type,
            "X": clean_float(s.X),
            "Y": clean_float(s.Y)
        } for s in shots
    ]

@router.get("/matches/{match_id}/players")
async def get_match_player_stats(match_id: int, db: AsyncSession = Depends(get_db)):
    """Restituisce le statistiche dei giocatori per una partita."""
    stmt = select(PlayerStat).where(PlayerStat.match_id == match_id)
    result = await db.execute(stmt)
    stats = result.scalars().all()
    return stats

@router.get("/matches/{match_id}/details")
async def get_match_details(match_id: int, db: AsyncSession = Depends(get_db)):
    """Restituisce i dettagli completi di una partita, inclusi tiri e statistiche giocatori."""
    try:
        # 1. Recupera la partita dal nostro modello corazzato
        match = await db.get(Match, match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Partita non trovata")
        
        # 2. Traduzione Nomi Squadre (SQL puro, nessun rischio di crash da joinedload)
        teams_dict = {}
        try:
            teams_result = await db.execute(text("SELECT id, name FROM team"))
            for row in teams_result.fetchall():
                teams_dict[row[0]] = str(row[1])
        except:
            pass
            
        home_name = teams_dict.get(match.home_team_id, f"Squadra {match.home_team_id}") if match.home_team_id else "N/D"
        away_name = teams_dict.get(match.away_team_id, f"Squadra {match.away_team_id}") if match.away_team_id else "N/D"

        # 3. Recupera i tiri
        shots_stmt = select(Shot).where(Shot.match_id == match_id)
        shots_result = await db.execute(shots_stmt)
        shots = shots_result.scalars().all()
        
        # 4. Recupera statistiche giocatori
        player_stats_stmt = select(PlayerStat).where(PlayerStat.match_id == match_id)
        player_stats_result = await db.execute(player_stats_stmt)
        player_stats = player_stats_result.scalars().all()

        # 5. Costruzione del payload per il frontend
        match_data = {
            "id": match.id,
            "home_team": home_name,
            "away_team": away_name,
            "home_score": getattr(match, 'home_goals', 0),
            "away_score": getattr(match, 'away_goals', 0),
            "home_xG": clean_float(getattr(match, 'home_xG', 0.0)),
            "away_xG": clean_float(getattr(match, 'away_xG', 0.0)),
            "match_datetime": match.match_datetime,
            "status": "FT" if getattr(match, 'is_completed', False) else "Pre",
            "round": getattr(match, 'round', 0)
        }

        shots_data = [
            {
                "minute": s.minute,
                "xG": clean_float(s.xG),
                "team": s.team_type,
                "player": s.player,
                "result": s.result,
                "X": clean_float(s.X),
                "Y": clean_float(s.Y),
                "situation": s.situation,
                "shotType": s.shotType,
                "lastAction": s.lastAction,
            }
            for s in shots
        ]

        return {
            "match": match_data,
            "shots": shots_data,
            "player_stats": [] # Lo lasciamo vuoto per ora per non appesantire la Timing Chart
        }

    except Exception as e:
        print(f"[ERRORE DETTAGLIO MATCH] {e}")
        raise HTTPException(status_code=500, detail="Errore interno al server")