import asyncio
import aiohttp
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

# Nel file update_stats.py
YEARS = [2021, 2024]

def calc_ppda(ppda_dict):
    try:
        att = float(ppda_dict.get('att', 0))
        df = float(ppda_dict.get('def', 1))
        if df == 0: return 0.0
        return round(att / df, 2)
    except:
        return 0.0

# ==========================================
# FIX SCHEMA: CREA LE COLONNE MANCANTI
# ==========================================
async def upgrade_database_schema():
    print("🛠️ Controllo e aggiornamento della struttura del database...")
    async with AsyncSessionLocal() as db:
        try:
            # Aggiunge le colonne fisicamente se non esistono
            alter_query = text("""
                ALTER TABLE matchcalendar 
                ADD COLUMN IF NOT EXISTS home_deep INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS away_deep INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS home_ppda FLOAT DEFAULT 0.0,
                ADD COLUMN IF NOT EXISTS away_ppda FLOAT DEFAULT 0.0,
                ADD COLUMN IF NOT EXISTS home_xpts FLOAT DEFAULT 0.0,
                ADD COLUMN IF NOT EXISTS away_xpts FLOAT DEFAULT 0.0;
            """)
            await db.execute(alter_query)
            await db.commit()
            print("   ✅ Colonne avanzate (DEEP, PPDA, xPTS) pronte all'uso!")
        except Exception as e:
            print(f"   ⚠️ Impossibile alterare la tabella (forse esistono già o mancano i permessi): {e}")

# ==========================================
# ESTRAZIONE DATI
# ==========================================
async def update_league_data(league_name, year):
    print(f"\n🚀 Recupero dati {league_name} stagione {year}/{year+1} tramite libreria 'understat'...")
    
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        
        try:
            matches = await understat.get_league_results(league_name, year)
        except Exception as e:
            print(f"   ❌ Errore durante il fetch: {e}")
            return

        if not matches:
            print("   ⚠️ Nessun dato trovato.")
            return

        print(f"   ✅ Trovate {len(matches)} partite. Aggiornamento DB in corso...")
        
        async with AsyncSessionLocal() as db:
            updated_count = 0
            for match in matches:
                if not match.get('isResult'):
                    continue

                u_match_id = int(match['id'])
                
                home_deep = match.get('deep', {}).get('h', 0)
                away_deep = match.get('deep', {}).get('a', 0)
                home_ppda = calc_ppda(match.get('ppda', {}).get('h', {}))
                away_ppda = calc_ppda(match.get('ppda', {}).get('a', {}))
                home_xpts = float(match.get('xpts', {}).get('h', 0.0))
                away_xpts = float(match.get('xpts', {}).get('a', 0.0))

                update_query = text("""
                    UPDATE matchcalendar 
                    SET home_deep = :hd, away_deep = :ad, 
                        home_ppda = :hp, away_ppda = :ap, 
                        home_xpts = :hx, away_xpts = :ax
                    WHERE id = :id
                """)
                
                result = await db.execute(update_query, {
                    "hd": home_deep, "ad": away_deep, 
                    "hp": home_ppda, "ap": away_ppda, 
                    "hx": home_xpts, "ax": away_xpts, 
                    "id": u_match_id
                })
                
                if result.rowcount > 0:
                    updated_count += 1
            
            await db.commit()
            print(f"   🎯 Completato! {updated_count} partite aggiornate con metriche avanzate.")

async def main():
    print("==============================================")
    print(" INIZIO AGGIORNAMENTO DATI TRAMITE UNDERSTAT LIB")
    print("==============================================")
    
    # 1. Costruiamo le colonne mancanti
    await upgrade_database_schema()
    
    # 2. Scarichiamo i dati
    for year in YEARS:
        await update_league_data("serie_a", year)
        await asyncio.sleep(2)

    print("\n✅ TUTTO COMPLETATO. Il tuo database ora ha la struttura e i dati perfetti.")

if __name__ == "__main__":
    asyncio.run(main())