# Architectural Decision Log

## ADR-015
**Date:** 2026-07
**Decision:** Implement Google Forms Webhook as an active fallback.
**Reason:** Allows immediate resume collection and lead capture without waiting for the Meta App Review process.
**Status:** Accepted

## ADR-016
**Date:** 2026-07
**Decision:** Consolidate Telegram Notifications into Unified Hot Lead Alerts.
**Reason:** Avoids sending separate chat notifications for metadata and PDF files. Pings are triggered only for hot leads (`score >= 50`) or manual intervention requests.
**Status:** Accepted

## ADR-017
**Date:** 2026-07
**Decision:** Two-way Google Sheets Status Sync.
**Reason:** Enables non-technical staff to update lead statuses directly in Google Sheets. `resume_extractor.py` pushes to Sheets, and `sheets_pull_status.py` pulls from Sheets back to the DB.
**Status:** Accepted

## ADR-018
**Date:** 2026-07
**Decision:** Command-driven Content Generation and Multi-Platform Scraping.
**Reason:** Future features (Content Studio and Scraping for Students, HRs, and Projects) will be invoked on demand via Telegram commands and saved to dedicated Google Sheets tabs.
**Status:** Planned
