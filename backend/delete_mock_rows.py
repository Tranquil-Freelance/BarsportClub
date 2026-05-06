import asyncio
import json
import os
import re
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/xpalermostat"

async def inietta_dati_puliti():
    # Il percorso ora punta dritto alla cartella corretta
    file_path = os.path.join("html_imports", "serieaultimagiornata.json")
    
    if not os.path.exists(file_path):
        print(f"❌ Errore critico: Il file {file_path} non si trova al suo posto. Controlla la cartella.")
        return

    # 1. Lettura maniacale e pulizia sintassi JSON (risolve l'errore di incollaggio multiplo)
    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Correggiamo gli array uniti male (sostituisce i blocchi attaccati ][ con una virgola ,)
    fixed_text = re.sub(r'\]\s*\[', ',', raw_text)

    try:
        matches = json.loads(fixed_text)
    except json.JSONDecodeError as e:
        print(f"❌ Errore residuo nel JSON: {e}")
        return

    engine = create_async_engine(DB_URL, isolation_level="AUTOCOMMIT")
    
    async with engine.connect() as conn:
        print(f"🚀 Inizio iniezione e pulizia per {len(matches)} blocchi trovati nel file...")

        match_processati = set()
        
        for m in matches:
            m_id = int(m['match_id'])
            
            # 2. Controllo Ripetizioni (salta il doppio copia-incolla del Genoa o futuri errori)
            if m_id in match_processati:
                print(f"⚠️ Salto il Match ID {m_id} perché è un duplicato nel file.")
                continue
                
            match_processati.add(m_id)
            print(f"[*] Iniezione Match ID: {m_id}...")

            # --- TIRI (LOGICA UPSERT: ON CONFLICT DO NOTHING) ---
            for side in ['h', 'a']:
                for s in m.get('shots', {}).get(side, []):
                    await conn.execute(text("""
                        INSERT INTO shots (id, match_id, player, minute, team_type, situation, result, "xG", "X", "Y")
                        VALUES (:id, :m_id, :p, :min, :tt, :sit, :res, :xg, :x, :y)
                        ON CONFLICT (id) DO NOTHING
                    """), {
                        "id": int(s['id']), "m_id": m_id, "p": s['player'], "min": int(s['minute']),
                        "tt": side, "sit": s['situation'], "res": s['result'], "xg": float(s['xG']),
                        "x": float(s['X']), "y": float(s['Y'])
                    })

            # --- GIOCATORI ---
            for side in ['h', 'a']:
                for pid, p in m.get('rosters', {}).get(side, {}).items():
                    await conn.execute(text("DELETE FROM player_stats WHERE match_id = :mid AND player_id = :pid"), 
                                     {"mid": m_id, "pid": int(p['player_id'])})
                    
                    await conn.execute(text("""
                        INSERT INTO player_stats (match_id, player_id, player_name, team_type, team_name, shots, key_passes, "xG")
                        VALUES (:mid, :pid, :pn, :tt, :tn, :s, :kp, :xg)
                    """), {
                        "mid": m_id, "pid": int(p['player_id']), "pn": p['player'], "tt": side,
                        "tn": "N/D",
                        "s": int(p['shots']), "kp": int(p['key_passes']), "xg": float(p['xG'])
                    })

            # --- SBLOCCO CALENDARIO ---
            await conn.execute(text("UPDATE matchcalendar SET is_scraped = True WHERE id = :mid"), {"mid": m_id})

    print(f"🎯 INIEZIONE COMPLETATA. {len(match_processati)} partite uniche caricate con successo. Il Meritometro è aggiornato.")

if __name__ == "__main__":
    asyncio.run(inietta_dati_puliti())