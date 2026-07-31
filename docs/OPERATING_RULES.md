# Operating Rules & Guardrails (OpenClaw Specific)

These are absolute rules enforced at the agent/system level.

---

## 1. Source of Truth
- Repository and PostgreSQL are the **source of truth**.
- OpenClaw is an **ephemeral execution layer**.

---

## 2. Tier 1: Allowed Actions (No Approval Required)
- Read files in `/home/praveen/marketing-agent`.
- Search and Update CRM records (INSERT/UPDATE leads, score adjustments).
- Execute standard Instagram DM Qualification flows.
- Answer standard FAQs (Location, basic course list) automatically.
- Send internal Telegram alerts.

---

## 3. Tier 2: Draft & Approve (Explicit Approval Required)
- Sending custom replies to complex user questions (Fees, Certifications).
- WhatsApp outbound follow-ups.
- Bulk messaging or campaign outreach.
- Agent generates draft -> Sends to Telegram -> Human replies `APPROVE <id>`.

---

## 4. Tier 3: Strict Lock (Admin Approval Only)
- Publishing public content (Instagram posts, Reels, Ads).
- Destructive database operations (DELETE, DROP).
- Modifying critical files (`openclaw.json`, `schema.sql`, `.env`).
- Running shell commands outside `~/marketing-agent`.

---

## 5. Strictly Forbidden
- Bypassing CAPTCHA, MFA, or bot detection.
- Scraping private/authenticated data.
- Using personal social accounts.
