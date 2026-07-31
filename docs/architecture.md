# Marketing-Agent Architecture

## Purpose
Marketing-Agent is an AI-powered marketing operations platform. The platform assists Career Solutions with student lead generation, qualification, placement operations, and content generation.

---

## Core Principle
OpenClaw is NOT the source of truth. The permanent memory and source of truth is the **PostgreSQL Database**.

---

## High Level Architecture

### User & Intake Channels
* **Instagram:** Official Graph API via Webhook (`skills/instagram_webhook.py`)
* **Web Intake:** Google Forms Webhook Fallback (`/form-webhook`)
* **WhatsApp:** Official Meta Cloud API (Prepared)
* **Telegram:** Operations Control Center & Staff Dashboard

### Data & Synchronization Layer
* **PostgreSQL:** Primary relational store (`leads`, `projects`, `webhook_events`, `students`).
* **Google Sheets Sync:**
  * **Outbound (`sheets_sync.py`):** Automatically refreshes the spreadsheet when a resume is processed.
  * **Inbound (`sheets_pull_status.py`):** Pulls manual status edits made by humans in Sheets back into PostgreSQL.

### Alerting & Control Rules (Telegram)
* **Unified Hot Lead Alert:** When a hot lead (`score >= 50`) uploads a resume, Telegram receives **ONE** unified alert containing student metadata + attached PDF.
* **Quiet Intake:** Low-scoring leads update PostgreSQL and Sheets without sending Telegram notifications.
* **Intervention Alerts:** Triggered instantly on complex DM/Comment questions.
* **Automated Daily Digest:** Scheduled daily summary pushed to Admin chats.

### Planned Telegram Operational Commands (Pending Phase 7 & 8)
1. **`/generate_content <topic>`:** Generates Reels, captions, and ad copy directly from Telegram.
2. **`/scrape_leads <domain/platform>`:** Triggers web and social scraping for Students, HRs, and Project Managers. Appends output to dedicated secondary Google Sheets tabs (`Students`, `HR_Contacts`, `Projects`).
