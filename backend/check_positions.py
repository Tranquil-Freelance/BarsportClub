import os
import json
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# ==========================================
# CONFIGURAZIONE DATABASE PITCHLOGIX
# ==========================================
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/xpalermostat"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# PERCORSO CARTELLA (Confermato dal tuo screenshot)
FOLDER_PATH = r"C:\Users\euron\Desktop\xpalermostat\backend\html_imports"

def calc_ppda(ppda_dict):
    """Calcola il PPDA dal dizionario {att: x, def: y}"""
    try:
        if not ppda_dict: return 0.0
        att = float(ppda_dict.get('att', 0))
        df = float(ppda_dict.get('def', 1))
        return round(att / df, 2) if df != 0 else 0.0
    except: return 0.0

async def get_or_create_team(db, team_name, team_id):
    """Garantisce che la squadra esista nel DB"""
    res = await db.execute(text("SELECT id FROM team WHERE id = :id"), {"id": team_id})
    if res.fetchone(): return team_id
    await db.execute(text("INSERT INTO team (id, name) VALUES (:id, :n) ON CONFLICT DO NOTHING"), {"id": team_id, "n": team_name})
    await db.commit()
    return team_id

async def process_massive_import():
    if not os.path.exists(FOLDER_PATH):
        print(f"❌ Errore: La cartella {FOLDER_PATH} non esiste.")
        return

    json_files = [f for f in os.listdir(FOLDER_PATH) if f.endswith(".json")]
    if not json_files:
        print("❌ Nessun file .json trovato. Controlla l'estensione dei file!")
        return

    print(f"🚀 Inizio iniezione massiva: {len(json_files)} stagioni rilevate.")

    async with AsyncSessionLocal() as db:
        for file_name in json_files:
            l_id = 1 
            name_low = file_name.lower()
            
            # Identificazione Lega Infallibile
            if "serie" in name_low:
                l_id = 1
            elif "premier" in name_low or "epl" in name_low:
                l_id = 2
            elif "bundesliga" in name_low:
                l_id = 4
            elif "liga" in name_low: # 'liga' deve stare dopo 'bundesliga'
                l_id = 3
            elif "ligue" in name_low:
                l_id = 5
            
            print(f"\n📂 Elaborazione: {file_name} (Lega ID: {l_id})")
            
            try:
                with open(os.path.join(FOLDER_PATH, file_name), "r", encoding="utf-8") as f:
                    master_data = json.load(f)

                dates_data = master_data.get('dates', {})
                teams_data = master_data.get('teams', {})

                # Normalizzazione calendario (lista o dict)
                matches_list = list(dates_data.values()) if isinstance(dates_data, dict) else dates_data

                # Mappatura Team -> Data -> Stats Avanzate
                team_hist = {}
                for t_id, t_info in teams_data.items():
                    team_hist[str(t_id)] = {h['date'][:10]: h for h in t_info.get('history', [])}

                updated_count = 0
                for m in matches_list:
                    if not m.get('id'): continue

                    h_id = str(m['h']['id'])
                    a_id = str(m['a']['id'])
                    match_date_str = m['datetime']
                    match_date_only = match_date_str[:10]

                    await get_or_create_team(db, m['h']['title'], int(h_id))
                    await get_or_create_team(db, m['a']['title'], int(a_id))
                    
                    try:
                        parsed_dt = datetime.strptime(match_date_str, "%Y-%m-%d %H:%M:%S")
                    except:
                        continue

                    # Risultati base
                    hg = int(m['goals']['h']) if m.get('goals') and m['goals'].get('h') is not None else 0
                    ag = int(m['goals']['a']) if m.get('goals') and m['goals'].get('a') is not None else 0
                    hxg = float(m['xG']['h']) if m.get('xG') and m['xG'].get('h') is not None else 0.0
                    axg = float(m['xG']['a']) if m.get('xG') and m['xG'].get('a') is not None else 0.0
                    
                    # Recupero dati avanzati incrociati
                    h_stats = team_hist.get(h_id, {}).get(match_date_only, {})
                    a_stats = team_hist.get(a_id, {}).get(match_date_only, {})

                    hd = int(h_stats.get('deep', 0))
                    ad = int(a_stats.get('deep', 0))
                    hp = calc_ppda(h_stats.get('ppda', {}))
                    ap = calc_ppda(a_stats.get('ppda', {}))
                    hx = float(h_stats.get('xpts', 0.0))
                    ax = float(a_stats.get('xpts', 0.0))

                    # UPSERT (Inserisce o Aggiorna tutto)
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
                        "id": int(m['id']), "l_id": l_id, "h_id": int(h_id), "a_id": int(a_id),
                        "hg": hg, "ag": ag, "hxg": hxg, "axg": axg,
                        "r": int(m.get('round', 0)), "dt": parsed_dt, "comp": m.get('isResult', False),
                        "hd": hd, "ad": ad, "hp": hp, "ap": ap, "hx": hx, "ax": ax
                    })
                    updated_count += 1
                
                await db.commit()
                print(f"   ✅ {updated_count} match sincronizzati correttamente.")

            except Exception as e:
                print(f"   🛑 Errore nel file {file_name}: {e}")

    print("\n🎯 PROCEDURA MASSIVA COMPLETATA. 5 anni di dati inseriti.")

if __name__ == "__main__":
    asyncio.run(process_massive_import())