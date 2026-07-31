-- Marketing-Agent CRM Schema V2 (updated for Instagram menu flow)
-- Run once to create fresh tables.

BEGIN;

-- CAMPAIGNS (unchanged)
CREATE TABLE IF NOT EXISTS campaigns (
    id SERIAL PRIMARY KEY,
    campaign_name VARCHAR(255) NOT NULL,
    channel VARCHAR(100),
    objective TEXT,
    status VARCHAR(100) DEFAULT 'active',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LEADS – added menu_state (JSONB) and other fields
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    college_name VARCHAR(255),
    degree VARCHAR(255),
    year_of_study VARCHAR(50),
    interested_course VARCHAR(255),
    career_goal TEXT,
    source_platform VARCHAR(100),
    source_post VARCHAR(255),
    social_username VARCHAR(255),
    campaign_id INTEGER REFERENCES campaigns(id),
    lead_status VARCHAR(100) DEFAULT 'new',
    lead_score INTEGER DEFAULT 0,
    qualification_status VARCHAR(100),
    qualification_reason TEXT,
    assigned_to VARCHAR(255),
    notes TEXT,
    -- Instagram‑specific
    igsid VARCHAR(255) UNIQUE,
    comment_id VARCHAR(255),
    last_comment_id VARCHAR(255),
    last_message_id VARCHAR(255),
    qualification_step INTEGER DEFAULT 0,
    conversation_summary TEXT,
    last_interaction_at TIMESTAMP,
    -- NEW: menu state (JSONB)
    menu_state JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- STUDENTS (unchanged)
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id),
    full_name VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    college_name VARCHAR(255),
    degree VARCHAR(255),
    enrolled_course VARCHAR(255),
    enrollment_date DATE,
    status VARCHAR(100) DEFAULT 'active',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- COMPANIES (unchanged)
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    website VARCHAR(255),
    industry VARCHAR(255),
    location VARCHAR(255),
    company_size VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HR CONTACTS (unchanged)
CREATE TABLE IF NOT EXISTS hr_contacts (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    full_name VARCHAR(255),
    designation VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    linkedin_url TEXT,
    relationship_status VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TASKS (unchanged)
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    assigned_to VARCHAR(255),
    status VARCHAR(100) DEFAULT 'open',
    priority VARCHAR(50) DEFAULT 'medium',
    due_date TIMESTAMP,
    related_lead_id INTEGER REFERENCES leads(id),
    related_company_id INTEGER REFERENCES companies(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AGENT MEMORY (unchanged)
CREATE TABLE IF NOT EXISTS agent_memory (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(255) NOT NULL,
    memory_key VARCHAR(255) NOT NULL,
    memory_value TEXT,
    memory_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- NEW: PROJECTS table for service inquiries
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

-- WEBHOOK EVENTS (idempotency)
CREATE TABLE IF NOT EXISTS webhook_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) NOT NULL UNIQUE,
    platform VARCHAR(50) NOT NULL,
    payload JSONB,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_leads_igsid ON leads(igsid);
CREATE INDEX IF NOT EXISTS idx_leads_social_username ON leads(social_username);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(lead_status);
CREATE INDEX IF NOT EXISTS idx_projects_lead_id ON projects(lead_id);
CREATE INDEX IF NOT EXISTS idx_webhook_events_event_id ON webhook_events(event_id);

COMMIT;
