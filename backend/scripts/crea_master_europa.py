from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres:password@localhost:5432/xpalermostat"
engine = create_engine(DB_URL)

def crea_tabella_unificata():
    # Questa query unisce tutte le tabelle in una sola chiamata 'master_europa'
    query_unione = text("""
        CREATE TABLE IF NOT EXISTS master_europa AS
        SELECT 'Premier League' as league, * FROM premier_match_players
        UNION ALL
        SELECT 'Serie A' as league, * FROM seriea_match_players
        UNION ALL
        SELECT 'La Liga' as league, * FROM laliga_match_players
        UNION ALL
        SELECT 'Bundesliga' as league, * FROM bundesliga_match_players
        UNION ALL
        SELECT 'Ligue 1' as league, * FROM ligue1_match_players;
    """)
    
    print("🚀 Raffineria in corso: Creazione tabella MASTER_EUROPA...")
    
    with engine.begin() as conn:
        # Cancelliamo la vecchia tabella se esiste per rifarla da zero pulita
        conn.execute(text("DROP TABLE IF EXISTS master_europa"))
        conn.execute(query_unione)
        
    print("✅ Successo! Ora hai un unico archivio con tutti i dati europei.")

if __name__ == "__main__":
    crea_tabella_unificata()