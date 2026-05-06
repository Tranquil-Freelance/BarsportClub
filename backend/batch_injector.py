import os
import json
import re
import codecs
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# ==========================================
# CONFIGURAZIONE DATABASE PITCHLOGIX
# ==========================================
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/xpalermostat"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# PERCORSO CARTELLA
FOLDER_PATH = r"C:\Users\euron\Desktop\xpalermostat\backend\html_imports"

# MAPPA LEGHE CORRETTA (Corrispondenza esatta con i tuoi nomi file)
LEAGUE_MAP = {
    "serie a": 1, 
    "epl": 2, 
    "premier": 2, 
    "la liga": 3, 
    "bundesliga": 4, 
    "ligue 1": 5
}

def calc_ppda(ppda_dict):
    try:
        att = float(ppda_dict.get('att', 0))
        df = float(ppda_dict.get('def', 1))
        return round(att / df, 2) if df != 0 else 0.0
    except: return 0.0

async def get_or_create_team(db, team_name, team_id):
    """Garantisce l'esistenza della squadra nel DB."""
    res = await db.execute(text("SELECT id FROM team WHERE id = :id"), {"id": team_id})
    if res.fetchone(): return team_id
    await db.execute(text("INSERT INTO team (id, name) VALUES (:id, :n) ON CONFLICT DO NOTHING"), {"id": team_id, "n": team_name})
    await db.commit()
    return team_id

async def process_final():
    if not os.path.exists(FOLDER_PATH):
        print(f"❌ Cartella non trovata: {FOLDER_PATH}")
        return

    html_files = [f for f in os.listdir(FOLDER_PATH) if f.endswith(".html")]
    print(f"📂 Trovati {len(html_files)} file. Inizio elaborazione dei dati...")

    async with AsyncSessionLocal() as db:
        for file_name in html_files:
            # Rilevamento Lega
            l_id = 1 
            name_low = file_name.lower()
            for key, val in LEAGUE_MAP.items():
                if key in name_low:
                    l_id = val
                    break
            
            print(f"\n🔍 Analisi: {file_name} (Lega ID: {l_id})")
            
            try:
                with open(os.path.join(FOLDER_PATH, file_name), "r", encoding="utf-8") as f:
                    content = f.read()

                # REGEX MANIACALE: Punto solo a datesData per evitare teamsData o playersData
                match = re.search(r"datesData\s*=\s*JSON\.parse\(['\"](.+?)['\"]\)", content)
                if not match:
                    print(f"   ⚠️  Variabile 'datesData' non trovata. Controlla il CTRL+U.")
                    continue

                raw_data = match.group(1)
                decoded_data = codecs.decode(raw_data, 'unicode_escape')
                matches_json = json.loads(decoded_data)
                
                # Gestione struttura (Se Understat lo manda come dizionario, prendiamo i valori)
                if isinstance(matches_json, dict):
                    matches_list = list(matches_json.values())
                else:
                    matches_list = matches_json

                print(f"   ✅ Dati estratti ({len(matches_list)} match rilevati). Iniezione...")

                for m in matches_list:
                    # Salto le partite senza ID (sicurezza)
                    if not m.get('id'): continue

                    # Sincronizzazione Squadre
                    await get_or_create_team(db, m['h']['title'], int(m['h']['id']))
                    await get_or_create_team(db, m['a']['title'], int(m['a']['id']))
                    
                    # UPSERT (Aggiornamento massivo di tutte le metriche avanzate)
                    upsert_q = text("""
                        INSERT INTO matchcalendar (
                            id, league_id, home_team_id, away_team_id, home_goals, away_goals,
                            "home_xG", "away_xG", round, match_datetime, is_scraped, is_completed,
                            home_deep, away_deep, home_ppda, away_ppda, home_xpts, away_xpts
                        ) VALUES (
                            :id, :l_id, :h_id, :a_id, :hg, :ag, :hxg, :axg, :r, :dt, True, :comp,
                            :hd, :ad, :hp, :ap, :hx, :ax
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            home_goals = EXCLUDED.home_goals, away_goals = EXCLUDED.away_goals,
                            "home_xG" = EXCLUDED."home_xG", "away_xG" = EXCLUDED."away_xG",
                            home_deep = EXCLUDED.home_deep, away_deep = EXCLUDED.away_deep,
                            home_ppda = EXCLUDED.home_ppda, away_ppda = EXCLUDED.away_ppda,
                            home_xpts = EXCLUDED.home_xpts, away_xpts = EXCLUDED.away_xpts,
                            is_completed = EXCLUDED.is_completed
                    """)
                    
                    await db.execute(upsert_q, {
                        "id": int(m['id']), "l_id": l_id, "h_id": int(m['h']['id']), "a_id": int(m['a']['id']),
                        "hg": int(m['goals']['h']) if m['goals']['h'] is not None else 0,
                        "ag": int(m['goals']['a']) if m['goals']['a'] is not None else 0,
                        "hxg": float(m['xG']['h']) if m['xG']['h'] is not None else 0.0,
                        "axg": float(m['xG']['a']) if m['xG']['a'] is not None else 0.0,
                        "r": int(m['round']) if m.get('round') else 0,
                        "dt": m['datetime'], "comp": m['isResult'],
                        "hd": int(m['deep']['h']), "ad": int(m['deep']['a']),
                        "hp": calc_ppda(m['ppda']['h']), "ap": calc_ppda(m['ppda']['a']),
                        "hx": float(m['xpts']['h']), "ax": float(m['xpts']['a'])
                    })
                
                await db.commit()
                print(f"   🚀 Aggiornamento completato con successo.")

            except Exception as e:
                print(f"   🛑 Errore critico nel file {file_name}: {e}")

    print("\n🎯 PROCEDURA TERMINATA. Controlla ora il database.")

if __name__ == "__main__":
    asyncio.run(process_final())