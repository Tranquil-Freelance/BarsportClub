# Design: Automated Understat Scraper Scheduler

**Date:** 2026-04-20  
**Status:** Approved

---

## Overview

Sistema automatizzato che monitora understat.com per rilevare partite appena concluse e scarica i dati (shots, rosters, metriche avanzate) al momento giusto — senza intervento manuale, su VPS Linux.

---

## Componenti

| File | Ruolo |
|------|-------|
| `prova2.py` | Scraper esistente (DrissionPage + Chromium headless), modificato con `co.headless(True)` |
| `scheduler.py` | Orchestratore: polling understat, scheduling dinamico dei job di scraping |
| `/etc/systemd/system/barsport.service` | Avvio automatico al boot della VPS, restart su crash |

---

## Flusso Logico

### Polling (ogni 15 minuti)

1. Per ogni lega in `TARGET_LEAGUES` (`Serie_A`, `EPL`, `La_liga`, `Bundesliga`, `Ligue_1`):
   - Apre `https://understat.com/league/{league}/{season}` con DrissionPage headless
   - Estrae `window.datesData` via JS
   - Per ogni partita con `isResult == True`:
     - Controlla nel DB se `is_scraped == False`
     - Calcola `orario_fine_previsto = datetime_kickoff + 105 minuti`
     - Se `now >= orario_fine_previsto + 10 min` → lancia scrape immediato
     - Se `now < orario_fine_previsto + 10 min` → schedula job a `orario_fine_previsto + 10 min`

### Scraping con Retry

```
scrape_match(match_id, attempt=1..3)
  T+10 min → attempt 1: estrai shotsData + rostersData
  T+20 min → attempt 2: se dati null (non ancora pubblicati)
  T+30 min → attempt 3: ultimo tentativo
  Dopo 3 fallimenti → log WARNING, skip
```

Un tentativo è considerato riuscito se `window.shotsData` e `window.rostersData` sono entrambi non-null nella pagina del match.

---

## Stima Orario Fine Partita

`orario_fine = kickoff_datetime + 105 min` (90 min + 15 min recupero medio).

Non serve API esterna — understat fornisce già `datetime` in `datesData`. Questo copre il 95% dei casi; i supplementari (solo coppe) sono rari e il retry da 10 min gestisce il ritardo extra.

---

## Headless Chrome su VPS

Setup una-tantum:
```bash
apt install -y chromium-browser
pip install apscheduler drissionpage sqlalchemy psycopg2-binary
```

Modifica a `prova2.py`:
```python
co = ChromiumOptions()
co.headless(True)                          # unica aggiunta
co.set_argument('--no-sandbox')            # necessario su Linux VPS
co.set_argument('--disable-dev-shm-usage') # evita crash su VPS con poca RAM
co.set_user_agent('Mozilla/5.0 ...')
page = ChromiumPage(co)
```

---

## APScheduler

- **Job fisso:** `poll_understat()` con `IntervalTrigger(minutes=15)`
- **Job dinamico:** `scrape_match(match_id, attempt)` con `DateTrigger(run_date=...)` creato al volo dal poller
- **JobStore:** in-memory (nessuna persistenza necessaria — il DB è la fonte di verità con `is_scraped`)

---

## systemd Service

`/etc/systemd/system/barsport.service`:
```ini
[Unit]
Description=Barsport Scout Engine - Automated Scraper
After=network.target postgresql.service

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/claude-of-control/backend
ExecStart=/home/ubuntu/venv312/bin/python scheduler.py
Restart=always
RestartSec=60
StandardOutput=append:/var/log/barsport/scheduler.log
StandardError=append:/var/log/barsport/scheduler.log

[Install]
WantedBy=multi-user.target
```

Comandi attivazione:
```bash
systemctl daemon-reload
systemctl enable barsport
systemctl start barsport
```

---

## Logging

- File: `/var/log/barsport/scheduler.log`
- Rotazione automatica via `logging.handlers.RotatingFileHandler` (max 10MB, 3 backup)
- Monitor live: `tail -f /var/log/barsport/scheduler.log`

---

## Cosa NON cambia

- Schema DB invariato (`matchcalendar.is_scraped` già esiste)
- Tutta la logica di inserimento shots/rosters/metriche resta in `prova2.py`
- Anti-ban (jitter 10-20s, hibernation 30min su 429) resta invariato

---

## Out of Scope

- Gestione supplementari/rigori (retry da 30 min copre casi limite)
- Notifiche email/Telegram su scrape completato
- Dashboard di monitoraggio
