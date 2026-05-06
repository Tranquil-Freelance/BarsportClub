#!/usr/bin/env python3
"""
Script per ottenere il primo match dal database e stamparlo come JSON.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_URL = "postgresql://postgres:password@localhost:5432/xpalermostat"

def main():
    try:
        engine = create_engine(DB_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Query per il primo match nella tabella matches (modello vecchio)
        result = session.execute(text("""
            SELECT id, understat_id, home_team, away_team, home_score, away_score, 
                   home_xg, away_xg, match_datetime, status, is_completed, is_scraped
            FROM matches 
            ORDER BY id 
            LIMIT 1
        """))
        row = result.fetchone()
        if row:
            match = {
                "id": row[0],
                "understat_id": row[1],
                "home_team": row[2],
                "away_team": row[3],
                "home_score": row[4],
                "away_score": row[5],
                "home_xg": float(row[6]) if row[6] is not None else None,
                "away_xg": float(row[7]) if row[7] is not None else None,
                "match_datetime": row[8].isoformat() if row[8] else None,
                "status": row[9],
                "is_completed": row[10],
                "is_scraped": row[11]
            }
            import json
            print(json.dumps(match, indent=2, ensure_ascii=False))
        else:
            # Nessun match, stampa esempio
            example = {
                "id": 1,
                "understat_id": 30116,
                "home_team": "Cagliari",
                "away_team": "Como",
                "home_score": 1,
                "away_score": 2,
                "home_xg": 0.8,
                "away_xg": 1.5,
                "match_datetime": "2025-02-15T15:00:00",
                "status": "FT",
                "is_completed": True,
                "is_scraped": True
            }
            import json
            print("Nessun match trovato nel database. Esempio di struttura:")
            print(json.dumps(example, indent=2, ensure_ascii=False))
        session.close()
    except Exception as e:
        print(f"Errore di connessione al database: {e}")
        print("Assicurarsi che PostgreSQL sia in esecuzione e le credenziali siano corrette.")
        sys.exit(1)

if __name__ == "__main__":
    main()