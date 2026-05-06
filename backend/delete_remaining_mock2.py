import pandas as pd
import logging
import math
from sqlalchemy import create_engine, text

# --- CONFIGURAZIONE LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- CONFIGURAZIONE DATABASE ---
DB_URI = "postgresql://postgres:postgres@localhost:5432/xpalermostat"
engine = create_engine(DB_URI)

def run_csv_updater():
    logging.info("🚀 Avvio Updater Anagrafico da CSV Locale (con Immagini)")

    # 1. Blindatura Tabella e Aggiunta Colonna Immagini
    with engine.begin() as conn:
        # Creazione base
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS player_registry (
                player_name VARCHAR PRIMARY KEY,
                age INTEGER,
                foot VARCHAR,
                height VARCHAR,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        # Aggiunta colonna image_url in modo sicuro se la tabella esisteva già
        conn.execute(text("""
            ALTER TABLE player_registry 
            ADD COLUMN IF NOT EXISTS image_url VARCHAR;
        """))

    try:
        logging.info("📂 Caricamento del file players.csv in memoria...")
        df = pd.read_csv('players.csv', low_memory=False)
        
        if 'name' not in df.columns:
            logging.error("❌ Colonna 'name' non trovata.")
            return
            
        df = df.dropna(subset=['name'])
        df['name_lower'] = df['name'].astype(str).str.lower().str.strip()
        
        # 2. Interrogazione del DB per i mancanti
        with engine.connect() as conn:
            query_target = text("""
                SELECT DISTINCT r.player 
                FROM rosters r
                LEFT JOIN player_registry p ON r.player = p.player_name
                WHERE r.time > 0 AND p.player_name IS NULL
            """)
            res = conn.execute(query_target).fetchall()
            players_to_find = [row[0] for row in res]

        if not players_to_find:
            logging.info("✅ Nessun giocatore mancante. Anagrafica al 100%.")
            return

        logging.info(f"🎯 Il Database ha rilevato {len(players_to_find)} giocatori mancanti. Inizio ricerca...")

        # 3. Elaborazione e Upsert
        found_count = 0
        current_year = 2026 
        
        with engine.begin() as conn:
            for target_name in players_to_find:
                match = df[df['name_lower'] == target_name.lower().strip()]
                
                if not match.empty:
                    player_data = match.iloc[0]
                    
                    # --- Età ---
                    age = None
                    if 'date_of_birth' in player_data and pd.notnull(player_data['date_of_birth']):
                        dob = str(player_data['date_of_birth'])
                        if len(dob) >= 4 and dob[:4].isdigit():
                            age = current_year - int(dob[:4])
                    
                    # --- Altezza ---
                    height = "N/A"
                    if 'height_in_cm' in player_data and pd.notnull(player_data['height_in_cm']):
                        h_val = player_data['height_in_cm']
                        if not math.isnan(h_val) and h_val > 0:
                            height = f"{int(h_val)}cm"
                    
                    # --- Piede ---
                    foot = "N/A"
                    if 'foot' in player_data and pd.notnull(player_data['foot']):
                        foot_raw = str(player_data['foot']).lower().strip()
                        if foot_raw == 'right': foot = "Destro"
                        elif foot_raw == 'left': foot = "Sinistro"
                        elif foot_raw == 'both': foot = "Ambidestro"

                    # --- Immagine ---
                    image_url = None
                    if 'image_url' in player_data and pd.notnull(player_data['image_url']):
                        image_url = str(player_data['image_url']).strip()

                    # 4. Iniezione nel Database
                    conn.execute(text("""
                        INSERT INTO player_registry (player_name, age, foot, height, image_url, last_updated)
                        VALUES (:n, :a, :f, :h, :img, CURRENT_TIMESTAMP)
                        ON CONFLICT (player_name) DO UPDATE SET
                            age = EXCLUDED.age,
                            foot = EXCLUDED.foot,
                            height = EXCLUDED.height,
                            image_url = EXCLUDED.image_url,
                            last_updated = EXCLUDED.last_updated
                    """), {"n": target_name, "a": age, "f": foot, "h": height, "img": image_url})
                    
                    found_count += 1
                    logging.info(f"  ✅ Archiviato: {target_name} -> Età: {age} | Foto: {'Trovata' if image_url else 'No'}")
                else:
                    logging.warning(f"  ❌ {target_name} non presente nel dump CSV.")

        logging.info("=" * 50)
        logging.info(f"🏁 Estrazione completata: {found_count} giocatori trovati e salvati.")
        logging.info("=" * 50)

    except Exception as e:
        logging.critical(f"Errore critico del motore CSV: {e}")

if __name__ == "__main__":
    run_csv_updater()