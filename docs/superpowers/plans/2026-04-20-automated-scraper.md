# Automated Understat Scraper Scheduler — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatizzare lo scraping di understat.com — il sistema rileva le partite finite, aspetta 10 min, scarica i dati con retry ogni 10 min per 30 min, gira da solo su VPS Linux.

**Architecture:** `prova2.py` espone una funzione `scrape_single_match()` richiamabile dal nuovo `scheduler.py`. Lo scheduler usa APScheduler con un job fisso di polling ogni 15 min e job dinamici per ogni match. Un service systemd garantisce l'esecuzione automatica su VPS.

**Tech Stack:** Python 3.12, DrissionPage, APScheduler 3.x, SQLAlchemy, PostgreSQL, systemd

---

## File Structure

| File | Azione | Responsabilità |
|------|--------|---------------|
| `backend/prova2.py` | **Creare** (codice fornito dall'utente + modifiche) | Scraper headless + funzione `scrape_single_match()` |
| `backend/scheduler.py` | **Creare** | Polling understat, scheduling dinamico retry |
| `deploy/barsport.service` | **Creare** | Systemd unit file per VPS |
| `deploy/setup_vps.sh` | **Creare** | Script bash setup una-tantum su VPS |

---

## Task 1: Creare prova2.py con supporto headless e funzione riusabile

**Files:**
- Create: `backend/prova2.py`

- [ ] **Step 1: Crea il file `backend/prova2.py`** con il codice dello scraper originale modificato per headless e con la funzione `scrape_single_match` estratta:

```python
import time
import random
import logging
import json
from DrissionPage import ChromiumPage, ChromiumOptions
from sqlalchemy import create_engine, text

# ==========================================
# CONFIGURAZIONE - STAGIONE 2025
# ==========================================
DB_URI = "postgresql://postgres:password@localhost:5432/xpalermostat"
engine = create_engine(DB_URI)

TARGET_LEAGUES = ['Serie_A', 'EPL', 'La_liga', 'Bundesliga', 'Ligue_1']
SEASON = '2025'

JITTER_MIN = 10.0
JITTER_MAX = 20.0
HIBERNATION_PERIOD = 1800


def safe_float(val):
    try:
        return float(val)
    except Exception:
        return 0.0


def safe_int(val):
    try:
        return int(val)
    except Exception:
        return 0


def get_ppda(p):
    if not p:
        return 0.0
    att = safe_float(p.get('att'))
    df = safe_float(p.get('def'))
    return att / df if df > 0 else 0.0


def build_matchdays_dict(dates_list):
    sorted_matches = sorted(dates_list, key=lambda x: x.get('datetime', ''))
    team_games = {}
    match_rounds = {}
    for m in sorted_matches:
        if not m.get('datetime'):
            continue
        h_id = str(m['h']['id'])
        a_id = str(m['a']['id'])
        team_games[h_id] = team_games.get(h_id, 0) + 1
        team_games[a_id] = team_games.get(a_id, 0) + 1
        round_num = max(team_games[h_id], team_games[a_id])
        match_rounds[int(m['id'])] = round_num
    return match_rounds


def make_page() -> ChromiumPage:
    """Crea un'istanza ChromiumPage headless per VPS Linux."""
    co = ChromiumOptions()
    co.headless(True)
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--disable-gpu')
    co.set_user_agent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    )
    return ChromiumPage(co)


def scrape_single_match(page: ChromiumPage, match_id: int) -> bool:
    """
    Scrapa shots e rosters di una singola partita.
    Restituisce True se i dati erano disponibili e sono stati salvati.
    Restituisce False se window.shotsData era null (dati non ancora pubblicati).
    """
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT is_scraped FROM matchcalendar WHERE id = :id"),
            {"id": match_id}
        ).fetchone()
        if row and row[0]:
            logging.info(f"Match {match_id}: già scrapato, skip.")
            return True

    time.sleep(random.uniform(JITTER_MIN, JITTER_MAX))
    page.get(f"https://understat.com/match/{match_id}")

    if "429" in page.html or "too many requests" in page.html.lower():
        logging.warning(f"Match {match_id}: BAN rilevato. Attendo 30 min.")
        time.sleep(HIBERNATION_PERIOD)
        page.get(f"https://understat.com/match/{match_id}")

    page.scroll.down(500)
    time.sleep(2)

    raw_match_json = page.run_js("""
        if(typeof window.shotsData !== 'undefined' && typeof window.rostersData !== 'undefined'){
            return JSON.stringify({s: window.shotsData, r: window.rostersData});
        }
        return null;
    """)

    if not raw_match_json:
        logging.info(f"Match {match_id}: dati non ancora pubblicati su understat.")
        return False

    m_json = json.loads(raw_match_json)

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM shots WHERE match_id = :id"), {"id": match_id})
        conn.execute(text("DELETE FROM rosters WHERE match_id = :id"), {"id": match_id})

        for side in ['h', 'a']:
            for s in m_json['s'].get(side, []):
                conn.execute(text("""
                    INSERT INTO shots (match_id, player_id, player, minute, "xG", "X", "Y",
                                      result, team_type, situation, "shotType", "lastAction")
                    VALUES (:m_id, :p_id, :p, :min, :xg, :x, :y, :res, :side, :sit, :st, :la)
                    ON CONFLICT (match_id, player, minute) DO NOTHING
                """), {
                    "m_id": match_id,
                    "p_id": safe_int(s.get('player_id')),
                    "p": s.get('player'),
                    "min": safe_int(s.get('minute')),
                    "xg": safe_float(s.get('xG')),
                    "x": safe_float(s.get('X')),
                    "y": safe_float(s.get('Y')),
                    "res": s.get('result'),
                    "side": 'home' if side == 'h' else 'away',
                    "sit": s.get('situation'),
                    "st": s.get('shotType'),
                    "la": s.get('lastAction'),
                })

        for side in ['h', 'a']:
            for r in m_json['r'].get(side, {}).values():
                conn.execute(text("""
                    INSERT INTO rosters (match_id, player_id, player, position, "time",
                                        goals, assists, shots, key_passes, "xG", "xA")
                    VALUES (:m_id, :p_id, :p, :pos, :t, :g, :as, :sh, :kp, :xg, :xa)
                """), {
                    "m_id": match_id,
                    "p_id": safe_int(r.get('player_id')),
                    "p": r.get('player'),
                    "pos": r.get('position'),
                    "t": safe_int(r.get('time')),
                    "g": safe_int(r.get('goals')),
                    "as": safe_int(r.get('assists')),
                    "sh": safe_int(r.get('shots')),
                    "kp": safe_int(r.get('key_passes')),
                    "xg": safe_float(r.get('xG')),
                    "xa": safe_float(r.get('xA')),
                })

        conn.execute(
            text("UPDATE matchcalendar SET is_scraped = TRUE WHERE id = :id"),
            {"id": match_id}
        )

    logging.info(f"✅ Match {match_id}: shots e rosters salvati.")
    return True


def sync_2025_with_advanced_metrics():
    """Bulk sync stagionale — da lanciare manualmente per recuperare partite storiche."""
    logging.info("🚀 AVVIO BULK SYNC STAGIONALE")
    page = make_page()

    for league in TARGET_LEAGUES:
        time.sleep(random.uniform(JITTER_MIN, JITTER_MAX))
        league_url = f"https://understat.com/league/{league}/{SEASON}"

        try:
            page.get(league_url)

            if "429" in page.html or "too many requests" in page.html.lower():
                logging.warning("🚨 BAN RILEVATO. IBERNAZIONE 30 MINUTI.")
                time.sleep(HIBERNATION_PERIOD)
                page.get(league_url)

            page.scroll.down(1000)
            time.sleep(2)

            raw_league_json = page.run_js("""
                if(typeof window.teamsData !== 'undefined' && typeof window.datesData !== 'undefined'){
                    return JSON.stringify({t: window.teamsData, d: window.datesData});
                }
                return null;
            """)

            if not raw_league_json:
                logging.warning(f"⚠️ Impossibile trovare teamsData per {league}. Salto.")
                continue

            league_data = json.loads(raw_league_json)
            teams_dict = league_data['t']
            dates_list = league_data['d']

            match_rounds = build_matchdays_dict(dates_list)
            played_matches = [m for m in dates_list if m.get('isResult') is True]
            matches_to_process = []

            with engine.connect() as conn:
                for m in played_matches:
                    m_id = int(m['id'])
                    row = conn.execute(
                        text("SELECT is_scraped FROM matchcalendar WHERE id = :id"),
                        {"id": m_id}
                    ).fetchone()
                    if not row or not row[0]:
                        matches_to_process.append(m)

            logging.info(f"📊 {league}: {len(matches_to_process)} match mancanti.")

            if not matches_to_process:
                continue

            with engine.begin() as conn:
                for m in matches_to_process:
                    m_id = int(m['id'])
                    m_date = m['datetime']
                    h_id = str(m['h']['id'])
                    a_id = str(m['a']['id'])
                    computed_round = match_rounds.get(m_id, 0)
                    h_stats = next(
                        (h for h in teams_dict[h_id]['history'] if h['date'] == m_date), {}
                    )
                    a_stats = next(
                        (h for h in teams_dict[a_id]['history'] if h['date'] == m_date), {}
                    )
                    conn.execute(text("""
                        UPDATE matchcalendar SET
                            home_ppda = :h_ppda, away_ppda = :a_ppda,
                            home_deep = :h_deep, away_deep = :a_deep,
                            home_xpts = :h_xpts, away_xpts = :a_xpts,
                            matchday = :md, is_completed = TRUE
                        WHERE id = :id
                    """), {
                        "id": m_id,
                        "md": computed_round,
                        "h_ppda": get_ppda(h_stats.get('ppda')),
                        "a_ppda": get_ppda(a_stats.get('ppda')),
                        "h_deep": safe_int(h_stats.get('deep')),
                        "a_deep": safe_int(a_stats.get('deep')),
                        "h_xpts": safe_float(h_stats.get('xpts')),
                        "a_xpts": safe_float(a_stats.get('xpts')),
                    })

            for m in matches_to_process:
                m_id = int(m['id'])
                scrape_single_match(page, m_id)

        except Exception as e:
            logging.error(f"❌ Errore critico su {league}: {e}")

    page.quit()
    logging.info("✅ Bulk sync completato.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    sync_2025_with_advanced_metrics()
```

- [ ] **Step 2: Verifica che il file esista**

```bash
ls backend/prova2.py
```
Atteso: il file compare nell'elenco.

- [ ] **Step 3: Commit**

```bash
git add backend/prova2.py
git commit -m "feat: add prova2.py with headless Chrome support and scrape_single_match()"
```

---

## Task 2: Creare scheduler.py

**Files:**
- Create: `backend/scheduler.py`

- [ ] **Step 1: Crea il file `backend/scheduler.py`**

```python
import json
import logging
import logging.handlers
import os
import random
import time
from datetime import datetime, timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import text

from prova2 import (
    DB_URI,
    HIBERNATION_PERIOD,
    JITTER_MIN,
    JITTER_MAX,
    SEASON,
    TARGET_LEAGUES,
    engine,
    make_page,
    scrape_single_match,
)

MATCH_DURATION_MINUTES = 105   # 90 min partita + 15 min recupero medio
SCRAPE_DELAY_MINUTES = 10      # attesa dopo fine prevista prima del 1° tentativo
MAX_ATTEMPTS = 3
RETRY_INTERVAL_MINUTES = 10
LOG_PATH = "/var/log/barsport/scheduler.log"


def setup_logging():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        LOG_PATH, maxBytes=10 * 1024 * 1024, backupCount=3
    )
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=[handler, logging.StreamHandler()],
    )


scheduler = BlockingScheduler(timezone="UTC")


def poll_understat():
    """
    Job fisso ogni 15 minuti.
    Controlla tutte le leghe su understat, trova partite con isResult=True
    non ancora scrapat e le schedula.
    """
    logging.info("=== POLL understat avviato ===")
    page = make_page()
    try:
        for league in TARGET_LEAGUES:
            time.sleep(random.uniform(JITTER_MIN, JITTER_MAX))
            url = f"https://understat.com/league/{league}/{SEASON}"
            page.get(url)

            if "429" in page.html or "too many requests" in page.html.lower():
                logging.warning(f"{league}: BAN rilevato, attendo 30 min.")
                time.sleep(HIBERNATION_PERIOD)
                page.get(url)

            page.scroll.down(1000)
            time.sleep(2)

            raw = page.run_js("""
                if(typeof window.datesData !== 'undefined'){
                    return JSON.stringify(window.datesData);
                }
                return null;
            """)

            if not raw:
                logging.warning(f"{league}: datesData non trovato, skip.")
                continue

            dates_list = json.loads(raw)
            played = [m for m in dates_list if m.get('isResult') is True]

            with engine.connect() as conn:
                for m in played:
                    m_id = int(m['id'])
                    row = conn.execute(
                        text("SELECT is_scraped FROM matchcalendar WHERE id = :id"),
                        {"id": m_id},
                    ).fetchone()

                    if row and row[0]:
                        continue  # già scrapato

                    kickoff_str = m.get('datetime', '')
                    if not kickoff_str:
                        continue

                    kickoff = datetime.strptime(kickoff_str, '%Y-%m-%d %H:%M:%S')
                    expected_end = kickoff + timedelta(minutes=MATCH_DURATION_MINUTES)
                    first_scrape_time = expected_end + timedelta(minutes=SCRAPE_DELAY_MINUTES)

                    now = datetime.utcnow()
                    job_id = f"scrape_{m_id}_1"

                    if scheduler.get_job(job_id):
                        continue  # già schedulato

                    if now >= first_scrape_time:
                        # La partita è finita da un po' ma non è mai stata scrapata
                        logging.info(f"Match {m_id}: in ritardo, scrape immediato.")
                        _schedule_scrape(m_id, 1, run_date=datetime.utcnow() + timedelta(seconds=5))
                    else:
                        logging.info(f"Match {m_id}: scrape schedulato per {first_scrape_time} UTC")
                        _schedule_scrape(m_id, 1, run_date=first_scrape_time)

    except Exception as e:
        logging.error(f"Errore nel poll: {e}")
    finally:
        page.quit()
    logging.info("=== POLL understat completato ===")


def _schedule_scrape(match_id: int, attempt: int, run_date: datetime):
    job_id = f"scrape_{match_id}_{attempt}"
    scheduler.add_job(
        scrape_match_with_retry,
        trigger=DateTrigger(run_date=run_date),
        args=[match_id, attempt],
        id=job_id,
        replace_existing=True,
    )


def scrape_match_with_retry(match_id: int, attempt: int):
    """
    Job dinamico. Tenta lo scrape di un singolo match.
    Se i dati non sono ancora disponibili, schedula un retry (max 3 tentativi).
    """
    if attempt > MAX_ATTEMPTS:
        logging.warning(
            f"Match {match_id}: dati non disponibili dopo {MAX_ATTEMPTS} tentativi. Skip."
        )
        return

    logging.info(f"Match {match_id}: tentativo {attempt}/{MAX_ATTEMPTS}")
    page = make_page()
    try:
        success = scrape_single_match(page, match_id)
    except Exception as e:
        logging.error(f"Match {match_id}: eccezione durante scrape: {e}")
        success = False
    finally:
        page.quit()

    if not success:
        retry_time = datetime.utcnow() + timedelta(minutes=RETRY_INTERVAL_MINUTES)
        logging.info(
            f"Match {match_id}: dati non pronti, retry {attempt + 1} alle {retry_time} UTC"
        )
        _schedule_scrape(match_id, attempt + 1, run_date=retry_time)


if __name__ == "__main__":
    setup_logging()
    logging.info("🚀 Barsport Scheduler avviato")

    scheduler.add_job(
        poll_understat,
        trigger=IntervalTrigger(minutes=15),
        id="poll_understat",
        next_run_time=datetime.utcnow(),  # esegui subito al primo avvio
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Scheduler fermato.")
```

- [ ] **Step 2: Verifica che il file esista**

```bash
ls backend/scheduler.py
```
Atteso: il file compare.

- [ ] **Step 3: Test fumo — importazione e sintassi**

```bash
cd backend && python -c "import scheduler; print('OK')"
```
Atteso output: `OK` (nessun ImportError o SyntaxError).  
Se esce `ModuleNotFoundError: apscheduler` → esegui `pip install apscheduler` e riprova.

- [ ] **Step 4: Commit**

```bash
git add backend/scheduler.py
git commit -m "feat: add scheduler.py with APScheduler polling and retry logic"
```

---

## Task 3: Creare il file systemd service

**Files:**
- Create: `deploy/barsport.service`

- [ ] **Step 1: Crea la directory e il file**

```bash
mkdir -p deploy
```

Crea `deploy/barsport.service` con questo contenuto (**sostituisci `/home/ubuntu` con il tuo vero home path sulla VPS**):

```ini
[Unit]
Description=Barsport Scout Engine - Automated Scraper Scheduler
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

- [ ] **Step 2: Commit**

```bash
git add deploy/barsport.service
git commit -m "feat: add systemd service file for VPS deployment"
```

---

## Task 4: Creare lo script di setup VPS

**Files:**
- Create: `deploy/setup_vps.sh`

- [ ] **Step 1: Crea `deploy/setup_vps.sh`**

```bash
#!/usr/bin/env bash
# Setup una-tantum per la VPS Linux.
# Esegui con: sudo bash deploy/setup_vps.sh /home/ubuntu/claude-of-control /home/ubuntu/venv312

set -e

PROJECT_DIR="${1:-/home/ubuntu/claude-of-control}"
VENV_DIR="${2:-/home/ubuntu/venv312}"
SERVICE_SRC="$PROJECT_DIR/deploy/barsport.service"
SERVICE_DST="/etc/systemd/system/barsport.service"
LOG_DIR="/var/log/barsport"

echo "=== [1/5] Installazione Chromium ==="
apt-get update -qq
apt-get install -y chromium-browser

echo "=== [2/5] Installazione dipendenze Python ==="
"$VENV_DIR/bin/pip" install --quiet apscheduler drissionpage sqlalchemy psycopg2-binary

echo "=== [3/5] Creazione directory log ==="
mkdir -p "$LOG_DIR"
chown ubuntu:ubuntu "$LOG_DIR"

echo "=== [4/5] Installazione systemd service ==="
# Aggiorna i path nel service file con quelli reali
sed "s|/home/ubuntu/claude-of-control|$PROJECT_DIR|g; s|/home/ubuntu/venv312|$VENV_DIR|g" \
    "$SERVICE_SRC" > "$SERVICE_DST"

systemctl daemon-reload
systemctl enable barsport
systemctl start barsport

echo "=== [5/5] Setup completato ==="
echo "Stato servizio:"
systemctl status barsport --no-pager

echo ""
echo "Per seguire i log in tempo reale:"
echo "  tail -f $LOG_DIR/scheduler.log"
```

- [ ] **Step 2: Rendi eseguibile**

```bash
chmod +x deploy/setup_vps.sh
```

- [ ] **Step 3: Commit**

```bash
git add deploy/setup_vps.sh
git commit -m "feat: add VPS one-time setup script"
```

---

## Task 5: Deploy sulla VPS

> Questi step si eseguono **sulla VPS**, non in locale.

- [ ] **Step 1: Copia il progetto sulla VPS** (da eseguire in locale)

```bash
# Se usi git:
git push origin main

# Sulla VPS:
git clone <tuo-repo-url> /home/ubuntu/claude-of-control
# oppure se già clonato:
cd /home/ubuntu/claude-of-control && git pull
```

- [ ] **Step 2: Esegui lo script di setup sulla VPS**

```bash
sudo bash /home/ubuntu/claude-of-control/deploy/setup_vps.sh \
  /home/ubuntu/claude-of-control \
  /home/ubuntu/venv312
```

Atteso output finale: `Active: active (running)` nello stato del servizio.

- [ ] **Step 3: Verifica che il polling parta correttamente**

```bash
tail -f /var/log/barsport/scheduler.log
```

Atteso nelle prime righe:
```
INFO: 🚀 Barsport Scheduler avviato
INFO: === POLL understat avviato ===
INFO: === POLL understat completato ===
```

- [ ] **Step 4: Verifica riavvio automatico**

```bash
# Simula crash del processo
kill $(systemctl show -p MainPID barsport | cut -d= -f2)

# Attendi 65 secondi (RestartSec=60 + margine)
sleep 65
systemctl status barsport --no-pager
```

Atteso: `Active: active (running)` — il servizio si è riavviato da solo.

---

## Comandi utili post-deploy

```bash
# Stato servizio
systemctl status barsport

# Ferma il servizio
systemctl stop barsport

# Riavvia dopo modifiche al codice
systemctl restart barsport

# Log in tempo reale
tail -f /var/log/barsport/scheduler.log

# Lancia bulk sync manuale (recupera storico)
cd /home/ubuntu/claude-of-control/backend
/home/ubuntu/venv312/bin/python prova2.py
```
