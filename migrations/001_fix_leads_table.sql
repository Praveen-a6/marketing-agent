-- ============================================================
-- Migration 001: Fix leads table for Instagram integration
-- Adds missing columns your webhook code needs, plus
-- uniqueness constraints to prevent duplicate leads.
-- Run: psql -d marketing_agent -f migrations/001_fix_leads_table.sql
-- ============================================================

BEGIN;

-- 1. Add columns the webhook/reply code actually needs
ALTER TABLE leads ADD COLUMN IF NOT EXISTS igsid VARCHAR(255);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS comment_id VARCHAR(255);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_comment_id VARCHAR(255);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_message_id VARCHAR(255);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS qualification_step INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS conversation_summary TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_interaction_at TIMESTAMP;

-- 2. Prevent duplicate leads for the same Instagram user (IGSID is the
--    stable identifier Meta gives us for DMs; username can change).
--    Partial unique index: only enforce when igsid is present.
CREATE UNIQUE INDEX IF NOT EXISTS uq_leads_igsid
ON leads (igsid)
WHERE igsid IS NOT NULL;

-- 3. Prevent duplicate leads for same username+platform when igsid is
--    not yet known (comment-only leads before DM contact).
CREATE UNIQUE INDEX IF NOT EXISTS uq_leads_social_platform
ON leads (social_username, source_platform)
WHERE igsid IS NULL AND social_username IS NOT NULL;

-- 4. Idempotency: never process the same Instagram comment/message twice.
CREATE UNIQUE INDEX IF NOT EXISTS uq_leads_last_comment_id
ON leads (last_comment_id)
WHERE last_comment_id IS NOT NULL;

-- 5. Dedicated event log table for webhook idempotency
--    (separate from leads so retries never touch lead data twice).
CREATE TABLE IF NOT EXISTS webhook_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) NOT NULL UNIQUE,
    platform VARCHAR(50) NOT NULL,
    payload JSONB,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_webhook_events_event_id ON webhook_events(event_id);

-- 6. Index for igsid lookups (hot path on every DM webhook call)
CREATE INDEX IF NOT EXISTS idx_leads_igsid ON leads(igsid);

COMMIT;

-- Verify
\d leads
