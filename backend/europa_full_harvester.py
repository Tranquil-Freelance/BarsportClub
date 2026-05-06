import asyncio
import sys
import os
import logging
from sqlalchemy import text

# Configurazione path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import AsyncSessionLocal
from app.scraper.sniper_protocol import sniper_strike
from app.scraper.sync_calendar import sync_league_calendar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EUROPA_HARVESTER")

# 5 Leghe, 5 Anni, 1 solo obiettivo: Dati Integrali
LEAGUES = [
    ('Serie_A', 1),
    ('EPL', 2),
    ('La_liga', 3),
    ('Bundesliga', 4),
    ('Ligue_1', 5)
]

# Copriamo dal 2020 ad oggi
SEASONS = [2020, 2021, 2022, 2023, 2024, 2025]

async def mass_harvest():
    print("🌍 [OPERAZIONE EUROPA] Sincronizzazione e Scraping Totale (2020-2025)")
    print("🚀 Questo script popolerà i calendari mancanti e scaricherà ogni singolo tiro.")
    print("-" * 70)

    for league_slug, league_id in LEAGUES:
        for season in SEASONS:
            async with AsyncSessionLocal() as session:
                print(f"\n📂 Elaborazione: {league_slug} | Stagione: {season}")
                
                # FASE 1: Sincronizzazione Calendario (Livello 1)
                # Crea i match mancanti nel database se non esistono
                try:
                    await sync_league_calendar(session, league_slug, season, league_id)
                    await session.commit()
                except Exception as e:
                    print(f"⚠️ Errore sync calendario {league_slug} {season}: {e}")
                    await session.rollback()

                # FASE 2: Recupero ID match da processare (is_scraped = False)
                # Qui includerà sia le 80 della Serie A che tutte quelle degli anni passati
                res = await session.execute(text("""
                    SELECT id FROM matchcalendar 
                    WHERE league_id = :l_id 
                    AND is_completed = True 
                    AND is_scraped = False
                """), {"l_id": league_id})
                match_ids = [row[0] for row in res.fetchall()]

                if not match_ids:
                    print(f"✨ {league_slug} {season}: Già completa.")
                    continue

                print(f"🎯 Trovati {len(match_ids)} match da scaricare. Avvio Sniper...")

                for m_id in match_ids:
                    try:
                        # Usiamo una sessione fresca per ogni match per isolare i fallimenti
                        async with AsyncSessionLocal() as sub_session:
                            # Il Sniper scarica tiri (con shotType, assist, coordinate) e stats giocatori
                            await sniper_strike(sub_session, str(m_id), f"{league_slug} {season}")
                            
                            # Update chirurgico dello stato
                            await sub_session.execute(
                                text("UPDATE matchcalendar SET is_scraped = True WHERE id = :id"),
                                {"id": m_id}
                            )
                            await sub_session.commit()
                            print(f"✅ Match {m_id} archiviato.")
                    except Exception as e:
                        print(f"⚠️ Salto Match {m_id} per errore: {e}")
                        continue
                    
                    # Pausa tecnica per rispettare il server
                    await asyncio.sleep(0.5)

    print("\n" + "="*70)
    print("🏆 ARCHIVIO EUROPEO COMPLETATO. Il database è ora una miniera d'oro.")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(mass_harvest())