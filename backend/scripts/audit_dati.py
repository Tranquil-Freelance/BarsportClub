from sqlalchemy import create_engine, text

# Connessione al database
DB_URL = "postgresql://postgres:password@localhost:5432/xpalermostat"
engine = create_engine(DB_URL)

def esegui_audit():
    tabelle = [
        "premier_match_players", 
        "seriea_match_players", 
        "laliga_match_players", 
        "bundesliga_match_players", 
        "ligue1_match_players"
    ]
    
    print("\n--- AUDIT MANIACALE DEL DATABASE ---")
    
    with engine.connect() as conn:
        for tabella in tabelle:
            try:
                # Conta quante partite diverse ci sono per ogni stagione
                query = text(f"SELECT season, COUNT(DISTINCT match_id) FROM {tabella} GROUP BY season ORDER BY season")
                risultati = conn.execute(query).fetchall()
                
                print(f"\n📊 Lega: {tabella.upper()}")
                for r in risultati:
                    stato = "✅ OK" if r[1] >= 306 else "⚠️ INCOMPLETO"
                    print(f"   Stagione {r[0]}: {r[1]} partite {stato}")
            except Exception as e:
                print(f"❌ Tabella {tabella} non trovata o vuota.")

if __name__ == "__main__":
    esegui_audit()