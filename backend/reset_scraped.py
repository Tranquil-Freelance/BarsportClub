import asyncio
from sqlalchemy import text
from app.db.database import get_db

async def reset_matches():
    async for db in get_db():
        # Portiamo is_scraped a False per tutte le partite completate
        # Così lo scraper le riprocesserà con la nuova logica AI
        await db.execute(text("UPDATE matchcalendar SET is_scraped = False WHERE is_completed = True;"))
        await db.commit()
        print("🟢 RESET COMPLETATO: Ora lo scraper riprocesserà tutte le partite con l'AI.")
        break

if __name__ == "__main__":
    asyncio.run(reset_matches())