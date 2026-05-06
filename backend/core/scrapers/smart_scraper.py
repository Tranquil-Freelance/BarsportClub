import asyncio
import aiohttp
import random
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from understat import Understat

# Importa le configurazioni dal tuo progetto
from app.db.database import AsyncSessionLocal
from app.db.models import Match, Shot

def safe_float(value):
    try:
        if value is None:
            return 0.0
        val = float(value)
        if val != val or val == float('inf') or val == float('-inf'):
            return 0.0
        return val
    except (TypeError, ValueError):
        return 0.0

def safe_int(value):
    try:
        if value is None:
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0

async def run_smart_scraper():
    print("🤖 AVVIO SMART SCRAPER: Elaborazione massiva corazzata...")

    async with AsyncSessionLocal() as db:
        # Preleviamo le partite (senza mantenere gli oggetti aperti nel ciclo per evitare errori di sessione)
        stmt = select(Match.id, Match.understat_id, Match.home_team, Match.away_team).where(
            Match.is_completed == True, 
            Match.is_scraped == False
        ).order_by(Match.match_datetime.asc())
        
        result = await db.execute(stmt)
        pending_matches = result.all() # Prende solo i valori crudi, non gli oggetti ORM complessi

        totale = len(pending_matches)
        if totale == 0:
            print("✅ Nessuna partita in sospeso. Il database è aggiornato al 100%.")
            return

        print(f"🎯 Trovate {totale} partite da elaborare. Inizio ciclo...")

        async with aiohttp.ClientSession() as session:
            understat = Understat(session)

            for index, match_row in enumerate(pending_matches, 1):
                db_id = match_row.id
                u_id = match_row.understat_id
                match_name = f"{match_row.home_team} vs {match_row.away_team}"
                
                print(f"[{index}/{totale}] ⏳ Scaricamento tiri per: {match_name} (ID: {u_id})...")

                try:
                    match_shots = await understat.get_match_shots(u_id)
                    
                    # Raccogliamo tutti i tiri della partita
                    shots_data = []
                    for team_type in ['h', 'a']:
                        shots_list = match_shots.get(team_type, [])
                        for shot in shots_list:
                            shots_data.append({
                                'match_id': db_id,
                                'minute': safe_int(shot.get('minute')),
                                'player': shot.get('player', 'Sconosciuto'),
                                'xG': safe_float(shot.get('xG')),
                                'result': shot.get('result', 'Unknown'),
                                'team_type': team_type,
                                'X': safe_float(shot.get('X')),
                                'Y': safe_float(shot.get('Y')),
                                'situation': shot.get('situation', ''),
                                'shotType': shot.get('shotType', ''),
                                'assist': shot.get('player_assisted')
                            })

                    # Se ci sono tiri, facciamo un inserimento "a prova di bomba" (ON CONFLICT DO NOTHING)
                    if shots_data:
                        insert_stmt = insert(Shot).values(shots_data)
                        # Ignora la riga se viola il vincolo di unicità uq_shot_unique
                        do_nothing_stmt = insert_stmt.on_conflict_do_nothing(
                            index_elements=['match_id', 'minute', 'player', 'team_type']
                        )
                        await db.execute(do_nothing_stmt)

                    # Sigilliamo la partita ri-caricando l'oggetto per evitare problemi di sessione (MissingGreenlet)
                    match_to_update = await db.get(Match, db_id)
                    if match_to_update:
                        match_to_update.is_scraped = True
                    
                    await db.commit()
                    print(f"  ✅ Tiri salvati/ignorati duplicati. Partita sigillata.")

                except Exception as e:
                    await db.rollback()
                    print(f"  ❌ ERRORE sulla partita {match_name}: {e}")

                if index < totale:
                    ritardo = random.uniform(5.0, 15.0)
                    print(f"  💤 Pausa tattica di {ritardo:.2f} secondi...\n")
                    await asyncio.sleep(ritardo)

        print("\n🏆 SMART SCRAPING COMPLETATO CON SUCCESSO!")

if __name__ == "__main__":
    asyncio.run(run_smart_scraper())