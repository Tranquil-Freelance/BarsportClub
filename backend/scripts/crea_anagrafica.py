from sqlalchemy import create_engine, text

# Connessione al tuo database
DB_URL = "postgresql://postgres:password@localhost:5432/xpalermostat"
engine = create_engine(DB_URL)

def pulizia_anagrafica():
    print("🧹 Inizio pulizia: Creazione dell'Anagrafe Unica...")
    
    with engine.begin() as conn:
        # 1. Cancelliamo la vecchia tabella se esiste per non fare pasticci
        conn.execute(text("DROP TABLE IF EXISTS player_registry"))
        
        # 2. Creiamo la nuova tabella pulita
        # UPPER(player_name) trasforma tutto in maiuscolo per facilitare la ricerca
        query = text("""
            CREATE TABLE player_registry AS
            SELECT DISTINCT ON (player_id)
                player_id,
                player_name as original_name,
                UPPER(TRIM(player_name)) as search_name,
                team_name as current_team,
                league,
                season as last_active_season
            FROM master_europa
            ORDER BY player_id, season DESC;
        """)
        conn.execute(query)
        
        # 3. Mettiamo l'ID come chiave primaria (velocizza le ricerche del 1000%)
        conn.execute(text("ALTER TABLE player_registry ADD PRIMARY KEY (player_id)"))
        
    print("✅ Anagrafica creata! Ora il sistema sa chi è chi.")

if __name__ == "__main__":
    pulizia_anagrafica()