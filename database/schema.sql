-- Marketing-Agent Initial Schema

CREATE TABLE students (
    id SERIAL PRIMARY KEY,

    full_name VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),

    college_name VARCHAR(255),
    degree VARCHAR(255),

    year_of_study VARCHAR(50),

    interested_course VARCHAR(255),

    lead_source VARCHAR(100),

    lead_status VARCHAR(100),

    lead_score INTEGER DEFAULT 0,

    notes TEXT,

    assigned_to VARCHAR(255),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE companies (
    id SERIAL PRIMARY KEY,

    company_name VARCHAR(255),

    website VARCHAR(255),

    industry VARCHAR(255),

    location VARCHAR(255),

    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE hr_contacts (
    id SERIAL PRIMARY KEY,

    company_id INTEGER REFERENCES companies(id),

    full_name VARCHAR(255),

    designation VARCHAR(255),

    email VARCHAR(255),

    phone VARCHAR(50),

    linkedin_url TEXT,

    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,

    campaign_name VARCHAR(255),

    channel VARCHAR(100),

    objective TEXT,

    status VARCHAR(100),

    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,

    title VARCHAR(255),

    description TEXT,

    assigned_to VARCHAR(255),

    status VARCHAR(100),

    priority VARCHAR(50),

    due_date TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE agent_memory (
    id SERIAL PRIMARY KEY,

    agent_name VARCHAR(255),

    memory_type VARCHAR(100),

    content TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
