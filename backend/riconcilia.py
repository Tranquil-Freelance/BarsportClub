import asyncio
import json
import tkinter as tk
from tkinter import filedialog
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Configurazione Database
DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/xpalermostat"

def estrai_tutti_i_match_bulldozer(testo_f):
    """
    Protocollo d'urgenza per file JSON corrotti o con dati extra.
    Scansiona il file carattere per carattere e recupera ogni oggetto match_id valido.
    """
    decoder = json.JSONDecoder()
    pos = 0
    match_recuperati = []
    
    print("🚜 Avvio scansione profonda del file... non ne lascerò indietro nessuno.")
    
    while pos < len(testo_f):
        # Salta spazi, virgole e parentesi quadre esterne tra un blocco e l'altro
        char = testo_f[pos]
        if char in (' ', '\n', '\r', '\t', ',', '[', ']'):
            pos += 1
            continue
            
        try:
            # Tenta di decodificare il prossimo oggetto JSON (lista o dizionario)
            obj, index = decoder.raw_decode(testo_f[pos:])
            
            if isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict) and "match_id" in item:
                        match_recuperati.append(item)
            elif isinstance(obj, dict) and "match_id" in obj:
                match_recuperati.append(obj)
                
            pos += index
        except json.JSONDecodeError:
            # Se trova un errore, avanza di un carattere e riprova la ricerca
            pos += 1
            
    return match_recuperati

async def esegui_iniezione_massiva():
    # 1. Selezione File
    root = tk.Tk()
    root.withdraw()
    print("👀 Seleziona il file JSON dalla finestra di Windows...")
    file_path = filedialog.askopenfilename(title="Seleziona il blocco Serie A")
    
    if not file_path:
        print("❌ Nessun file selezionato.")
        return

    # 2. Lettura e Parsing a Spallate
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            contenuto = f.read()
        
        lista_match = estrai_tutti_i_match_bulldozer(contenuto)
    except Exception as e:
        print(f"❌ Errore critico in lettura: {e}")
        return

    if not lista_match:
        print("❌ Il Bulldozer non ha trovato match validi nel file. Controlla il contenuto.")
        return

    print(f"🔥 RISULTATO: Trovati {len(lista_match)} match pronti per l'iniezione.")

    # 3. Iniezione nel Database
    engine = create_async_engine(DB_URL, isolation_level="AUTOCOMMIT")
    
    async with engine.connect() as conn:
        for i, m in enumerate(lista_match):
            m_id = m['match_id']
            shots = m.get('shots', {})
            rosters = m.get('rosters', {})
            
            # Identificazione squadre per log
            h_t = shots.get('h', [{}])[0].get('h_team', 'Home')
            a_t = shots.get('h', [{}])[0].get('a_team', 'Away')

            print(f"[*] [{i+1}/{len(lista_match)}] Iniezione Match {m_id}: {h_t} - {a_t}")

            # Pulizia e Iniezione Tiri
            await conn.execute(text("DELETE FROM shots WHERE match_id = :mid"), {"mid": int(m_id)})
            for side in ['h', 'a']:
                for s in shots.get(side, []):
                    await conn.execute(text("""
                        INSERT INTO shots (id, match_id, player, minute, team_type, situation, result, "xG", "X", "Y")
                        VALUES (:id, :mid, :p, :min, :tt, :sit, :res, :xg, :x, :y)
                        ON CONFLICT (id) DO NOTHING
                    """), {
                        "id": int(s['id']), "mid": int(m_id), "p": s['player'], "min": int(s['minute']),
                        "tt": side, "sit": s['situation'], "res": s['result'], "xg": float(s['xG']),
                        "x": float(s['X']), "y": float(s['Y'])
                    })

            # Iniezione Player Stats (La Polpa)
            await conn.execute(text("DELETE FROM player_stats WHERE match_id = :mid"), {"mid": int(m_id)})
            for side in ['h', 'a']:
                for p_id_key, p in rosters.get(side, {}).items():
                    await conn.execute(text("""
                        INSERT INTO player_stats (
                            match_id, player_id, player_name, team_type, team_name, 
                            shots, key_passes, "xG", "xA", "xGChain", "xGBuildup", goals, assists, time
                        ) VALUES (:mid, :pid, :pn, :tt, :tn, :s, :kp, :xg, :xa, :xgc, :xgb, :g, :a, :t)
                    """), {
                        "mid": int(m_id), "pid": int(p['player_id']), "pn": p['player'], "tt": side, "tn": h_t if side == 'h' else a_t,
                        "s": int(p['shots']), "kp": int(p['key_passes']), "xg": float(p['xG']),
                        "xa": float(p['xA']), "xgc": float(p['xGChain']), "xgb": float(p['xGBuildup']),
                        "g": int(p['goals']), "a": int(p['assists']), "t": int(p['time'])
                    })
            
            # Fine match
            await conn.execute(text("UPDATE matchcalendar SET is_scraped = True WHERE id = :mid"), {"mid": int(m_id)})

    print(f"\n✅ OPERAZIONE COMPLETATA. Tutti i {len(lista_match)} match sono ora nel database.")

if __name__ == "__main__":
    asyncio.run(esegui_iniezione_massiva())