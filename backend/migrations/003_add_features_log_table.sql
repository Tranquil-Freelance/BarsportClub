-- ==============================================================
-- MIGRATION 003: Features Log Table — ML Training Data (Phase 5)
-- ==============================================================
-- Records every evaluated bet's feature vector for future ML
-- model training and backtesting analysis.
-- ==============================================================
-- Execute: psql -U <user> -d <db> -f 003_add_features_log_table.sql
-- ==============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS features_log (
    id                  BIGSERIAL       PRIMARY KEY,
    match_id            BIGINT          REFERENCES matchcalendar(id) ON DELETE SET NULL,
    market_key          VARCHAR(100)    NOT NULL,
    lambda_home         DOUBLE PRECISION,
    lambda_away         DOUBLE PRECISION,
    p_model             DOUBLE PRECISION,
    p_book              DOUBLE PRECISION,
    ev_base             DOUBLE PRECISION,
    team_strength_home  DOUBLE PRECISION,
    team_strength_away  DOUBLE PRECISION,
    stability_home      DOUBLE PRECISION,
    stability_away      DOUBLE PRECISION,
    odds                DOUBLE PRECISION,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- Index on match_id for fast lookups by fixture
CREATE INDEX IF NOT EXISTS idx_features_log_match_id ON features_log(match_id);

-- Index on created_at for chronological range queries
CREATE INDEX IF NOT EXISTS idx_features_log_created_at ON features_log(created_at);

-- Composite index for ML dataset extraction (filter by market + time range)
CREATE INDEX IF NOT EXISTS idx_features_log_market_created
    ON features_log(market_key, created_at);

COMMIT;
