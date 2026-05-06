import requests
import logging
from sqlalchemy import create_engine, text

# ==========================================
# CONFIGURAZIONE
# ==========================================
API_KEY = "a625974ace874e5bace4b50ee066f5fb"
DB_URI = "postgresql://postgres:password@localhost:5432/xpalermostat" # Metti la tua password

# Mappatura Competizioni (API-ID -> Nome nel tuo DB)
COMPETITIONS = {
    "PL": "Premier League",
    "PD": "La liga",
    "BL1": "Bundesliga",
    "FL1": "Ligue 1"
}

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def sync_calendari_ufficiali():
    engine = create_engine(DB_URI)
    headers = {"X-Auth-Token": API_KEY}
    
    logging.info("🚀 Inizio sincronizzazione giornate ufficiali...")

    for code, league_name in COMPETITIONS.items():
        logging.info(f"--- ⚽ Elaborazione: {league_name} ---")
        
        # 1. Recupero ID Lega dal tuo DB
        with engine.connect() as conn:
            res_id = conn.execute(text("SELECT id FROM league WHERE name ILIKE :name"), {"name": f"%{league_name}%"}).fetchone()
            if not res_id:
                logging.error(f"❌ Lega {league_name} non trovata nel DB.")
                continue
            league_id = res_id[0]

        # 2. Chiamata API per il calendario 2025 (Stagione Corrente)
        url = f"https://api.football-data.org/v4/competitions/{code}/matches?season=2025"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                logging.error(f"❌ Errore API per {league_name}: {response.status_code}")
                continue
            
            api_data = response.json()
            matches = api_data.get('matches', [])
            
            count_updated = 0
            with engine.begin() as conn:
                for m in matches:
                    matchday = m.get('matchday')
                    # Estraiamo la data pura (YYYY-MM-DD)
                    m_date = m.get('utcDate').split('T')[0]
                    home_team_api = m.get('homeTeam', {}).get('shortName') or m.get('homeTeam', {}).get('name')
                    away_team_api = m.get('awayTeam', {}).get('shortName') or m.get('awayTeam', {}).get('name')

                    # 3. Update Chirurgico nel DB
                    # Cerchiamo il match nel tuo DB che ha la stessa data (o quasi) e una delle due squadre 
                    # (usiamo ILIKE per gestire differenze di nomi tipo 'Man City' vs 'Manchester City')
                    query_update = text("""
                        UPDATE matchcalendar 
                        SET matchday = :round
                        WHERE league_id = :l_id 
                          AND match_datetime::date = :m_date::date
                          AND (
                            home_team_id IN (SELECT id FROM team WHERE name ILIKE :h_name OR name ILIKE :h_short)
                            OR 
                            away_team_id IN (SELECT id FROM team WHERE name ILIKE :a_name OR name ILIKE :a_short)
                          )
                    """)
                    
                    result = conn.execute(query_update, {
                        "round": matchday,
                        "l_id": league_id,
                        "m_date": m_date,
                        "h_name": f"%{home_team_api}%",
                        "h_short": f"{home_team_api[:5]}%", # Failsafe: primi 5 caratteri
                        "a_name": f"%{away_team_api}%",
                        "a_short": f"{away_team_api[:5]}%"
                    })
                    
                    if result.rowcount > 0:
                        count_updated += 1

            logging.info(f"✅ {league_name} sincronizzata: {count_updated} match corretti.")

        except Exception as e:
            logging.error(f"💥 Errore durante l'elaborazione di {league_name}: {e}")

    logging.info("==========================================")
    logging.info("🏁 SINCRONIZZAZIONE COMPLETATA.")
    logging.info("==========================================")

if __name__ == "__main__":
    sync_calendari_ufficiali()