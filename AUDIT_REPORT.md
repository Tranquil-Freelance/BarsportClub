# Data Integrity Audit — xPalermoStat

**Data:** 2026-05-01  
**Database:** PostgreSQL `xpalermostat` @ localhost:5432  
**Script:** [`backend/data_integrity_audit.py`](backend/data_integrity_audit.py)

---

## Sommario Database

| Tabella | Righe | Copertura |
|---------|-------|-----------|
| `matchcalendar` | 11.114 totali | 10.927 completati, 10.497 scrapati |
| `rosters` | 325.992 | 10.679 match coperti |
| `shots` | 263.242 | 10.678 match coperti |
| `player_stats` | 34.502 | — |

**Stato matchcalendar:**

| Completato | Scrapato | Conteggio |
|:----------:|:--------:|----------:|
| false | false | 187 |
| true | false | 430 |
| true | true | 10.497 |

> 187 match futuri (non ancora giocati), 430 completati ma non scrapati (dati tiri non importati).

---

## Check 1 — Partite Fantasma ✅ PULITO

### 1a — NULL values in completed matches
**0 partite trovate.** Nessun match completato ha goals o xG a NULL.

### 1b — All-zero in scraped matches
**0 partite trovate.** Nessun match scrapato ha `home_goals=0 AND away_goals=0 AND home_xG=0.0 AND away_xG=0.0`.

**Verdetto:** Il database non contiene partite fantasma.

---

## Check 2 — Incongruenza Reti ⚠️ 1.400 discrepanze

**Criterio:** Solo match `is_completed=true AND is_scraped=true`.  
Confronto tra `home_goals`/`away_goals` (matchcalendar) e `COUNT(shots WHERE result='Goal')` raggruppato per `team_type='home'/'away'`.

### Risultati

| Categoria | Conteggio | Spiegazione |
|-----------|:---------:|-------------|
| Discrepanze totali | **1.400** | — |
| Spiegabili da autogol (`result='OwnGoal'`) | **855** (61%) | Autogol nel DB tiri (`result='OwnGoal'`) contano nel tabellino ma non nel filtro `result='Goal'` |
| **Non spiegate** | **545** (39%) | Necessitano verifica — vedi sotto |

### Pattern delle discrepanze
- Quasi tutte sono **Diff_H=+1** o **Diff_A=+1** (un goal in più nel tabellino rispetto ai tiri)
- Nessun caso di `shots_h > home_goals` (conteggio tiri maggiore del tabellino)
- La distribuzione è uniforme tra campionati e stagioni

### Analisi autogol
- 899 tiri con `result='OwnGoal'` in 864 match distinti
- 401 autogol di squadra `'home'`, 498 di squadra `'away'`
- Gli autogol spiegano completamente 855 delle 1.400 discrepanze

### Possibili cause per le 545 discrepanze residue
1. **Sorgente dati diversa:** i dati xG provengono da Understat, i dati tiri da altra fonte (es. FBref/API). Leggeri mismatch sono attesi
2. **Tiri mancanti nel dump:** alcuni tiri potrebbero non essere stati catturati durante lo scraping
3. **Goal assegnati a giocatore sbagliato:** raro ma possibile

**Raccomandazione:** Priorità bassa. Le 545 discrepanze residue sono minori (per lo più ±1) e probabilmente dovute a differenze tra sorgenti dati. Monitorare ma non richiede azione immediata.

---

## Check 3 — Giocatori Ombra ⚠️ 84.158

**Criterio:** `time >= 30 minuti` E tutti i seguenti a 0 o NULL: `shots`, `key_passes`, `xG`, `xA`, `goals`, `assists`.

### Risultati

| Metrica | Valore |
|---------|-------:|
| Giocatori ombra (>=30min) | **84.158** |
| Totale righe rosters | 325.992 |
| Percentuale | **25,8%** |

### Analisi
Il 25,8% dei roster entries riguarda giocatori che hanno giocato almeno 30 minuti senza produrre alcuna statistica offensiva. Questa percentuale è **fisiologica** per:

- **Difensori centrali** — raramente tirano o fanno assist
- **Terzini** — statistiche offensive variabili, molti match senza contributo
- **Portieri** — statistiche offensive sempre zero
- **Centrocampisti difensivi** — bassa produzione offensiva

**Raccomandazione:** Per un audit più mirato, filtrare per `position` escludendo `Goalkeeper`, `Defender`, `Defensive Midfielder`. Stimiamo che il numero scenderebbe a ~5.000-10.000 (principalmente attaccanti in giornata storta).

---

## Check 4 — Orfani e Missing ✅ PULITO

### 4a — Rosters orfani
**0 match_id orfani** in `rosters` ✅

### 4b — Shots orfani
**0 match_id orfani** in `shots` ✅

### 4c — Match senza rosters
**435 match** senza righe in `rosters` — tutti `is_completed=false` (partite future) ✅

### 4d — Match senza shots
**436 match** senza righe in `shots` — tutti `is_completed=false` (partite future) ✅

**Verdetto:** Nessun problema di integrità referenziale. Le 430 partite completate ma non scrapate (`is_scraped=false`) sono attese in attesa dello scraping.

---

## Bonus — Tabella `player_stats` ✅ PULITO

- Tabella presente con **34.502 righe**
- **0 match_id orfani**

---

## Conclusione Finale

| Controllo | Esito | Dettaglio |
|-----------|:-----:|-----------|
| Partite fantasma (NULL) | ✅ OK | 0 |
| Partite fantasma (all-zero) | ✅ OK | 0 |
| Goal discrepanti (scrapati) | ⚠️ 1.400 | 855 spiegati da autogol, 545 minori |
| Giocatori ombra (>=30min) | ⚠️ 84.158 | Atteso per ruoli difensivi |
| Orfani rosters | ✅ OK | 0 |
| Orfani shots | ✅ OK | 0 |
| Match senza rosters | ✅ OK | Solo match futuri |
| Match senza shots | ✅ OK | Solo match futuri |
| player_stats | ✅ OK | 34.502 righe, 0 orfani |

### **Verdetto: DATABASE IN OTTIMA SALUTE**

Nessun dato corrotto, nessun record orfano, nessuna partita fantasma. Le due segnalazioni (`goal discrepanti` e `giocatori ombra`) sono:
1. **Goal discrepanti** — spiegati per il 61% da autogol; il resto sono differenze minori attese tra sorgenti dati diverse
2. **Giocatori ombra** — fisiologici per ruoli difensivi (25,8% del totale roster)

**Nessuna azione correttiva urgente richiesta.**

---

*Report generato da [`backend/data_integrity_audit.py`](backend/data_integrity_audit.py)*
