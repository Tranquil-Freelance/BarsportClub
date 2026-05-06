-- ==============================================================
-- MIGRATION 004: Settlement Columns — Phase 6
-- ==============================================================
-- Adds the target-variable and settlement-result columns needed
-- by the Settlement Engine to close out open bets and train the
-- Machine Learning AI on actual outcomes.
-- ==============================================================
-- Execute: psql -U <user> -d <db> -f 004_add_settlement_columns.sql
-- ==============================================================

BEGIN;

-- ── 1. bets.profit ──────────────────────────────────────────────
-- Stores the net profit/loss after settlement.
--   positive = win,  negative = loss,  0.0 = push / void
ALTER TABLE bets
    ADD COLUMN IF NOT EXISTS profit DOUBLE PRECISION;

COMMENT ON COLUMN bets.profit IS
    'Net profit (+) or loss (−) after settlement; 0.0 = push/void';

-- Update the status comment to reflect the new SETTLED state
-- (PostgreSQL does not support COMMENT ON COLUMN for enum-like strings,
--  so we just add the column cleanly).

-- ── 2. features_log.outcome_profit ──────────────────────────────
-- The target variable y = outcome_profit for ML training.
ALTER TABLE features_log
    ADD COLUMN IF NOT EXISTS outcome_profit DOUBLE PRECISION;

COMMENT ON COLUMN features_log.outcome_profit IS
    'Target variable y — actual profit/loss after match settlement';

-- Index for fast ML dataset extraction by matched match+market
CREATE INDEX IF NOT EXISTS idx_features_log_outcome_market
    ON features_log(outcome_profit, market_key, created_at);

COMMIT;
