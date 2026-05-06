import os
from sqlalchemy import create_engine, text, inspect

# ==========================================
# CONFIGURAZIONE DATABASE
# ==========================================
DB_URI = "postgresql://postgres:tua_password@localhost:5432/xpalermostat_db" # <--- INSERISCI LA PASSWORD
engine = create_engine(DB_URI)

# Definiamo il percorso esatto per il tuo Desktop
desktop_path = r"C:\Users\euron\Desktop\report_database.txt"

print(f"\nGenerazione report in corso... sto scrivendo il file sul Desktop...")

try:
    with open(desktop_path, "w", encoding="utf-8") as f:
        f.write("=== 📊 RADIOGRAFIA SINTETICA DATABASE ===\n\n")
        
        inspector = inspect(engine)
        tabelle = inspector.get_table_names()
        
        with engine.connect() as conn:
            # Vecchia architettura
            if 'matchcalendar' in tabelle:
                tot_mc = conn.execute(text("SELECT COUNT(*) FROM matchcalendar")).scalar()
                fantasmi_mc = conn.execute(text("SELECT COUNT(*) FROM matchcalendar WHERE is_scraped = False OR home_goals IS NULL")).scalar()
                f.write(f"🏛️ VECCHIA ARCHITETTURA (matchcalendar):\n")
                f.write(f"   - Partite totali: {tot_mc}\n")
                f.write(f"   - Partite vuote/fantasmi: {fantasmi_mc}\n\n")
            else:
                f.write("🏛️ VECCHIA ARCHITETTURA: Tabella non trovata.\n\n")

            # Nuova architettura
            if 'matches' in tabelle:
                tot_m = conn.execute(text("SELECT COUNT(*) FROM matches")).scalar()
                fantasmi_m = conn.execute(text('SELECT COUNT(*) FROM matches WHERE "date" IS NULL OR home_goals IS NULL')).scalar()
                f.write(f"🚀 NUOVA ARCHITETTURA (matches):\n")
                f.write(f"   - Partite perfette (2024/2025): {tot_m}\n")
                f.write(f"   - Partite vuote/fantasmi: {fantasmi_m}\n\n")
            else:
                f.write("🚀 NUOVA ARCHITETTURA: Tabella non trovata.\n\n")

            # Dati profondi
            if 'shots' in tabelle:
                tot_s = conn.execute(text("SELECT COUNT(*) FROM shots")).scalar()
                f.write(f"🎯 TIRI TOTALI (shots): {tot_s}\n")
                
            if 'rosters' in tabelle:
                tot_r = conn.execute(text("SELECT COUNT(*) FROM rosters")).scalar()
                f.write(f"🏃 STATISTICHE GIOCATORI (rosters): {tot_r}\n")
                
        f.write("\n=========================================\n")
        
    print(f"✅ FATTO! Apri il file 'report_database.txt' sul tuo Desktop.")

except Exception as e:
    print(f"❌ Errore durante la scrittura: {e}")