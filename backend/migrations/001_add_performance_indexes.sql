-- ==============================================================
-- MIGRATION 001: Performance indexes & Materialized View for IMR
-- ==============================================================
-- Esegui: psql -U <user> -d <db> -f 001_add_performance_indexes.sql
-- ==============================================================

BEGIN;

-- ─── INDICI PER ACCELERARE LE JOIN SU match_id ────────────────
CREATE INDEX IF NOT EXISTS idx_shots_match_id ON shots(match_id);
CREATE INDEX IF NOT EXISTS idx_rosters_match_id ON rosters(match_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_match_id ON player_stats(match_id);

-- ─── INDICI PER FILTRARE IL CALENDARIO VELOCEMENTE ────────────
CREATE INDEX IF NOT EXISTS idx_matchcalendar_is_completed ON matchcalendar(is_completed);
CREATE INDEX IF NOT EXISTS idx_matchcalendar_league_id ON matchcalendar(league_id);
CREATE INDEX IF NOT EXISTS idx_matchcalendar_is_scraped ON matchcalendar(is_scraped);

-- ─── INDICE COMPOSTO PER LA QUERY DEL MERITOMETRO ─────────────
-- Copre il WHERE league_id = ? AND is_scraped = True AND home_goals IS NOT NULL
CREATE INDEX IF NOT EXISTS idx_matchcalendar_meritometro 
    ON matchcalendar(league_id, is_scraped, home_goals)
    WHERE home_goals IS NOT NULL AND is_scraped = True;

-- ─── MATERIALIZED VIEW: IMR PRE-COMPUTATO PER TEAM ────────────
-- Sostituisce il ricalcolo CTE ad ogni richiesta HTTP.
-- I pesi sono allineati alla versione router in meritometro.py:
--   - ShotPoints: Penalty=2.0, altrimenti (xG² × 10) + (Goal/SavedShot bonus 1.0)
--   - BuildupPoints: xA × 1.2 + xGChain × 0.5
DROP MATERIALIZED VIEW IF EXISTS mv_team_imr CASCADE;

CREATE MATERIALIZED VIEW mv_team_imr AS
WITH UniqueShots AS (
    SELECT DISTINCT match_id, player, minute, team_type, situation, result, "xG", "X"
    FROM shots
),
ShotPoints AS (
    SELECT 
        match_id,
        team_type,
        SUM(CASE 
            WHEN situation = 'Penalty' THEN 2.0
            ELSE (POWER("xG"::numeric, 2) * 10.0) + 
                 (CASE WHEN result IN ('Goal', 'SavedShot') THEN 1.0 ELSE 0.0 END)
        END) AS s_pts
    FROM UniqueShots
    GROUP BY match_id, team_type
),
UniquePlayerStats AS (
    SELECT DISTINCT match_id, player_name, team_type, "xA", "xGChain"
    FROM player_stats
),
BuildupPoints AS (
    SELECT 
        match_id,
        team_type,
        (SUM(COALESCE("xA"::numeric, 0)) * 1.2) + 
        (SUM(COALESCE("xGChain"::numeric, 0)) * 0.5) AS b_pts
    FROM UniquePlayerStats
    GROUP BY match_id, team_type
)
SELECT 
    COALESCE(sp.match_id, bp.match_id) AS match_id,
    COALESCE(sp.team_type, bp.team_type) AS team_type,
    COALESCE(sp.s_pts, 0.0) + COALESCE(bp.b_pts, 0.0) AS imr_total
FROM ShotPoints sp
FULL OUTER JOIN BuildupPoints bp 
    ON sp.match_id = bp.match_id AND sp.team_type = bp.team_type;

-- Indice univoco per permettere REFRESH MATERIALIZED VIEW CONCURRENTLY
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_team_imr_pk 
    ON mv_team_imr(match_id, team_type);

COMMIT;
