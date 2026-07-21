# Marketing-Agent Architecture

## Purpose

Marketing-Agent is an AI-powered marketing operations platform built on top of OpenClaw.

The platform assists Career Solutions with:

* Student lead generation
* Student lead management
* HR relationship management
* Company relationship management
* Marketing content generation
* Placement operations support
* Training operations support
* Research and reporting

The platform is human-supervised and not autonomous.

---

# Core Principle

OpenClaw is NOT the source of truth.

The source of truth is:

1. Repository
2. PostgreSQL Database

OpenClaw acts as an execution and reasoning layer.

The system must remain operational even if OpenClaw is replaced in the future.

---

# High Level Architecture

User Channels

* Telegram
* Instagram
* WhatsApp

↓

Workflow Layer

* Lead Capture
* Lead Qualification
* Content Generation
* Reporting
* Research

↓

Agent Layer

* Token Monitor
* Lead Hunter
* Lead Qualification Engine
* Lead Enricher
* Content Studio
* Campaign Planner
* Telegram Control
* Instagram Assistant
* WhatsApp Assistant
* Analytics Agent

↓

Knowledge Layer

knowledge/

* company_profile.md
* services.md
* courses.md
* placement_process.md
* lead_qualification.md
* SOPs
* marketing_playbooks

↓

Data Layer

PostgreSQL

* students
* companies
* hr_contacts
* campaigns
* tasks
* agent_memory

↓

Infrastructure Layer

* OpenClaw
* DeepSeek V4 Flash
* Gateway
* WSL2 Ubuntu
* Future Docker Deployment

---

# Repository Structure

marketing-agent/

docs/
architecture.md
roadmap.md
decisions.md

knowledge/
company_profile.md
services.md
courses.md
placement_process.md
lead_qualification.md

database/

workflows/

skills/

prompts/

configs/

logs/

backups/

drafts/

---

# Security Model

Allowed

* Read repository files
* Read workflows
* Read knowledge files
* Search CRM
* Create CRM records
* Update CRM records
* Generate reports
* Generate drafts

Approval Required

* Git commits
* Record deletion
* Bulk updates
* Schema changes
* Infrastructure changes
* Campaign launch
* Message sending
* Money spending

---

# Telegram Architecture

Primary Operations Interface

Users:

* Admin
* Placement Officer
* Marketing Executive

Functions:

* Approval requests
* Reports
* Lead notifications
* Task management
* Token alerts

Telegram becomes the operational control panel.

---

# Instagram Architecture

Inbound Lead Collection

Monitor:

* Comments
* Mentions
* DMs

Classify:

* General Engagement
* Interest
* Lead Intent

Store qualified leads inside CRM.

Notify staff through Telegram.

---

# WhatsApp Architecture

Phase 1

Inbound only

Workflow:

Message
→ Draft generated
→ Human approval
→ Send

No autonomous outbound messaging.

---

# Knowledge First Strategy

Before invoking LLMs:

1. Search repository knowledge
2. Search CRM
3. Search workflow definitions

Only use DeepSeek when information is not available.

Goal:

Minimize token consumption.

---

# Token Management

Budgets:

* Monthly
* Daily
* Per Task

System Responsibilities:

* Track usage
* Estimate costs
* Alert overruns
* Prefer retrieval
* Prefer tools
* Minimize generation

---

# Migration Strategy

Target Environment

Ubuntu VPS
Docker
PostgreSQL
OpenClaw

Deployment Objective

git clone

docker compose up

System operational with minimal manual configuration.

