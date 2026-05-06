from sqlalchemy import create_engine, text, inspect
import datetime

# --- CONFIGURAZIONE ---
DB_URI = "postgresql://postgres:tua_password@localhost:5432/xpalermostat_db" # INSERISCI LA PASSWORD
engine = create_engine(DB_URI)

print("\n🔍 Analisi maniacale dello storico partite in corso...\n")

def get_column_names(table_name):
    inspector = inspect(engine)
    return [c['name'] for c in inspector.get_columns(table_name)]

try:
    with engine.connect() as conn:
        cols = get_column_names('matches')
        
        # Rilevamento esatto delle colonne per evitare crash
        date_col = next((c for c in cols if c.lower() in ['date', 'datetime']), 'date')
        ht_col = next((c for c in cols if c.lower() in ['home_team', 'h_team']), 'h_team')
        at_col = next((c for c in cols if c.lower() in ['away_team', 'a_team']), 'a_team')
        hg_col = next((c for c in cols if c.lower() in ['home_goals', 'h_goals', 'score_h']), 'h_goals')
        ag_col = next((c for c in cols if c.lower() in ['away_goals', 'a_goals', 'score_a']), 'a_goals')

        # 1. Raggruppamento per Anno (Dimostra lo storico)
        print("=== 📅 PARTITE NEL DATABASE DIVISE PER ANNO ===")
        query_anni = text(f"""
            SELECT EXTRACT(YEAR FROM "{date_col}") as anno, COUNT(*) as totale 
            FROM matches 
            WHERE "{date_col}" IS NOT NULL 
            GROUP BY EXTRACT(YEAR FROM "{date_col}") 
            ORDER BY anno DESC
        """)
        anni = conn.execute(query_anni).fetchall()
        for anno in anni:
            # Converte l'anno float a intero pulito
            print(f"    Stagione {int(anno[0])}: {anno[1]} partite")
            
        print("\n===============================================\n")

        # 2. Ultime 10 partite (Dimostra i dati freschi della Serie A attuale)
        print(f"=== ⚽ LE ULTIME 15 PARTITE INIETTATE (Stagione Corrente) ===")
        query_ultime = text(f"""
            SELECT "{date_col}", "{ht_col}", "{hg_col}", "{ag_col}", "{at_col}" 
            FROM matches 
            ORDER BY "{date_col}" DESC 
            LIMIT 15
        """)
        ultime_partite = conn.execute(query_ultime).fetchall()
        
        for p in ultime_partite:
            data_match = p[0]
            if isinstance(data_match, str):
                data_match = data_match[:10] # Prende solo YYYY-MM-DD
            elif isinstance(data_match, datetime.datetime):
                data_match = data_match.strftime('%Y-%m-%d')
                
            print(f"    [{data_match}] {p[1]} {p[2]} - {p[3]} {p[4]}")
            
        print("\n===============================================\n")

except Exception as e:
    print(f"❌ Errore durante l'analisi: {e}")