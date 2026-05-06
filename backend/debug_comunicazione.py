import psycopg2
from psycopg2.extras import RealDictCursor

# PARAMETRI DI CONNESSIONE
DB_CONFIG = {
    "dbname": "xpalermostat_db",
    "user": "postgres",
    "password": "tua_password", 
    "host": "localhost",
    "port": "5432"
}

def find_the_broken_link():
    print("--- ANALISI CHIRURGICA DEI DATI ---")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 1. Verifica se esistono match_id comuni
        cur.execute("""
            SELECT COUNT(DISTINCT r.match_id) as common_matches
            FROM rosters r
            INNER JOIN shots s ON r.match_id = CAST(s.match_id AS INTEGER);
        """)
        common = cur.fetchone()['common_matches']
        print(f"[DATI] Match comuni per ID: {common}")

        # 2. Verifica se il problema è il nome del giocatore (Case Sensitivity / Spaces)
        cur.execute("""
            SELECT 
                (SELECT player FROM rosters LIMIT 1) as sample_roster,
                (SELECT player FROM shots LIMIT 1) as sample_shots;
        """)
        samples = cur.fetchone()
        print(f"[DATI] Esempio Roster: '{samples['sample_roster']}'")
        print(f"[DATI] Esempio Shots: '{samples['sample_shots']}'")

        # 3. TEST DEFINITIVO: Perché il JOIN fallisce?
        # Cerchiamo se esiste ALMENO un record dove match_id coincide ma il nome no
        cur.execute("""
            SELECT r.match_id, r.player as r_player, s.player as s_player
            FROM rosters r
            JOIN shots s ON r.match_id = CAST(s.match_id AS INTEGER)
            WHERE r.player != s.player
            LIMIT 1;
        """)
        mismatch = cur.fetchone()
        
        if common == 0:
            print("[RISULTATO] Il problema è negli ID: i match_id in 'rosters' e 'shots' sono totalmente diversi.")
        elif mismatch:
            print(f"[RISULTATO] Il problema è nei NOMI: per il match {mismatch['match_id']}, ")
            print(f"rosters dice '{mismatch['r_player']}' e shots dice '{mismatch['s_player']}'.")
        else:
            # Se arriviamo qui, i dati ci sono ma il filtro 500 minuti li sta segando tutti
            cur.execute("SELECT player, SUM(time) as t FROM rosters GROUP BY player ORDER BY t DESC LIMIT 1;")
            top_player = cur.fetchone()
            print(f"[RISULTATO] Il giocatore con più minuti ha: {top_player['t']} min.")
            if top_player['t'] < 500:
                print("ECCO IL PUNTO: Nessun giocatore nel database raggiunge i 500 minuti richiesti dal filtro.")

    except Exception as e:
        print(f"[ERRORE SQL] {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    find_the_broken_link()