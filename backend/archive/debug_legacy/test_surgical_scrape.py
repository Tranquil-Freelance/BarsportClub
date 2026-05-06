import asyncio
import aiohttp
from sqlalchemy import select
from understat import Understat

# Importa le configurazioni dal tuo progetto
from app.db.database import AsyncSessionLocal
from app.db.models import Match, Shot

def safe_float(value):
    """Sanitizzazione maniacale per i decimali (xG, X, Y)."""
    try:
        if value is None:
            return 0.0
        val = float(value)
        # Blocca i NaN e gli Inf matematici
        if val != val or val == float('inf') or val == float('-inf'):
            return 0.0
        return val
    except (TypeError, ValueError):
        return 0.0

def safe_int(value):
    """Sanitizzazione per i numeri interi (minuti, ID)."""
    try:
        if value is None:
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0

async def test_surgical_scrape():
    print("🔬 INIZIO TEST CHIRURGICO: Scraping tiri di una singola partita...")

    async with AsyncSessionLocal() as db:
        # 1. Isoliamo un singolo bersaglio dal database
        stmt = select(Match).where(
            Match.is_completed == True, 
            Match.is_scraped == False
        ).limit(1)
        
        result = await db.execute(stmt)
        target_match = result.scalars().first()

        if not target_match:
            print("❌ Nessuna partita trovata da processare (tutte già elaborate o nessuna completata).")
            return

        u_id = target_match.understat_id
        db_id = target_match.id
        print(f"🎯 Bersaglio acquisito: Partita DB_ID {db_id} | Understat_ID {u_id} ({target_match.home_team} vs {target_match.away_team})")

        # 2. Estrazione dati crudi da Understat
        async with aiohttp.ClientSession() as session:
            understat = Understat(session)
            try:
                print("⏳ Connessione a Understat in corso...")
                match_shots = await understat.get_match_shots(u_id)
            except Exception as e:
                print(f"❌ Errore di connessione a Understat: {e}")
                return

        print("✅ Dati grezzi scaricati. Inizio sanitizzazione e inserimento nella tabella 'shots'...")

        shots_added = 0
        
        # 3. Costruzione sicura degli oggetti Shot
        for team_type in ['h', 'a']:
            shots_list = match_shots.get(team_type, [])
            for shot_data in shots_list:
                new_shot = Shot(
                    match_id=db_id,
                    minute=safe_int(shot_data.get('minute')),
                    player=shot_data.get('player', 'Sconosciuto'),
                    xG=safe_float(shot_data.get('xG')),
                    result=shot_data.get('result', 'Unknown'),
                    team_type=team_type,
                    X=safe_float(shot_data.get('X')),
                    Y=safe_float(shot_data.get('Y')),
                    situation=shot_data.get('situation', ''),
                    shotType=shot_data.get('shotType', ''),
                    assist=shot_data.get('player_assisted')
                )
                db.add(new_shot)
                shots_added += 1

        # 4. Sigilliamo la partita e salviamo tutto
        target_match.is_scraped = True
        
        try:
            await db.commit()
            print(f"🏆 TEST SUPERATO! Inseriti {shots_added} tiri nel database.")
            print(f"🔒 Partita {u_id} aggiornata a is_scraped = True.")
        except Exception as e:
            await db.rollback()
            print(f"❌ ERRORE CRITICO DURANTE IL SALVATAGGIO A DB: {e}")

if __name__ == "__main__":
    asyncio.run(test_surgical_scrape())