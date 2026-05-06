from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres:password@localhost:5432/xpalermostat"
engine = create_engine(DB_URL)

def calcola_medie():
    print("📈 Calcolo delle statistiche molecolari (per 90 minuti)...")
    
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS player_stats_seasonal"))
        
        query = text("""
            CREATE TABLE player_stats_seasonal AS
            SELECT 
                player_id,
                UPPER(TRIM(player_name)) as search_name,
                SUM(time) as total_minutes,
                ROUND(CAST(SUM(xg) * 90.0 / NULLIF(SUM(time), 0) AS NUMERIC), 2) as xg_per_90,
                ROUND(CAST(SUM(xa) * 90.0 / NULLIF(SUM(time), 0) AS NUMERIC), 2) as xa_per_90,
                ROUND(CAST(SUM(npxg) * 90.0 / NULLIF(SUM(time), 0) AS NUMERIC), 2) as npxg_per_90,
                ROUND(CAST(SUM(xgchain) * 90.0 / NULLIF(SUM(time), 0) AS NUMERIC), 2) as xgchain_per_90,
                ROUND(CAST(SUM(key_passes) * 90.0 / NULLIF(SUM(time), 0) AS NUMERIC), 2) as keypasses_per_90
            FROM master_europa
            GROUP BY player_id, player_name
            HAVING SUM(time) > 450; -- Escludiamo chi ha giocato troppo poco
        """)
        conn.execute(query)
    
    print("✅ Statistiche pronte! I grafici ora avranno i numeri reali.")

if __name__ == "__main__":
    calcola_medie()