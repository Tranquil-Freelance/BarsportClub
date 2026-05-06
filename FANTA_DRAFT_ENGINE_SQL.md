# Fanta Draft Engine - SQL Queries & Logic

## 1. Weighted xG/xA (Proiezione base)

Aggregazione per giocatore e stagione:

```sql
SELECT
    player_id,
    player_name,
    season,
    SUM(goals) AS goals,
    SUM(assists) AS assists,
    SUM(xg) AS xg,
    SUM(xa) AS xa,
    SUM(time) AS minutes
FROM master_europe_players
WHERE season IN (2025, 2024, 2023)
GROUP BY player_id, player_name, season
ORDER BY player_id, season DESC;
```

Calcolo pesato (0.5, 0.3, 0.2) con riproporzionamento se mancano anni:

```sql
WITH season_stats AS (
    SELECT
        player_id,
        season,
        SUM(xg) AS xg,
        SUM(xa) AS xa
    FROM master_europe_players
    WHERE season IN (2025, 2024, 2023)
    GROUP BY player_id, season
),
ranked_seasons AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY season DESC) AS rn
    FROM season_stats
),
weighted AS (
    SELECT
        player_id,
        CASE WHEN COUNT(*) = 3 THEN 0.5 * MAX(CASE WHEN rn = 1 THEN xg ELSE 0 END) +
                                  0.3 * MAX(CASE WHEN rn = 2 THEN xg ELSE 0 END) +
                                  0.2 * MAX(CASE WHEN rn = 3 THEN xg ELSE 0 END)
             WHEN COUNT(*) = 2 THEN 0.65 * MAX(CASE WHEN rn = 1 THEN xg ELSE 0 END) +
                                  0.35 * MAX(CASE WHEN rn = 2 THEN xg ELSE 0 END)
             ELSE xg
        END AS weighted_xg,
        CASE WHEN COUNT(*) = 3 THEN 0.5 * MAX(CASE WHEN rn = 1 THEN xa ELSE 0 END) +
                                  0.3 * MAX(CASE WHEN rn = 2 THEN xa ELSE 0 END) +
                                  0.2 * MAX(CASE WHEN rn = 3 THEN xa ELSE 0 END)
             WHEN COUNT(*) = 2 THEN 0.65 * MAX(CASE WHEN rn = 1 THEN xa ELSE 0 END) +
                                  0.35 * MAX(CASE WHEN rn = 2 THEN xa ELSE 0 END)
             ELSE xa
        END AS weighted_xa
    FROM ranked_seasons
    GROUP BY player_id
)
SELECT * FROM weighted;
```

## 2. Regressione alla Media (Breakout/Bust)

Delta tra xG e Gol reali nell'ultima stagione:

```sql
WITH latest_season AS (
    SELECT
        player_id,
        season,
        SUM(goals) AS goals,
        SUM(xg) AS xg
    FROM master_europe_players
    WHERE season = (SELECT MAX(season) FROM master_europe_players)
    GROUP BY player_id, season
)
SELECT
    player_id,
    goals,
    xg,
    (xg - goals) AS delta,
    CASE WHEN xg > 0 THEN (xg - goals) / xg ELSE 0 END AS delta_ratio,
    -- Moltiplicatore breakout: se delta positivo (sottoperformato) aumento proiezione
    1.0 + (CASE WHEN xg > 0 THEN (xg - goals) / xg * 0.5 ELSE 0 END) AS breakout_multiplier
FROM latest_season;
```

## 3. Team Attack Index (TAI)

Classificazione squadre in Top/Medie/Basse basata sulla media xG per partita nella stagione:

```sql
WITH team_season_xg AS (
    SELECT
        team_name,
        season,
        COUNT(DISTINCT match_id) AS matches,
        SUM(xg) AS total_xg,
        SUM(xg) / COUNT(DISTINCT match_id) AS xg_per_match
    FROM master_europe_players
    WHERE season = 2025
    GROUP BY team_name, season
),
percentiles AS (
    SELECT
        *,
        NTILE(3) OVER (ORDER BY xg_per_match DESC) AS tier
    FROM team_season_xg
    WHERE matches >= 5
)
SELECT
    team_name,
    season,
    xg_per_match,
    CASE tier
        WHEN 1 THEN 1.2
        WHEN 2 THEN 1.0
        WHEN 3 THEN 0.8
    END AS tai_multiplier
FROM percentiles;
```

## 4. Value Score & Max Bid

Fantasy Points Expected (goal = 5 punti, assist = 3 punti):

```sql
WITH weighted_stats AS (
    -- Inserire qui la query weighted xG/xA
),
value_calc AS (
    SELECT
        player_id,
        weighted_xg * 5.0 + weighted_xa * 3.0 AS fantasy_points_expected,
        RANK() OVER (ORDER BY weighted_xg * 5.0 + weighted_xa * 3.0 DESC) AS rank_value
    FROM weighted_stats
    WHERE weighted_xg + weighted_xa > 0
)
SELECT
    player_id,
    fantasy_points_expected,
    -- Max Bid %: proporzionale al valore relativo, massimo 20% del budget
    (fantasy_points_expected / MAX(fantasy_points_expected) OVER ()) * 20 AS max_bid_percent
FROM value_calc;
```

## 5. Etichette Automatiche

```sql
WITH player_season_latest AS (
    SELECT
        player_id,
        player_name,
        season,
        SUM(goals) AS goals,
        SUM(xg) AS xg,
        SUM(shots) AS shots,
        SUM(time) AS minutes
    FROM master_europe_players
    WHERE season = 2025
    GROUP BY player_id, player_name, season
)
SELECT
    player_id,
    player_name,
    CASE WHEN xg > goals AND xg > 0.2 THEN 'Undervalued Finisher' END AS label1,
    CASE WHEN goals > xg * 1.5 AND xg > 0.1 THEN 'Overperformer - Risky' END AS label2,
    CASE WHEN shots > 3 AND xg / shots < 0.1 THEN 'Volume Striker' END AS label3,
    -- Safe Pick richiede confronto con stagioni precedenti (implementazione più complessa)
FROM player_season_latest;
```

## 6. Dashboard Widgets Query

### Best Value Picks (sottovalutati)
```sql
SELECT player_id, player_name, weighted_xg, weighted_xa, max_bid_percent
FROM (
    -- Combinazione delle query sopra
) AS calc
WHERE max_bid_percent > 10
ORDER BY max_bid_percent DESC
LIMIT 10;
```

### Breakout Candidates (giovani/nuovi con trend positivo)
```sql
SELECT player_id, player_name, breakout_multiplier, (xg - goals) AS delta
FROM (
    -- Query regressione alla media
) AS breakout
WHERE breakout_multiplier > 1.1
ORDER BY breakout_multiplier DESC
LIMIT 10;
```

### Toxic Assets / Avoid (overperformer rischiosi)
```sql
SELECT player_id, player_name, goals, xg, goals - xg AS overperformance
FROM (
    -- Query ultima stagione
) AS toxic
WHERE goals > xg * 1.5
ORDER BY overperformance DESC
LIMIT 10;
```

### Safe Picks (rendimento costante YoY)
```sql
WITH season_variance AS (
    SELECT
        player_id,
        STDDEV(xg) OVER (PARTITION BY player_id) AS xg_stddev,
        AVG(xg) OVER (PARTITION BY player_id) AS xg_avg
    FROM (
        SELECT player_id, season, SUM(xg) AS xg
        FROM master_europe_players
        WHERE season IN (2025,2024,2023)
        GROUP BY player_id, season
    ) AS s
)
SELECT player_id, xg_avg, xg_stddev
FROM season_variance
WHERE xg_stddev / NULLIF(xg_avg,0) < 0.2  -- bassa variabilità
LIMIT 10;
```

---

Queste query possono essere eseguite direttamente nel database PostgreSQL e sono integrate nel backend Python (`backend/app/api/fanta_routes.py`) con le funzioni helper.

Per ulteriori ottimizzazioni, si consiglia di creare viste materializzate per le metriche aggregate, dato il volume di dati (260k righe).