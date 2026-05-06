import asyncio
import aiohttp
import random
from understat import Understat
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# ==========================================
# CONFIGURAZIONE DATABASE
# ==========================================
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/xpalermostat"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# MAPPA LEGHE (Usa queste stringhe in LEAGUE_TO_PROCESS)
# "premier_league", "la_liga", "bundesliga", "ligue_1", "serie_a"
LEAGUE_TO_PROCESS = "premier_league"
LEAGUE_ID_MAP = {"serie_a": 1, "premier_league": 2, "la_liga": 3, "bundesliga": 4, "ligue_1": 5}
YEARS = [2020, 2021, 2022, 2023, 2024]

def calc_ppda(ppda_dict):
    try:
        att = float(ppda_dict.get('att', 0))
        df = float(ppda_dict.get('def', 1))
        return round(att / df, 2) if df != 0 else 0.0
    except: return 0.0

async def get_or_create_team(db, team_name):
    res = await db.execute(text("SELECT id FROM team WHERE name = :n"), {"n": team_name})
    row = res.fetchone()
    if row: return row[0]
    res = await db.execute(text("INSERT INTO team (name) VALUES (:n) RETURNING id"), {"n": team_name})
    return res.fetchone()[0]

async def process_season(league_name, year):
    league_id = LEAGUE_ID_MAP.get(league_name)
    print(f"\n🚀 {league_name.upper()} | Stagione {year} | Avvio Protocollo...")
    
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        try:
            # Jitter base per ogni richiesta
            await asyncio.sleep(random.uniform(3, 6))
            matches = await understat.get_league_results(league_name, year)
            
            async with AsyncSessionLocal() as db:
                for m in matches:
                    if not m.get('isResult'): continue
                    
                    # 1. Gestione Team
                    h_id = await get_or_create_team(db, m['h']['title'])
                    a_id = await get_or_create_team(db, m['a']['title'])
                    
                    # 2. UPSERT MATCH (Crea se manca, aggiorna se esiste)
                    upsert_q = text("""
                        INSERT INTO matchcalendar (
                            id, league_id, home_team_id, away_team_id, home_goals, away_goals,
                            "home_xG", "away_xG", round, match_datetime, is_scraped, is_completed,
                            home_deep, away_deep, home_ppda, away_ppda, home_xpts, away_xpts
                        ) VALUES (
                            :id, :l_id, :h_id, :a_id, :hg, :ag, :hxg, :axg, :r, :dt, True, True,
                            :hd, :ad, :hp, :ap, :hx, :ax
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            home_deep = EXCLUDED.home_deep,
                            away_deep = EXCLUDED.away_deep,
                            home_ppda = EXCLUDED.home_ppda,
                            away_ppda = EXCLUDED.away_ppda,
                            home_xpts = EXCLUDED.home_xpts,
                            away_xpts = EXCLUDED.away_xpts
                    """)
                    
                    await db.execute(upsert_q, {
                        "id": int(m['id']), "l_id": league_id, "h_id": h_id, "a_id": a_id,
                        "hg": int(m['goals']['h']), "ag": int(m['goals']['a']),
                        "hxg": float(m['xG']['h']), "axg": float(m['xG']['a']),
                        "r": int(m.get('round', 0)), "dt": m['datetime'],
                        "hd": int(m['deep']['h']), "ad": int(m['deep']['a']),
                        "hp": calc_ppda(m['ppda']['h']), "ap": calc_ppda(m['ppda']['a']),
                        "hx": float(m['xpts']['h']), "ax": float(m['xpts']['a'])
                    })
                await db.commit()
                print(f"   ✅ Stagione {year} completata con successo.")
                
        except (aiohttp.ClientConnectorError, aiohttp.ServerDisconnectedError, Exception) as e:
            print(f"   ⚠️ ERRORE RILEVATO: {e}")
            print("   💤 PROTOCOLLO IBERNAZIONE: Attesa di 30 minuti (1800s) prima di riprovare...")
            await asyncio.sleep(1800)
            # Riprova la stessa stagione dopo il sonno
            await process_season(league_name, year)

async def main():
    print("==============================================")
    print(f" PITCHLOGIX GLOBAL REBUILDER: {LEAGUE_TO_PROCESS.upper()}")
    print("==============================================")
    for year in YEARS:
        await process_season(LEAGUE_TO_PROCESS, year)
    print("\n🎯 DATABASE AGGIORNATO E COERENTE.")

if __name__ == "__main__":
    asyncio.run(main())