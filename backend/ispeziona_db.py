import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat"

async def inspect_columns():
    engine = create_async_engine(DB_URL, echo=False)
    try:
        async with engine.begin() as conn:
            # Chiediamo a Postgres l'elenco esatto delle colonne per 'matchcalendar'
            query = text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'matchcalendar';
            """)
            result = await conn.execute(query)
            columns = result.fetchall()
            
            print("\n=== COLONNE REALI DI 'matchcalendar' ===")
            if not columns:
                print("Nessuna colonna trovata. Sicuro del nome della tabella?")
            else:
                for col in columns:
                    print(f"- {col[0]} ({col[1]})")
            print("========================================\n")
    except Exception as e:
        print(f"\n[ERRORE DI CONNESSIONE]: {e}\n")

if __name__ == "__main__":
    asyncio.run(inspect_columns())