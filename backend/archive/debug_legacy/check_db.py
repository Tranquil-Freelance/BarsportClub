from sqlalchemy import create_engine, text

# Usa le tue credenziali
DB_URL = "postgresql://postgres:password@localhost:5432/xpalermostat"
engine = create_engine(DB_URL)

def check():
    try:
        with engine.connect() as conn:
            # Controllo Premier League
            res_epl = conn.execute(text("SELECT COUNT(*) FROM premier_match_players")).fetchone()
            # Controllo Serie A (Tiri)
            res_sa_shots = conn.execute(text("SELECT COUNT(*) FROM seriea_shots")).fetchone()
            # Controllo Serie A (Giocatori)
            res_sa_players = conn.execute(text("SELECT COUNT(*) FROM seriea_player_stats")).fetchone()

            print("\n📊 --- REPORTO STATO DATABASE ---")
            print(f"🏴󠁧󠁢󠁥󠁮󠁧󠁿 PREMIER LEAGUE (Giocatori): {res_epl[0]} righe")
            print(f"🇮🇹 SERIE A (Tiri molecolari): {res_sa_shots[0]} righe")
            print(f"🇮🇹 SERIE A (Giocatori): {res_sa_players[0]} righe")
            
            if res_epl[0] > 40000:
                print("\n✅ PREMIER: Dati presenti. Il lavoro di ieri è salvo.")
            else:
                print("\n❌ PREMIER: Dati insufficienti o mancanti!")

    except Exception as e:
        print(f"❌ Errore durante il controllo: {e}")

if __name__ == "__main__":
    check()