"""
Analytics API routes and helper functions for extracting shot data from Understat HTML.
"""
import json
import re
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.endpoints import get_match_shots_rest


def _extract_shots_json(html: str) -> Dict[str, Any]:
    # Questa Regex ora cerca in modo molto più flessibile (spazi, apici, virgolette)
    match = re.search(r"shotsData\s*=\s*JSON\.parse\(['\"](.+?)['\"]\)", html, re.DOTALL)
    
    if not match:
        # Stampiamo l'inizio dell'HTML nel terminale per vedere cosa ci manda Understat
        print("--- DEBUG HTML RICEVUTO (Primi 500 caratteri) ---")
        print(html[:500])
        print("------------------------------------------------")
        raise ValueError("Understat ha risposto, ma i dati dei tiri sono protetti o mancanti.")

    raw_json = match.group(1)
    # Decodifica robusta
    try:
        decoded = raw_json.encode('utf-8').decode('unicode_escape')
        return json.loads(decoded)
    except:
        # Se la decodifica fallisce, proviamo il metodo grezzo
        return json.loads(raw_json.replace('\\x', '\\u00'))


router = APIRouter()


@router.get("/match/{match_id}/shots")
async def get_match_shots(
    match_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint compatibile con il frontend esistente.
    Delegata alla funzione già definita in endpoints.py.
    """
    return await get_match_shots_rest(match_id, db)