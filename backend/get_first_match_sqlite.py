#!/usr/bin/env python3
import sqlite3
import json
import os

def main():
    db_path = os.path.join(os.path.dirname(__file__), "..", "comostat_backend", "comostat.db")
    if not os.path.exists(db_path):
        print(f"Database non trovato: {db_path}")
        # Cerca un altro database
        db_path = os.path.join(os.path.dirname(__file__), "comostat.db")
        if not os.path.exists(db_path):
            print("Nessun database SQLite trovato.")
            return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verifica se esiste una tabella 'matches'
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='matches';")
    if cursor.fetchone():
        cursor.execute("SELECT * FROM matches LIMIT 1;")
        row = cursor.fetchone()
        if row:
            # Ottieni nomi colonne
            cursor.execute("PRAGMA table_info(matches);")
            columns = [col[1] for col in cursor.fetchall()]
            match = dict(zip(columns, row))
            print(json.dumps(match, indent=2, ensure_ascii=False))
        else:
            print("Tabella matches vuota.")
    else:
        print("Tabella matches non presente nel database SQLite.")
    
    conn.close()

if __name__ == "__main__":
    main()