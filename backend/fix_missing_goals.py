"""
Fix diretto: scarica risultati da Understat e aggiorna matchcalendar.home_goals
Usa il DB corretto (xpalermostat) e connessione diretta asyncpg.
"""
import asyncio
import aiohttp
import asyncpg
from understat import Understat

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "user": "postgres",
    "password": "password",
    "database": "xpalermostat",
}

LEAGUES = [
    ("serie_a",      1),
    ("epl",          2),
    ("la_liga",      3),
    ("bundesliga",   4),
    ("ligue_1",      5),
]
SEASON = 2025


async def main():
    conn = await asyncpg.connect(**DB_CONFIG)
    print("✅ Connesso a xpalermostat\n")

    async with aiohttp.ClientSession() as http:
        understat = Understat(http)

        for slug, league_id in LEAGUES:
            print(f"🔄 Scarico risultati {slug} stagione {SEASON}...")
            try:
                results = await understat.get_league_results(slug, SEASON)
            except Exception as e:
                print(f"  ⚠️  Errore fetch: {e}")
                results = []

            if not results:
                print(f"  ⚠️  0 risultati da Understat per {slug} {SEASON}")
                continue

            print(f"  📥 {len(results)} partite trovate")
            updated = 0

            for m in results:
                try:
                    mid = int(m.get("id", 0))
                    hg = int(m["goals"]["h"]) if m.get("goals") else None
                    ag = int(m["goals"]["a"]) if m.get("goals") else None
                    hxg = float(m["xG"]["h"]) if m.get("xG") else None
                    axg = float(m["xG"]["a"]) if m.get("xG") else None
                    is_done = m.get("isResult", False)

                    if not mid or hg is None:
                        continue

                    row = await conn.fetchrow(
                        "SELECT id FROM matchcalendar WHERE id = $1", mid
                    )
                    if row:
                        await conn.execute("""
                            UPDATE matchcalendar
                            SET home_goals=$1, away_goals=$2,
                                "home_xG"=$3, "away_xG"=$4,
                                is_completed=$5
                            WHERE id=$6
                        """, hg, ag, hxg, axg, is_done, mid)
                        updated += 1
                except Exception as e:
                    print(f"  ⚠️  Errore match {m.get('id')}: {e}")

            print(f"  ✅ {updated} partite aggiornate in matchcalendar")

    # Verifica finale
    print("\n--- Verifica Serie A (ultime giornate) ---")
    rows = await conn.fetch("""
        SELECT mc.matchday, COUNT(*) as tot,
               SUM(CASE WHEN mc.home_goals IS NOT NULL THEN 1 ELSE 0 END) as con_gol
        FROM matchcalendar mc
        JOIN league l ON mc.league_id = l.id
        WHERE l.name ILIKE '%Serie A%'
          AND mc.match_datetime >= '2025-07-01'
          AND mc.matchday IS NOT NULL
        GROUP BY mc.matchday
        ORDER BY mc.matchday DESC
        LIMIT 6
    """)
    print("Giornata | Tot | Con gol")
    for r in rows:
        print(f"   {r['matchday']:>2}     | {r['tot']:>3} | {r['con_gol']:>3}")

    await conn.close()
    print("\n✅ Done. Aggiorna la pagina nel browser.")


if __name__ == "__main__":
    asyncio.run(main())
