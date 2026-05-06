"""
⚙️ CREAZIONE MASTER VIEW: EUROPA TOP 5
Script per l'unificazione molecolare del database xpalermostat.
Costruisce un'infrastruttura ad altissime prestazioni per lo Scout Engine.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_URL_ASYNC = "postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat"

async def build_master_view():
    # Usiamo isolation_level AUTOCOMMIT perché Postgres lo richiede per alcune operazioni strutturali pesanti
    engine = create_async_engine(DB_URL_ASYNC, isolation_level="AUTOCOMMIT")
    
    try:
        async with engine.connect() as conn:
            print("🚀 Distruzione vecchia vista (se esistente)...")
            await conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS master_europe_players CASCADE;"))
            
            print("🌍 Fusione molecolare delle 5 Leghe in corso (creazione Materialized View)...")
            
            # Creiamo la Super Tabella aggiungendo la colonna 'league_name' per filtrare in futuro
            query_view = text("""
                CREATE MATERIALIZED VIEW master_europe_players AS
                SELECT 'Premier League' AS league_name, * FROM premier_match_players
                UNION ALL
                SELECT 'Serie A' AS league_name, * FROM seriea_match_players
                UNION ALL
                SELECT 'La Liga' AS league_name, * FROM laliga_match_players
                UNION ALL
                SELECT 'Bundesliga' AS league_name, * FROM bundesliga_match_players
                UNION ALL
                SELECT 'Ligue 1' AS league_name, * FROM ligue1_match_players;
            """)
            await conn.execute(query_view)
            
            print("⚡ Creazione Indici B-Tree per latenza zero sulle query dello Scout Engine...")
            
            # Indice sul nome giocatore (per la ricerca istantanea)
            await conn.execute(text("CREATE INDEX idx_master_player_name ON master_europe_players (player_name);"))
            # Indice sulla lega (per filtrare i sostituti solo in certi campionati)
            await conn.execute(text("CREATE INDEX idx_master_league ON master_europe_players (league_name);"))
            
            print("=====================================================")
            print("✅ MASTER VIEW 'master_europe_players' CREATA CON SUCCESSO")
            print("L'infrastruttura per lo Z-Score europeo è operativa.")
            print("=====================================================")

    except Exception as e:
        print(f"❌ ERRORE CRITICO DB: {e}")

if __name__ == "__main__":
    asyncio.run(build_master_view())