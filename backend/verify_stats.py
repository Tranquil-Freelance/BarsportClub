import asyncio
import json
import re
import random
from curl_cffi import requests
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Configurazione Database
DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/xpalermostat"
BASE_URL = "https://understat.com"

async def fetch_match_data(session, match_id):
    url = f"{BASE_URL}/match/{match_id}"
    try:
        # Impersonificazione Chrome per mimetizzazione totale
        resp = session.get(url, impersonate="chrome110", timeout=30)
        
        if resp.status_code == 403:
            print(f"🚫 [403] Rilevato. Pausa necessaria.")
            return "BLOCK"
        if resp.status_code != 200:
            return None
        
        html = resp.text
        shots_match = re.search(r"var shotsData\s*=\s*JSON\.parse\('(.+?)'\)", html)
        rosters_match = re.search(r"var rostersData\s*=\s*JSON\.parse\('(.+?)'\)", html)
        
        if shots_match and rosters_match:
            def decode(data):
                return json.loads(bytes(data, "utf-8").decode("unicode_escape"))
            return {
                "match_id": match_id,
                "shots": decode(shots_match.group(1)),
                "rosters": decode(rosters_match.group(1))
            }
    except Exception as e:
        print(f"❌ Errore fetch {match_id}: {e}")
    return None

async def run_next_batch():
    engine = create_async_engine(DB_URL, isolation_level="AUTOCOMMIT")
    
    # Selezioniamo i prossimi 40 match di Serie A non ancora completi di dati evoluti
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT m.id 
            FROM matchcalendar m
            JOIN league l ON m.league_id = l.id
            WHERE l.name ILIKE '%Serie A%'
              AND m.match_datetime < NOW()
              AND m.id NOT IN (
                  SELECT DISTINCT match_id FROM player_stats WHERE "xA" > 0
              )
            ORDER BY m.match_datetime DESC
            LIMIT 40
        """))
        match_ids = [r[0] for r in res]

    if not match_ids:
        print("🎯 Nessuna partita di Serie A da aggiornare trovata.")
        return

    print(f"🚀 AGGIORNAMENTO SERIE A: Elaborazione di {len(match_ids)} partite...")

    with requests.Session() as session:
        for i, m_id in enumerate(match_ids):
            print(f"[*] [{i+1}/{len(match_ids)}] Elaborazione Match ID: {m_id}...")
            
            data = await fetch_match_data(session, m_id)
            
            if data == "BLOCK":
                print("🛑 Blocco rilevato. Interrompo per sicurezza.")
                break

            if data:
                async with engine.connect() as conn:
                    # 1. UPSERT TIRI
                    for side in ['h', 'a']:
                        for s in data['shots'].get(side, []):
                            await conn.execute(text("""
                                INSERT INTO shots (id, match_id, player, minute, team_type, situation, result, "xG", "X", "Y")
                                VALUES (:id, :m_id, :p, :min, :tt, :sit, :res, :xg, :x, :y)
                                ON CONFLICT (id) DO NOTHING
                            """), {
                                "id": int(s['id']), "m_id": m_id, "p": s['player'], "min": int(s['minute']),
                                "tt": side, "sit": s['situation'], "res": s['result'], "xg": float(s['xG']),
                                "x": float(s['X']), "y": float(s['Y'])
                            })

                    # 2. INIEZIONE STATISTICHE TOTALI (Tutti i dati Understat)
                    for side in ['h', 'a']:
                        for pid, p in data['rosters'].get(side, {}).items():
                            await conn.execute(text("DELETE FROM player_stats WHERE match_id = :mid AND player_id = :pid"), 
                                             {"mid": m_id, "pid": int(p['player_id'])})
                            
                            await conn.execute(text("""
                                INSERT INTO player_stats (
                                    match_id, player_id, player_name, team_type, team_name, 
                                    shots, key_passes, "xG", "xA", "xGChain", "xGBuildup", 
                                    goals, assists, time
                                ) VALUES (
                                    :mid, :pid, :pn, :tt, :tn, 
                                    :s, :kp, :xg, :xa, :xgc, :xgb, 
                                    :g, :a, :t
                                )
                            """), {
                                "mid": m_id, "pid": int(p['player_id']), "pn": p['player'], "tt": side, "tn": "Serie A Update",
                                "s": int(p['shots']), "kp": int(p['key_passes']), "xg": float(p['xG']),
                                "xa": float(p['xA']), "xgc": float(p['xGChain']), "xgb": float(p['xGBuildup']),
                                "g": int(p['goals']), "a": int(p['assists']), "t": int(p['time'])
                            })
                    
                    await conn.execute(text("UPDATE matchcalendar SET is_scraped = True WHERE id = :mid"), {"mid": m_id})
                print(f"✅ Dati completi inseriti per il match {m_id}.")

            # Ritardo Jitter tra 12 e 20 secondi per la massima sicurezza
            wait_time = random.uniform(12.0, 20.0)
            print(f"⏲️ Pausa di sicurezza: {wait_time:.1f}s...")
            await asyncio.sleep(wait_time)

    print("\n🎯 SESSIONE COMPLETATA. 40 partite aggiornate con dati evoluti.")

if __name__ == "__main__":
    asyncio.run(run_next_batch())