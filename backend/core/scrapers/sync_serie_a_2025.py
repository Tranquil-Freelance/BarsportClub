import asyncio
import aiohttp
from sqlalchemy import select
from understat import Understat

# Importa il motore del database. 
# Verifica che "AsyncSessionLocal" sia il nome corretto usato in database.py
from app.db.database import AsyncSessionLocal
from app.db.models import Match

def safe_float(value):
    """Sanitizzazione maniacale per i decimali."""
    try:
        if value is None:
            return 0.0
        val = float(value)
        # Blocca i NaN e gli Inf
        if val != val or val == float('inf') or val == float('-inf'):
            return 0.0
        return val
    except (TypeError, ValueError):
        return 0.0

def safe_int(value):
    """Sanitizzazione per i numeri interi."""
    try:
        if value is None:
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0

async def sync_serie_a():
    print("⏳ Avvio sincronizzazione Serie A 2025/2026...")
    
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        # Scarichiamo la stagione corrente
        results = await understat.get_league_results("serie_a", 2025)
        
        print(f"✅ Scaricati {len(results)} risultati da Understat. Inizio salvataggio a DB...\n")
        
        async with AsyncSessionLocal() as db:
            added = 0
            updated = 0
            
            for match_data in results:
                u_id = safe_int(match_data.get('id'))
                if not u_id:
                    continue
                    
                # 1. Controlliamo se la partita esiste già nel DB
                stmt = select(Match).where(Match.understat_id == u_id)
                result = await db.execute(stmt)
                existing_match = result.scalars().first()
                
                # 2. Estrazione sicura dei dati da Understat
                h_team = match_data['h']['title']
                a_team = match_data['a']['title']
                h_goals = safe_int(match_data['goals']['h'])
                a_goals = safe_int(match_data['goals']['a'])
                h_xg = safe_float(match_data['xG']['h'])
                a_xg = safe_float(match_data['xG']['a'])
                is_comp = match_data.get('isResult') == True
                
                if existing_match:
                    # UPDATE: Modifichiamo l'oggetto in modo diretto. Nessun dizionario che può fallire.
                    existing_match.home_score = h_goals
                    existing_match.away_score = a_goals
                    existing_match.home_goals = h_goals
                    existing_match.away_goals = a_goals
                    existing_match.home_xG = h_xg
                    existing_match.away_xG = a_xg
                    existing_match.is_completed = is_comp
                    if is_comp:
                        existing_match.status = "concluso"
                    updated += 1
                else:
                    # CREATE: Creiamo un nuovo oggetto pulito
                    new_match = Match(
                        understat_id=u_id,
                        home_team=h_team,
                        away_team=a_team,
                        home_score=h_goals,
                        away_score=a_goals,
                        home_goals=h_goals,
                        away_goals=a_goals,
                        home_xG=h_xg,
                        away_xG=a_xg,
                        is_completed=is_comp,
                        status="concluso" if is_comp else "programmato",
                        is_scraped=False # Resta False finché non scaricheremo i tiri
                    )
                    db.add(new_match)
                    added += 1
                    
            # 3. Salvataggio in blocco
            await db.commit()
            print(f"🏆 Sincronizzazione completata! Partite aggiunte: {added} | Partite aggiornate: {updated}")

if __name__ == "__main__":
    asyncio.run(sync_serie_a())