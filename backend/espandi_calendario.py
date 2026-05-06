import asyncio
import aiohttp
import random
from datetime import datetime
from understat import Understat
from app.db.database import AsyncSessionLocal
from app.db.models import Match

# ==========================================
# CONFIGURAZIONE TARGET E MAPPATURA LEGHE
# ==========================================
LEAGUE_MAP = {
    "serie_a": 1,
    "EPL": 2,
    "la_liga": 3,
    "bundesliga": 4,
    "Ligue_1": 5
}

STAGIONI = [2020, 2021, 2022, 2023, 2024] 

async def espandi_archivio():
    print("🌍 INIZIO ESPANSIONE CALENDARI EUROPEI (MODALITÀ STEALTH)...")
    
    # Impostiamo un timeout per evitare che il programma resti appeso se Understat è lento
    timeout = aiohttp.ClientTimeout(total=60)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        understat = Understat(session)
        async with AsyncSessionLocal() as db:
            for lega_slug, lega_id in LEAGUE_MAP.items():
                for anno in STAGIONI:
                    print(f"⏳ Sincronizzazione {lega_slug.upper()} {anno}...")
                    try:
                        # Recupero dati
                        results = await understat.get_league_results(lega_slug, anno)
                        if not results:
                            print(f"⚠️ Nessun dato trovato per {lega_slug} {anno}.")
                            continue

                        count_added = 0
                        for m_data in results:
                            try:
                                u_id = int(m_data.get('id', 0))
                                if not u_id: continue
                                
                                # Verifichiamo se il match esiste già per non generare errori di duplicato
                                existing = await db.get(Match, u_id)
                                if existing: continue

                                # GESTIONE DATA (Manicale): Understat usa 'datetime'
                                raw_dt = m_data.get('datetime')
                                if raw_dt:
                                    dt_obj = datetime.strptime(raw_dt, '%Y-%m-%d %H:%M:%S')
                                else:
                                    dt_obj = datetime(anno, 1, 1) # Fallback se manca la data

                                # GESTIONE TEAM ID E ROUND
                                # Nota: Understat non manda 'round' qui, quindi lo mettiamo a 0
                                h_id = int(m_data.get('h', {}).get('id', 0))
                                a_id = int(m_data.get('a', {}).get('id', 0))
                                m_round = int(m_data.get('round', 0)) 

                                new_match = Match(
                                    id=u_id,
                                    league_id=lega_id,
                                    home_team_id=h_id,
                                    away_team_id=a_id,
                                    match_datetime=dt_obj,
                                    round=m_round,
                                    home_goals=int(m_data.get('goals', {}).get('h', 0)),
                                    away_goals=int(m_data.get('goals', {}).get('a', 0)),
                                    home_xG=float(m_data.get('xG', {}).get('h', 0.0)),
                                    away_xG=float(m_data.get('xG', {}).get('a', 0.0)),
                                    is_completed=True,
                                    is_scraped=False # Sarà scaricato poi con lo scraper dei tiri
                                )
                                db.add(new_match)
                                count_added += 1

                            except Exception as e_match:
                                # Se un singolo match fallisce, non fermiamo tutta la stagione
                                continue
                        
                        await db.commit()
                        print(f"✅ {lega_slug.upper()} {anno}: Aggiunti {count_added} match.")
                        
                        # ANTI-BAN: Pausa randomica tra una stagione e l'altra
                        pausa = random.uniform(4.0, 8.0)
                        print(f"💤 Pausa stealth di {pausa:.1f}s...")
                        await asyncio.sleep(pausa)

                    except Exception as e:
                        print(f"❌ Errore critico {lega_slug} {anno}: {e}")
                        await db.rollback()
                        # Se c'è un errore di rete (possibile ban temporaneo), aspettiamo di più
                        await asyncio.sleep(20)

if __name__ == "__main__":
    asyncio.run(espandi_archivio())