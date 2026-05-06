import asyncio
import logging
from sqlalchemy import select, func
# Cambiato l'import per puntare al file corretto nel tuo progetto
from app.db.database import AsyncSessionLocal 
from app.db.models import Match, Shot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DB_CHECK")

async def check_integrity():
    try:
        async with AsyncSessionLocal() as session:
            print("\n" + "="*50)
            print("🔍 REPORT DI INTEGRITÀ xPALERMOSTAT")
            print("="*50)

            # 1. Controllo Match
            match_count = await session.execute(select(func.count(Match.id)))
            total_matches = match_count.scalar()
            print(f"🏟️  Totale Match nel DB: {total_matches}")

            # 2. Controllo Shots
            shot_count = await session.execute(select(func.count(Shot.id)))
            total_shots = shot_count.scalar()
            print(f"⚽ Totale Shots nel DB: {total_shots}")

            # 3. Verifica Nuove Colonne (Maniacale)
            # Verifichiamo se le colonne esistono e sono popolate
            try:
                null_scores = await session.execute(
                    select(func.count(Match.id)).where(Match.home_score == None)
                )
                total_null_scores = null_scores.scalar()
                
                null_dates = await session.execute(
                    select(func.count(Match.id)).where(Match.date == None)
                )
                total_null_dates = null_dates.scalar()

                print(f"\n📊 STATO NUOVE COLONNE:")
                print(f"❌ Match senza Risultato (home_score): {total_null_scores}")
                print(f"❌ Match senza Data: {total_null_dates}")
            except Exception as e:
                print(f"\n⚠️  ERRORE COLONNE: Le nuove colonne (home_score/date) non esistono ancora nel DB.")
                print(f"   Dettaglio: {e}")
                total_null_scores = -1

            # 4. Analisi di un Match Campione
            if total_matches > 0:
                sample_match = await session.execute(select(Match).limit(1))
                m = sample_match.scalar()
                
                # Conta tiri per questo match
                m_shots = await session.execute(
                    select(func.count(Shot.id)).where(Shot.match_id == m.id)
                )
                count_m_shots = m_shots.scalar()

                print(f"\n🧪 TEST CAMPIONE (Match ID: {m.id}):")
                print(f"   {m.home_team} vs {m.away_team}")
                try:
                    print(f"   Risultato nel DB: {m.home_score}-{m.away_score}")
                    print(f"   Data nel DB: {m.date}")
                except:
                    print("   Risultato/Data: Colonne non trovate nel database fisico.")
                print(f"   Tiri collegati: {count_m_shots}")

            print("="*50 + "\n")

    except Exception as e:
        print(f"❌ ERRORE CRITICO DI CONNESSIONE: {e}")

if __name__ == "__main__":
    asyncio.run(check_integrity())