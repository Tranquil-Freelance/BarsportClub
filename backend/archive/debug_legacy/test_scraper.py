import asyncio
import aiohttp
from understat import Understat

async def main():
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        print("⏳ Collegamento a Understat in corso...\n")
        
        try:
            # Scarichiamo i risultati della Serie A (stagione 2024/2025)
            results = await understat.get_league_results("serie_a", 2024) 
            
            print(f"✅ Download completato. Trovate {len(results)} partite in totale.\n")
            
            # Cerchiamo la prima partita del Como
            trovata = False
            for match in results:
                home_team = match['h']['title']
                away_team = match['a']['title']
                
                if home_team == 'Como' or away_team == 'Como':
                    print("🎯 ECCO I DATI PURI DAL SERVER UNDERSTAT:")
                    print(f"⚽ Partita: {home_team} vs {away_team}")
                    print(f"🥅 Risultato Reale: {match['goals']['h']} - {match['goals']['a']}")
                    print(f"📊 Expected Goals (xG): {match['xG']['h']} - {match['xG']['a']}")
                    print(f"🆔 ID Partita Understat: {match['id']}")
                    print("-" * 40)
                    trovata = True
                    break  # Ci fermiamo alla prima partita trovata
            
            if not trovata:
                print("⚠️ Nessuna partita del Como trovata in questo elenco.")
                
        except Exception as e:
            print(f"❌ Errore durante lo scaricamento: {e}")

# Eseguiamo il codice asincrono
asyncio.run(main())

# L'incantesimo anti-Houdini: blocchiamo la finestra per farti leggere il risultato
input("\nPremi INVIO per chiudere questa finestra...")