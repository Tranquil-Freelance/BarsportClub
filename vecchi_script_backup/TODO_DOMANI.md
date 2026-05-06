# TODO per domani (2026-03-15)

## Priorità alta

1. **FIX PYTHONPATH** - Risolvere il conflitto di importazione backend.app vs app.
   - Confermato che il server parte correttamente quando si imposta `PYTHONPATH=%PYTHONPATH%;%CD%\backend`.
   - Inserire questa modifica nello script di avvio permanente (es. `.env`, `run.sh`, o configurazione del servizio systemd).
   - Verificare che tutti gli import `backend.app.xxx` siano coerenti con la struttura delle cartelle (nessuna modifica necessaria).

2. **Test di integrazione** - Dopo il fix, eseguire un test completo delle API:
   - `/api/latest-match`
   - `/api/matches`
   - `/api/match/{id}/shots`
   - `/api/standings`
   - Verificare che lo scheduler parta senza errori (log "Background scheduler started successfully").

3. **Frontend connectivity** - Assicurarsi che il frontend (localhost:3000) riesca a comunicare con il backend (localhost:8000).
   - Controllare CORS (attualmente `allow_origins=["*"]`).
   - Testare una pagina che richiede dati live (es. `/palermo`).

## Priorità media

4. **Refactoring codice** - Valutare se riorganizzare gli import per evitare ambiguità.
   - Considerare di spostare `backend/app` in `app` (rinominare) e aggiornare gli import di conseguenza.
   - Oppure aggiungere `backend` come namespace package e mantenere `backend.app` come percorso assoluto.

5. **Documentazione** - Aggiornare il README con le istruzioni per l'avvio in ambiente di sviluppo e produzione.
   - Includere il comando con PYTHONPATH.
   - Aggiungere note sul database (PostgreSQL) e sulle variabili d'ambiente.

6. **Monitoring** - Configurare log più dettagliati per lo scheduler (APScheduler) e per le richieste HTTP.

## Note tecniche

- Oggi abbiamo verificato che il server parte e stampa `Application startup complete` quando si usa:
  ```
  set PYTHONPATH=%PYTHONPATH%;%CD%\backend && venv312\Scripts\python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
  ```
- Gli import `backend.app.tasks.updater` e `backend.app.scraper.understat_parser` sono corretti e non vanno modificati.
- Il frontend è attivo sulla porta 3000 (Terminal 2).
- Il server amministrativo (scraper) è stato testato tramite Terminal 1.

## Chiusura sessione

- Server spento dopo il test.
- Terminali attivi: Terminal 1 (scraper check), Terminal 2 (frontend dev).