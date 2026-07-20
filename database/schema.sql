-- Marketing-Agent CRM Schema V1
-- Source of Truth: PostgreSQL

-- ==========================================
-- CAMPAIGNS
-- ==========================================

CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,

    campaign_name VARCHAR(255) NOT NULL,

    channel VARCHAR(100),

    objective TEXT,

    status VARCHAR(100) DEFAULT 'active',

    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- LEADS
-- ==========================================

CREATE TABLE leads (
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

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- STUDENTS
-- ==========================================

CREATE TABLE students (
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

-- ==========================================
-- COMPANIES
-- ==========================================

CREATE TABLE companies (
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

-- ==========================================
-- HR CONTACTS
-- ==========================================

CREATE TABLE hr_contacts (
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

-- ==========================================
-- TASKS
-- ==========================================

CREATE TABLE tasks (
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

-- ==========================================
-- AGENT MEMORY
-- ==========================================

CREATE TABLE agent_memory (
    id SERIAL PRIMARY KEY,

    agent_name VARCHAR(255) NOT NULL,

    memory_key VARCHAR(255) NOT NULL,

    memory_value TEXT,

    memory_type VARCHAR(100),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- INDEXES
-- ==========================================

CREATE INDEX idx_leads_phone
ON leads(phone);

CREATE INDEX idx_leads_email
ON leads(email);

CREATE INDEX idx_leads_status
ON leads(lead_status);

CREATE INDEX idx_students_email
ON students(email);

CREATE INDEX idx_hr_contacts_email
ON hr_contacts(email);

CREATE INDEX idx_tasks_status
ON tasks(status);

CREATE INDEX idx_agent_memory_agent
ON agent_memory(agent_name);
