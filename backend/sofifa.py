import requests
from bs4 import BeautifulSoup
import psycopg2
import time
import random
import urllib.parse
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ─── CONFIGURAZIONE DATABASE ─────────────────────────────────────────────────
# Cablato con i tuoi dati esatti
DB_CONFIG = {
    "dbname": "xpalermostat", 
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5432"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection": "keep-alive"
}

def get_missing_players(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT r.player 
            FROM rosters r
            WHERE r.player NOT IN (SELECT player_name FROM player_metadata)
        """)
        return [row[0] for row in cur.fetchall()]

def save_player_metadata(conn, player_name, age):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO player_metadata (player_name, age)
            VALUES (%s, %s)
            ON CONFLICT (player_name) DO NOTHING;
        """, (player_name, age))
    conn.commit()

def fetch_age_from_sofifa(player_name):
    encoded_name = urllib.parse.quote(player_name)
    url = f"https://sofifa.com/players?keyword={encoded_name}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        # Livello 2 Anti-ban: Rate Limit Recovery
        if response.status_code == 429:
            logger.warning(f"RATE LIMIT RAGGIUNTO (429) per {player_name}. Inizio ibernazione di 30 minuti...")
            time.sleep(1800)
            return fetch_age_from_sofifa(player_name)
            
        if response.status_code != 200:
            logger.error(f"Errore {response.status_code} su SoFIFA per {player_name}")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # TENTATIVO 1: Pagina di ricerca (esiste una tabella)
        table_row = soup.select_one('table tbody tr')
        if table_row:
            # Cerchiamo il primo numero plausibile per un'età (tra 15 e 45 anni) nelle celle
            for td in table_row.select('td'):
                txt = td.get_text(strip=True)
                if txt.isdigit() and 15 <= int(txt) <= 45:
                    return int(txt)

        # TENTATIVO 2: Redirect automatico alla pagina del profilo del giocatore
        text_content = soup.get_text()
        
        # Cerchiamo format " 22y.o. "
        match_yo = re.search(r'\b(\d{2})\s*y\.o\.', text_content)
        if match_yo:
            return int(match_yo.group(1))
            
        # Cerchiamo format "Age 22" o "Età 22"
        match_age = re.search(r'(?:Age|Età)[\s:]*(\d{2})', text_content, re.IGNORECASE)
        if match_age:
            return int(match_age.group(1))
            
        logger.warning(f"HTML incomprensibile o giocatore inesistente per {player_name}")
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Errore di connessione per {player_name}: {e}")
        return None

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Connessione al database stabilita.")
        
        players = get_missing_players(conn)
        logger.info(f"Trovati {len(players)} giocatori mancanti nel metadata.")
        
        for idx, player in enumerate(players):
            logger.info(f"[{idx+1}/{len(players)}] Scansione per: {player}")
            
            age = fetch_age_from_sofifa(player)
            
            if age is not None:
                save_player_metadata(conn, player, age)
                logger.info(f"Salvato: {player} - {age} anni")
            else:
                # Inseriamo NULL per non interrogarlo all'infinito se non esiste
                save_player_metadata(conn, player, None)
                logger.info(f"Giocatore non trovato. Marcato come mancante: {player}")
            
            # Livello 1 Anti-ban: Jitter base
            sleep_time = random.uniform(3.0, 7.0)
            logger.info(f"Jitter: attesa di {sleep_time:.2f} secondi...")
            time.sleep(sleep_time)
            
    except Exception as e:
        logger.error(f"Errore fatale nello script: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            logger.info("Connessione al database chiusa.")

if __name__ == "__main__":
    main()