import asyncio
import aiohttp
import random
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from understat import Understat
from aiohttp.client_exceptions import ClientResponseError

from app.db.database import AsyncSessionLocal
from app.db.models import Match, Shot, PlayerStat

# ==========================================
# IMPOSTAZIONI DI ESTRAZIONE
# ==========================================
LEGA = "serie_a"
STAGIONI = [2024, 2025] 

def safe_float(value):
    try:
        if value is None: return 0.0
        val = float(value)
        if val != val: return 0.0
        return val
    except: return 0.0

def safe_int(value):
    try:
        if value is None: return 0
        return int(value)
    except: return 0

async def run_total_scraper():
    print(f"🚀 AVVIO SCRAPER PURO (Senza AI): {LEGA.upper()}")
    
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        async with AsyncSessionLocal() as db:
            
            stmt = select(Match).where(
                Match.is_completed == True, 
                Match.is_scraped == False
            ).order_by(Match.id.asc())
            
            result = await db.execute(stmt)
            pending_matches = result.scalars().all()
            
            totale = len(pending_matches)
            if totale == 0:
                print("✅ Database aggiornato. Nessuna partita da scaricare.")
                return
                
            print(f"🎯 Partite da scaricare: {totale}")
            
            for index, m in enumerate(pending_matches, 1):
                u_id = int(m.id)
                print(f"[{index}/{totale}] ⏳ Download dati match ID {u_id}...")
                
                try:
                    match_shots = await understat.get_match_shots(u_id)
                    match_players = await understat.get_match_players(u_id)
                    
                    # Preparazione Tiri
                    shots_data = []
                    for team in ['h', 'a']:
                        for s in match_shots.get(team, []):
                            shots_data.append({
                                'match_id': u_id,
                                'minute': safe_int(s.get('minute')),
                                'player': s.get('player', 'N/D'),
                                'team_type': team,
                                'result': s.get('result', ''),
                                'xG': safe_float(s.get('xG')),
                                'X': safe_float(s.get('X')),
                                'Y': safe_float(s.get('Y')),
                                'situation': s.get('situation', '')
                            })
                    
                    # Preparazione Statistiche Giocatori
                    players_data = []
                    for team in ['h', 'a']:
                        for p_id, p in match_players.get(team, {}).items():
                            players_data.append({
                                'match_id': u_id,
                                'player_id': safe_int(p_id),
                                'player_name': p.get('player', 'N/D'),
                                'team_name': p.get('team_title', 'N/D'),
                                'team_type': team,
                                'key_passes': safe_int(p.get('key_passes')),
                                'goals': safe_int(p.get('goals')),
                                'xG': safe_float(p.get('xG')),
                                'time': safe_int(p.get('time'))
                            })

                    # Upsert Tiri
                    if shots_data:
                        await db.execute(insert(Shot).values(shots_data).on_conflict_do_nothing())
                    
                    # Upsert Giocatori
                    if players_data:
                        await db.execute(insert(PlayerStat).values(players_data).on_conflict_do_nothing())
                        
                    m.is_scraped = True
                    await db.commit()
                    print(f"  ✅ Dati salvati con successo.")
                    
                except ClientResponseError as e:
                    if e.status == 429:
                        print("🚨 Blocco Understat. Stop 30 min.")
                        await asyncio.sleep(1800)
                    else:
                        print(f"❌ Errore HTTP: {e}")
                except Exception as e:
                    print(f"❌ Errore Match {u_id}: {e}")
                    await db.rollback()
                
                await asyncio.sleep(random.uniform(1.5, 3.0))

if __name__ == "__main__":
    asyncio.run(run_total_scraper())