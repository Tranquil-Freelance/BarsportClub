-- ==============================================================
-- MIGRATION 002: Bets Table — Capital Allocation (Phase 1)
-- ==============================================================
-- Fractional Kelly Criterion staking layer.
-- Tracks stake, bankroll_before, bankroll_after per bet.
-- ==============================================================
-- Execute: psql -U <user> -d <db> -f 002_add_bets_table.sql
-- ==============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS bets (
    id              BIGSERIAL       PRIMARY KEY,
    match_id        BIGINT          REFERENCES matchcalendar(id) ON DELETE SET NULL,
    market_key      VARCHAR(100)    NOT NULL,
    decimal_odds    DOUBLE PRECISION NOT NULL,
    p_model         DOUBLE PRECISION NOT NULL,
    ev              DOUBLE PRECISION,

    -- === CAPITAL ALLOCATION COLUMNS ===
    stake           DOUBLE PRECISION,   -- fraction of bankroll wagered
    bankroll_before DOUBLE PRECISION,   -- bankroll just before placement
    bankroll_after  DOUBLE PRECISION,   -- bankroll just after placement

    status          VARCHAR(20)     NOT NULL DEFAULT 'pending',
    placed_at       TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    settled_at      TIMESTAMPTZ
);

-- Index on match_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_bets_match_id ON bets(match_id);

-- Index on placement timestamp for chronological queries
CREATE INDEX IF NOT EXISTS idx_bets_placed_at ON bets(placed_at);

-- Index on status for filtering active / settled bets
CREATE INDEX IF NOT EXISTS idx_bets_status ON bets(status);

COMMIT;
