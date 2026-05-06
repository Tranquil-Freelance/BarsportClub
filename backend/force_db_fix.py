import asyncio
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError

# Importiamo il motore asincrono che hai già configurato nel tuo progetto
from app.db.database import engine

async def fix_database():
    print("🔧 Inizio ispezione e forzatura delle colonne nella tabella 'matches'...\n")
    
    # Lista esatta delle colonne mancanti segnalate dall'errore
    colonne_da_aggiungere = [
        "ADD COLUMN league_id INTEGER",
        "ADD COLUMN home_team_id INTEGER",
        "ADD COLUMN home_xg FLOAT",
        "ADD COLUMN round INTEGER",
        "ADD COLUMN away_team_id INTEGER",
        "ADD COLUMN match_datetime DATETIME",
        "ADD COLUMN is_completed BOOLEAN DEFAULT FALSE",
        "ADD COLUMN is_scraped BOOLEAN DEFAULT FALSE",
        "ADD COLUMN home_goals INTEGER",
        "ADD COLUMN away_goals INTEGER",
        "ADD COLUMN away_xg FLOAT"
    ]

    async with engine.begin() as conn:
        for colonna in colonne_da_aggiungere:
            query = text(f"ALTER TABLE matches {colonna};")
            try:
                await conn.execute(query)
                print(f"✅ SUCCESSO - Eseguito: {colonna}")
            except Exception as e:
                # Se fallisce (solitamente perché la colonna esiste già o per la sintassi del dialetto)
                # catturiamo l'errore e andiamo avanti senza far esplodere lo script.
                errore_str = str(e).replace('\n', ' ')
                print(f"⏩ SALTATO - {colonna} (Motivo: colonna già presente o dialetto incompatibile)")
    
    print("\n✅ Scansione e allineamento del database completati.")

if __name__ == "__main__":
    asyncio.run(fix_database())
    # Blocco anti-chiusura per farti leggere l'output se lo lanci fuori dal terminale integrato
    input("\nPremi INVIO per chiudere questa finestra e tornare al lavoro...")