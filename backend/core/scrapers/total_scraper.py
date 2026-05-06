import asyncio
import aiohttp
import random
import logging
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from understat import Understat
from aiohttp.client_exceptions import ClientResponseError

from app.db.database import AsyncSessionLocal
from app.db.models import Match, Shot, PlayerStat
# IMPORTIAMO IL TUO NUOVO MODULO AI
from meritometro_ai import generate_imr_verdict

# ==========================================
# IMPOSTAZIONI DI ESTRAZIONE
# ==========================================
LEGA = "serie_a"
STAGIONI = [2020, 2021, 2022, 2023, 2024, 2025] 

logger = logging.getLogger(__name__)

def safe_float(value):
    try:
        if value is None: return 0.0
        val = float(value)
        if val != val or val == float('inf') or val == float('-inf'): return 0.0
        return val
    except (TypeError, ValueError): return 0.0

def safe_int(value):
    try:
        if value is None: return 0
        return int(value)
    except (TypeError, ValueError): return 0

async def sync_matches(db, understat, lega, anno):
    """Sincronizza il calendario usando la manipolazione diretta degli oggetti."""
    print(f"\n📅 Sincronizzazione calendario {lega.upper()} - {anno}...")
    try:
        results = await understat.get_league_results(lega, anno)
        added = 0
        updated = 0
        
        for match_data in results:
            u_id = safe_int(match_data.get('id'))
            if not u_id: continue
                
            stmt = select(Match).where(Match.id == u_id) # Usiamo l'ID come chiave primaria
            result = await db.execute(stmt)
            existing = result.scalars().first()
            
            is_comp = match_data.get('isResult') == True
            
            if existing:
                existing.home_goals = safe_int(match_data['goals']['h'])
                existing.away_goals = safe_int(match_data['goals']['a'])
                existing.home_xG = safe_float(match_data['xG']['h'])
                existing.away_xG = safe_float(match_data['xG']['a'])
                existing.is_completed = is_comp
                updated += 1
            else:
                new_match = Match(
                    id=u_id,
                    home_team_id=0, # Andrà popolato con la logica dei team se necessaria
                    away_team_id=0, 
                    home_goals=safe_int(match_data['goals']['h']),
                    away_goals=safe_int(match_data['goals']['a']),
                    home_xG=safe_float(match_data['xG']['h']),
                    away_xG=safe_float(match_data['xG']['a']),
                    is_completed=is_comp,
                    round=safe_int(match_data.get('round', 0)),
                    is_scraped=False
                )
                db.add(new_match)
                added += 1
                
        await db.commit()
        print(f"✔️ Calendario {anno} allineato (Aggiunte: {added}, Aggiornate: {updated})")
    except Exception as e:
        print(f"❌ Errore durante sincronizzazione calendario {anno}: {e}")

async def run_total_scraper():
    print(f"🚀 AVVIO SCRAPER TOTALE: {LEGA.upper()} ({min(STAGIONI)}-{max(STAGIONI)})")
    print("🛡️ Sistema difensivo: ON (Jitter 5-15s | Ibernazione 30min su Errore 429 | Upsert ON CONFLICT DO NOTHING)\n")
    
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        
        async with AsyncSessionLocal() as db:
            # FASE 1: Aggiornamento calendari
            for anno in STAGIONI:
                await sync_matches(db, understat, LEGA, anno)
            
            # FASE 2: Estrazione Tiri e Giocatori
            print("\n🔬 INIZIO ESTRAZIONE PROFONDA + ANALISI AI (IMR)...")
            
            stmt = select(Match).where(
                Match.is_completed == True, 
                Match.is_scraped == False
            ).order_by(Match.id.asc())
            
            result = await db.execute(stmt)
            pending_matches = result.scalars().all()
            
            totale = len(pending_matches)
            if totale == 0:
                print("✅ Il database è aggiornato al 100%. Nessuna partita da processare.")
                return
                
            print(f"🎯 Partite in coda: {totale}")
            
            for index, m in enumerate(pending_matches, 1):
                u_id = m.id
                print(f"[{index}/{totale}] ⏳ Download e Analisi: Match ID {u_id}...")
                
                ciclo_completato = False
                while not ciclo_completato:
                    try:
                        match_shots = await understat.get_match_shots(u_id)
                        match_players = await understat.get_match_players(u_id)
                        
                        # --- CALCOLO IMR IN TEMPO REALE PER L'AI ---
                        imr_stats = {'h': {'occ': 0, 'area': 0, 'fuori': 0, 'kp': 0}, 
                                     'a': {'occ': 0, 'area': 0, 'fuori': 0, 'kp': 0}}

                        # Elaborazione Tiri
                        shots_to_save = []
                        for team_type in ['h', 'a']:
                            for s in match_shots.get(team_type, []):
                                xg_val = safe_float(s.get('xG'))
                                x_coord = safe_float(s.get('X'))
                                situation = s.get('situation', '')

                                if situation != 'Penalty':
                                    if xg_val >= 0.30: imr_stats[team_type]['occ'] += 1
                                    elif x_coord > 0.88: imr_stats[team_type]['area'] += 1
                                    else: imr_stats[team_type]['fuori'] += 1

                                shots_to_save.append({
                                    'match_id': u_id,
                                    'minute': safe_int(s.get('minute')),
                                    'player': s.get('player', 'N/D'),
                                    'xG': xg_val,
                                    'result': s.get('result', ''),
                                    'team_type': team_type,
                                    'X': x_coord, 'Y': safe_float(s.get('Y')),
                                    'situation': situation,
                                    'shotType': s.get('shotType', ''),
                                    'assist': s.get('player_assisted')
                                })
                        
                        # Elaborazione Giocatori e Key Passes
                        players_to_save = []
                        for team_type in ['h', 'a']:
                            for p_id, p in match_players.get(team_type, {}).items():
                                kp = safe_int(p.get('key_passes'))
                                imr_stats[team_type]['kp'] += kp
                                
                                players_to_save.append({
                                    'match_id': u_id,
                                    'player_id': safe_int(p_id),
                                    'player_name': p.get('player', 'N/D'),
                                    'team_name': p.get('team_title', 'N/D'),
                                    'team_type': team_type,
                                    'key_passes': kp,
                                    'goals': safe_int(p.get('goals')),
                                    'xG': safe_float(p.get('xG')),
                                    'xA': safe_float(p.get('xA')),
                                    'time': safe_int(p.get('time')),
                                    'position': p.get('position', '')
                                })

                        # Calcolo punteggio finale IMR
                        imr_h = (imr_stats['h']['occ']*5) + (imr_stats['h']['area']*3) + (imr_stats['h']['fuori']*1) + (imr_stats['h']['kp']*2)
                        imr_a = (imr_stats['a']['occ']*5) + (imr_stats['a']['area']*3) + (imr_stats['a']['fuori']*1) + (imr_stats['a']['kp']*2)

                        # --- CHIAMATA AI (DEEPSEEK) ---
                        print(f" 🤖 Generazione Verdetto AI per IMR: {imr_h} - {imr_a}...")
                        ai_data = {
                            "home_name": "Casa", "away_name": "Ospiti", # Nomi semplificati se non estratti
                            "home_score": m.home_goals, "away_score": m.away_goals,
                            "home_xg": m.home_xG, "away_xg": m.away_xG,
                            "home_imr": imr_h, "away_imr": imr_a
                        }
                        m.ai_verdict = generate_imr_verdict(ai_data)

                        # --- UPSERT DATI ---
                        if shots_to_save:
                            await db.execute(insert(Shot).values(shots_to_save).on_conflict_do_nothing(
                                index_elements=['match_id', 'minute', 'player', 'team_type', 'X', 'Y']
                            ))
                        if players_to_save:
                            await db.execute(insert(PlayerStat).values(players_to_save).on_conflict_do_nothing(
                                index_elements=['match_id', 'player_id']
                            ))
                            
                        m.is_scraped = True
                        await db.commit()
                        print(f" ✅ Partita archiviata con Verdetto AI.")
                        ciclo_completato = True
                        
                    except ClientResponseError as e:
                        if e.status == 429:
                            print("\n🚨 BLOCCO 429 - Ibernazione 30 min...")
                            await asyncio.sleep(1800)
                        else:
                            print(f" ❌ Errore HTTP: {e}")
                            ciclo_completato = True
                    except Exception as e:
                        await db.rollback()
                        print(f" ❌ Errore critico: {e}")
                        ciclo_completato = True
                
                # JITTER ANTI-BAN
                if index < totale:
                    ritardo = random.uniform(5.0, 15.0)
                    await asyncio.sleep(ritardo)

if __name__ == "__main__":
    asyncio.run(run_total_scraper())