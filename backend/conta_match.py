import os
import json
import logging
from sqlalchemy import create_engine, text

# ==========================================
# CONFIGURAZIONE DATABASE E PERCORSI
# ==========================================
DB_URI = "postgresql://postgres:password@localhost:5432/xpalermostat" # La tua password
JSON_DIR = r"C:\Users\euron\Desktop\ultima iniezione"

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def safe_float(val):
    try: return float(val)
    except: return 0.0

def safe_int(val):
    try: return int(val)
    except: return 0

def lancia_autobotte_grimaldello_corretto():
    logging.info("🚛 AUTOBOTTE v2.1 (FIX CASTING DATA): Bypasso Fuso Orario...")
    engine = create_engine(DB_URI)
    
    # FIX: Usiamo la sintassi nativa di Postgres (::date) per comparare solo l'anno-mese-giorno
    update_home_query = text("""
        UPDATE matchcalendar 
        SET home_xpts = :xpts, home_deep = :deep, home_ppda = :ppda
        WHERE match_datetime::date = :m_date::date AND home_team_id = :team_id
    """)
    
    update_away_query = text("""
        UPDATE matchcalendar 
        SET away_xpts = :xpts, away_deep = :deep, away_ppda = :ppda
        WHERE match_datetime::date = :m_date::date AND away_team_id = :team_id
    """)

    if not os.path.exists(JSON_DIR):
        logging.error(f"❌ Cartella {JSON_DIR} non trovata.")
        return

    files_json = [f for f in os.listdir(JSON_DIR) if f.endswith('.json')]
    logging.info(f"📂 Trovati {len(files_json)} file JSON.")

    totale_record_aggiornati = 0

    for filename in files_json:
        filepath = os.path.join(JSON_DIR, filename)
        logging.info(f"⚙️ Iniezione forzata per: {filename} ...")
        
        match_count = 0
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            with engine.begin() as conn:
                for team_id_str, team_data in data.items():
                    team_id = int(team_id_str)
                    history = team_data.get('history', []) if isinstance(team_data, dict) else team_data
                    
                    for match in history:
                        raw_date = match.get('date') # Formato "YYYY-MM-DD HH:MM:SS"
                        
                        # FIX: Estraiamo solo la data pura "YYYY-MM-DD" per evitare casini a Postgres
                        m_date_only = raw_date.split(' ')[0] if raw_date else None
                        
                        if not m_date_only:
                            continue
                            
                        side = match.get('h_a')
                        xpts = safe_float(match.get('xpts'))
                        deep = safe_int(match.get('deep'))
                        
                        ppda_val = 0.0
                        ppda_data = match.get('ppda', {})
                        ppda_def = safe_float(ppda_data.get('def'))
                        ppda_att = safe_float(ppda_data.get('att'))
                        
                        if ppda_def > 0:
                            ppda_val = ppda_att / ppda_def
                            
                        # INIEZIONE
                        if side == 'h':
                            res = conn.execute(update_home_query, {
                                "xpts": xpts, "deep": deep, "ppda": ppda_val, 
                                "m_date": m_date_only, "team_id": team_id
                            })
                            match_count += res.rowcount
                        elif side == 'a':
                            res = conn.execute(update_away_query, {
                                "xpts": xpts, "deep": deep, "ppda": ppda_val, 
                                "m_date": m_date_only, "team_id": team_id
                            })
                            match_count += res.rowcount
                        
                        totale_record_aggiornati += 1

            logging.info(f"✅ {filename} completato. Righe colpite nel DB: {match_count}")

        except Exception as e:
            logging.error(f"❌ Errore nel file {filename}: {e}")

    logging.info("==================================================")
    logging.info(f"🏁 RECUPERO COMPLETATO. Dati elaborati: {totale_record_aggiornati}")
    logging.info("==================================================")

if __name__ == "__main__":
    lancia_autobotte_grimaldello_corretto()