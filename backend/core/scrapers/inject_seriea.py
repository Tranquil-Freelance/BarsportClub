"""
💉 INIETTORE DATI: JSON -> POSTGRESQL (SERIE A)
"""
import json
from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres:password@localhost:5432/xpalermostat"
engine = create_engine(DB_URL)

def inject_data():
    print("💉 Lettura del file serie_a_understat.json in corso...")
    try:
        with open("serie_a_understat.json", "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        print("❌ ERRORE: Assicurati che il file 'serie_a_understat.json' sia nella cartella backend.")
        return
    except Exception as e:
        print(f"❌ Errore nella lettura del file: {e}")
        return

    # Creazione della tabella dedicata alla Serie A
    query_create = text("""
        CREATE TABLE IF NOT EXISTS seriea_matches (
            match_id VARCHAR(50) PRIMARY KEY,
            season VARCHAR(10),
            date TIMESTAMP,
            home_team VARCHAR(100),
            away_team VARCHAR(100),
            home_goals INTEGER,
            away_goals INTEGER,
            home_xg FLOAT,
            away_xg FLOAT
        );
    """)

    with engine.connect() as conn:
        conn.execute(query_create)
        conn.commit()

        # Adattamento struttura JSON (Lista piatta o Dizionario a stagioni)
        matches = []
        if isinstance(raw_data, list):
            matches = raw_data
        elif isinstance(raw_data, dict):
            for k, v in raw_data.items():
                if isinstance(v, list):
                    matches.extend(v)

        print(f"📊 Trovati {len(matches)} record nel JSON. Inizio iniezione nel DB...")

        inserted = 0
        for m in matches:
            try:
                # Salta le partite programmate ma non ancora giocate
                if not m.get("isResult"): continue 

                match_id = str(m.get("id", ""))
                season = str(m.get("season", "2024"))
                date = m.get("datetime")
                
                # Supporto per i vari formati chiave di Understat
                h_team = m.get("h", {}).get("title") or m.get("home_team")
                a_team = m.get("a", {}).get("title") or m.get("away_team")

                goals = m.get("goals", {})
                h_goals = int(goals.get("h", 0)) if isinstance(goals, dict) else int(m.get("home_goals", 0))
                a_goals = int(goals.get("a", 0)) if isinstance(goals, dict) else int(m.get("away_goals", 0))

                xg_data = m.get("xG", {})
                h_xg = float(xg_data.get("h", 0.0)) if isinstance(xg_data, dict) else float(m.get("home_xg", 0.0))
                a_xg = float(xg_data.get("a", 0.0)) if isinstance(xg_data, dict) else float(m.get("away_xg", 0.0))

                query_insert = text("""
                    INSERT INTO seriea_matches (match_id, season, date, home_team, away_team, home_goals, away_goals, home_xg, away_xg)
                    VALUES (:m_id, :sea, :dt, :h, :a, :hg, :ag, :hxg, :axg)
                    ON CONFLICT (match_id) DO NOTHING;
                """)

                conn.execute(query_insert, {
                    "m_id": match_id, "sea": season, "dt": date,
                    "h": h_team, "a": a_team, "hg": h_goals, "ag": a_goals, "hxg": h_xg, "axg": a_xg
                })
                inserted += 1
            except Exception:
                pass # Salta silenziosamente i record malformati

        conn.commit()
        print(f"✅ INIEZIONE COMPLETATA: {inserted} partite di Serie A caricate nel database PostgreSQL in 'seriea_matches'!")

if __name__ == "__main__":
    inject_data()