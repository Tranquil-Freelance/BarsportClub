import asyncio
import sys
import os
import logging
from datetime import datetime
from sqlalchemy import text

# Configurazione path per trovare i moduli dell'app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import AsyncSessionLocal
from app.scraper.sniper_protocol import sniper_strike

# Configurazione logging minimale
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SERIE_A_STRIKE")

async def serie_a_last_5_years():
    print("🇮🇹 [OPERAZIONE MIRATA] Recupero Serie A: Ultimi 5 Anni (2020-2025)")
    print("🚀 Conversione data in corso... Postgres ora sarà soddisfatto.")
    print("-" * 60)
    
    # Definiamo il range: dalla stagione 2020 alla 2025
    SEASONS = [str(year) for year in range(2020, 2026)]
    
    # Trasformiamo la stringa in un oggetto datetime reale
    start_date_obj = datetime(2020, 8, 1)
    
    for season in SEASONS:
        async with AsyncSessionLocal() as session:
            # Query SQL pura: il parametro :start_date ora riceve un oggetto datetime
            stmt = text("""
                SELECT id FROM matchcalendar 
                WHERE league_id = 1 
                AND is_completed = True 
                AND is_scraped = False
                AND match_datetime >= :start_date
            """)
            
            res = await session.execute(stmt, {"start_date": start_date_obj})
            match_ids = [row[0] for row in res.fetchall()]
            
            if not match_ids:
                print(f"✅ Stagione {season} già allineata o nessun match trovato.")
                continue

            print(f"🎯 Stagione {season}: Trovati {len(match_ids)} match mancanti.")

            for m_id in match_ids:
                try:
                    async with AsyncSessionLocal() as sub_session:
                        print(f"📡 Recupero Match ID: {m_id} (Stagione {season})")
                        
                        # Il cecchino scarica i tiri e le stats dei giocatori
                        await sniper_strike(sub_session, str(m_id), f"Serie A {season}")
                        
                        # Aggiornamento dello stato 'is_scraped'
                        await sub_session.execute(
                            text("UPDATE matchcalendar SET is_scraped = True WHERE id = :id"),
                            {"id": m_id}
                        )
                        await sub_session.commit()
                        print(f"✅ ID {m_id} archiviato correttamente.")
                        
                except Exception as e:
                    print(f"⚠️ Errore Match {m_id}: {e}")
                    continue
                
                # Respiro di sicurezza (Jitter aggiuntivo)
                await asyncio.sleep(0.8)

    print("\n" + "="*60)
    print("🏆 OBIETTIVO RAGGIUNTO: Serie A recente è nel database.")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(serie_a_last_5_years())