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
    """Recupera i dati simulando un browser reale"""
    url = f"{BASE_URL}/match/{match_id}"
    try:
        # Impersonificazione Chrome 110: fondamentale per non farsi resettare la connessione
        resp = session.get(url, impersonate="chrome110", timeout=30)
        
        if resp.status_code == 403:
            print(f"🚫 [403] Understat ha rilevato troppe richieste. Fermarsi subito.")
            return "BLOCK"
        if resp.status_code != 200:
            print(f"⚠️ Match {match_id} non trovato (Status {resp.status_code})")
            return None
        
        html = resp.text
        shots_match = re.search(r"var shotsData\s*=\s*JSON\.parse\('(.+?)'\)", html)
        rosters_match = re.search(r"var rostersData\s*=\s*JSON\.parse\('(.+?)'\)", html)
        
        if shots_match and rosters_match:
            # Controllo se la partita ha effettivamente dei dati dentro
            if len(shots_match.group(1)) < 20: 
                return "EMPTY"

            def decode(data):
                return json.loads(bytes(data, "utf-8").decode("unicode_escape"))
            
            return {
                "match_id": match_id,
                "shots": decode(shots_match.group(1)),
                "rosters": decode(rosters_match.group(1))
            }
    except Exception as e:
        print(f"❌ Errore critico su match {match_id}: {e}")
    return None

async def run_serie_a_recovery():
    engine = create_async_engine(DB_URL, isolation_level="AUTOCOMMIT")
    
    # MODIFICA MANIACALE: 
    # 1. Solo Serie A
    # 2. Solo partite passate (almeno 3 ore fa)
    # 3. Solo partite che NON hanno dati evoluti (xA > 0)
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT m.id 
            FROM matchcalendar m
            JOIN league l ON m.league_id = l.id
            WHERE l.name ILIKE '%Serie A%'
              AND m.match_datetime < NOW() - INTERVAL '3 hours'
              AND m.is_scraped = False
            ORDER BY m.match_datetime DESC
            LIMIT 50
        """))
        match_ids = [r[0] for r in res]

    if not match_ids:
        print("🎯 Nessuna partita di Serie A da recuperare. Database già pulito e pieno.")
        return

    print(f"🚀 RECUPERO SERIE A: Analisi di {len(match_ids)} partite passate...")
    print("⏲️ Modalità: Notturna Lenta (15-25 secondi di pausa)")

    with requests.Session() as session:
        for i, m_id in enumerate(match_ids):
            print(f"[*] [{i+1}/{len(match_ids)}] Scaricando Match ID: {m_id}...")
            
            data = await fetch_match_data(session, m_id)
            
            if data == "BLOCK":
                print("🛑 Ban rilevato! Spegnere tutto e cambiare IP o aspettare 1 ora.")
                break
            
            if data == "EMPTY":
                print(f"⚠️ Match {m_id} è un guscio vuoto (dati non ancora pronti).")
                continue

            if data:
                async with engine.connect() as conn:
                    # Pulizia preventiva per evitare duplicati sporchi
                    await conn.execute(text("DELETE FROM shots WHERE match_id = :m"), {"m": m_id})
                    await conn.execute(text("DELETE FROM player_stats WHERE match_id = :m"), {"m": m_id})
                    
                    # 1. Inserimento Tiri
                    for side in ['h', 'a']:
                        for s in data['shots'].get(side, []):
                            await conn.execute(text("""
                                INSERT INTO shots (id, match_id, player, minute, team_type, situation, result, "xG", "X", "Y")
                                VALUES (:id, :m_id, :p, :min, :tt, :sit, :res, :xg, :x, :y)
                            """), {
                                "id": int(s['id']), "m_id": m_id, "p": s['player'], "min": int(s['minute']),
                                "tt": side, "sit": s['situation'], "res": s['result'], "xg": float(s['xG']),
                                "x": float(s['X']), "y": float(s['Y'])
                            })

                    # 2. Inserimento Statistiche Giocatori (xA, xGChain, xGBuildup)
                    for side in ['h', 'a']:
                        for pid, p in data['rosters'].get(side, {}).items():
                            await conn.execute(text("""
                                INSERT INTO player_stats (
                                    match_id, player_id, player_name, team_type, team_name, 
                                    shots, key_passes, "xG", "xA", "xGChain", "xGBuildup", goals, assists, time
                                ) VALUES (:mid, :pid, :pn, :tt, :tn, :s, :kp, :xg, :xa, :xgc, :xgb, :g, :a, :t)
                            """), {
                                "mid": m_id, "pid": int(p['player_id']), "pn": p['player'], "tt": side, "tn": "Serie A Recovery",
                                "s": int(p['shots']), "kp": int(p['key_passes']), "xg": float(p['xG']),
                                "xa": float(p['xA']), "xgc": float(p['xGChain']), "xgb": float(p['xGBuildup']),
                                "g": int(p['goals']), "a": int(p['assists']), "t": int(p['time'])
                            })
                    
                    # Conferma scraping completato
                    await conn.execute(text("UPDATE matchcalendar SET is_scraped = True WHERE id = :mid"), {"mid": m_id})
                
                print(f"✅ Match {m_id} archiviato con successo.")

            # --- RITARDO MANIACALE PER LA SICUREZZA ---
            wait_time = random.uniform(15.0, 25.0)
            print(f"⏲️ Attesa cautelativa: {wait_time:.1f}s...")
            await asyncio.sleep(wait_time)

    print("\n🎯 FINE SESSIONE. Controlla il Meritometro.")

if __name__ == "__main__":
    asyncio.run(run_serie_a_recovery())