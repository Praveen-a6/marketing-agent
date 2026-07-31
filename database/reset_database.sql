-- ============================================================
-- Marketing-Agent: FULL DATABASE WIPE + RESET
-- Run as: psql -U <user> -d marketing_agent -f reset_database.sql
-- WARNING: This deletes ALL data in leads, students, companies,
-- hr_contacts, campaigns, tasks, agent_memory. Irreversible.
-- ============================================================

BEGIN;

TRUNCATE TABLE
    agent_memory,
    tasks,
    hr_contacts,
    students,
    leads,
    companies,
    campaigns
RESTART IDENTITY CASCADE;

COMMIT;

-- Verify sequences reset to 1
SELECT 'leads' AS table_name, last_value FROM leads_id_seq
UNION ALL
SELECT 'students', last_value FROM students_id_seq
UNION ALL
SELECT 'companies', last_value FROM companies_id_seq
UNION ALL
SELECT 'hr_contacts', last_value FROM hr_contacts_id_seq
UNION ALL
SELECT 'campaigns', last_value FROM campaigns_id_seq
UNION ALL
SELECT 'tasks', last_value FROM tasks_id_seq
UNION ALL
SELECT 'agent_memory', last_value FROM agent_memory_id_seq;
