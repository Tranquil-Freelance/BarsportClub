import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat"

async def check_shots():
    engine = create_async_engine(DB_URL, echo=False)
    try:
        async with engine.begin() as conn:
            # Conta quanti tiri ci sono in totale
            result = await conn.execute(text("SELECT COUNT(*) FROM shots;"))
            count = result.scalar()
            
            print("\n=== VERIFICA DATABASE: TABELLA TIRI ===")
            print(f"Tiri totali salvati: {count}")
            
            if count > 0:
                # Se ci sono tiri, controlliamo che ID partita usano
                sample = await conn.execute(text("SELECT match_id FROM shots LIMIT 5;"))
                ids = [row[0] for row in sample.fetchall()]
                print(f"Esempio di ID Partita usati nei tiri: {ids}")
                print("=======================================\n")
                print("Diagnosi: I tiri esistono, ma gli ID non combaciano con il calendario.")
            else:
                print("=======================================\n")
                print("Diagnosi: La tabella è VUOTA. Lo scraper dei dettagli non è stato lanciato.")
                
    except Exception as e:
        print(f"\n[ERRORE DI CONNESSIONE]: {e}\n")

if __name__ == "__main__":
    asyncio.run(check_shots())