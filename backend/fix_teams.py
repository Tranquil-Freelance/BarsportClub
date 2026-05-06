import asyncio
from sqlalchemy import select, update
from app.db.database import AsyncSessionLocal
from app.db.models import Match, PlayerStat

async def ripara_squadre():
    print("🩺 Inizio operazione: Riassegnazione squadre ai giocatori...")
    
    async with AsyncSessionLocal() as db:
        # Preleviamo tutte le partite che hanno i nomi corretti
        matches = (await db.execute(select(Match))).scalars().all()
        
        count = 0
        for m in matches:
            # 1. Assegna i giocatori di casa ('h') alla squadra di casa
            await db.execute(
                update(PlayerStat)
                .where(PlayerStat.match_id == m.id)
                .where(PlayerStat.team_type == 'h')
                .values(team_name=m.home_team)
            )
            
            # 2. Assegna i giocatori in trasferta ('a') alla squadra in trasferta
            await db.execute(
                update(PlayerStat)
                .where(PlayerStat.match_id == m.id)
                .where(PlayerStat.team_type == 'a')
                .values(team_name=m.away_team)
            )
            count += 1
            if count % 500 == 0:
                print(f"⏳ Elaborate {count} partite...")
                
        await db.commit()
        print("✅ Operazione riuscita! Tutte le squadre sono state ripristinate.")

if __name__ == "__main__":
    asyncio.run(ripara_squadre())