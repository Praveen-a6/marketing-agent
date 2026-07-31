-- Migration 002: Add menu_state and projects table
BEGIN;

ALTER TABLE leads ADD COLUMN IF NOT EXISTS menu_state JSONB;

CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id),
    project_type VARCHAR(255),
    description TEXT,
    budget_estimate VARCHAR(100),
    timeline VARCHAR(100),
    requirements TEXT,
    status VARCHAR(100) DEFAULT 'new',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMIT;
